import ast
import hashlib
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path
from typing import Any

from src.config import settings


class ASTAnalyzer:
    """Analyzes Python files to find structural duplicates and high complexity functions."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.paths.src

    def _hash_ast(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """
        Creates a hash of the AST structure, including function signature types and logic structure.
        """
        class StructuralVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.structure: list[str] = []

            def visit_arg(self, node: ast.arg) -> None:
                # Include type annotation if present, otherwise just 'arg'
                if node.annotation:
                    anno_str = ast.unparse(node.annotation)
                    self.structure.append(f"arg:{anno_str}")
                else:
                    self.structure.append("arg:Any")
                self.generic_visit(node)

            def generic_visit(self, node: ast.AST) -> None:
                self.structure.append(type(node).__name__)

                # Include specific operator types to differentiate logic (e.g. + vs -)
                if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp)):
                    self.structure.append(type(node.op).__name__)
                elif isinstance(node, ast.Compare):
                    for op in node.ops:
                        self.structure.append(type(op).__name__)

                super().generic_visit(node)

        visitor = StructuralVisitor()

        # Include return type in hash if present
        if node.returns:
            visitor.structure.append(f"returns:{ast.unparse(node.returns)}")
        else:
            visitor.structure.append("returns:Any")

        docstring = ast.get_docstring(node)
        if docstring:
            visitor.structure.append(f"doc:{docstring}")

        visitor.visit(node)
        structure_str = ",".join(visitor.structure)
        return hashlib.sha256(structure_str.encode("utf-8")).hexdigest()

    def _calculate_mccabe_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """
        Calculates McCabe cyclomatic complexity of a function.
        Complexity is 1 + number of actual control flow decision points.
        Excludes comprehensions to prevent false positives.
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.And,
                    ast.Or,
                    ast.ExceptHandler,
                    ast.AsyncFor,
                    ast.Assert,
                    ast.IfExp,
                    ast.Match,
                ),
            ):
                complexity += 1
        return complexity

    def _get_python_files(self) -> Generator[Path, None, None]:
        """Generator that streams python files to prevent OOM on large codebases."""
        if not self.base_dir.exists():
            return

        import os
        max_files = settings.ast_analyzer.max_files
        max_depth = settings.ast_analyzer.max_depth
        count = 0

        # We manually walk to respect depth limits
        stack = [(self.base_dir, 0)]
        while stack and count < max_files:
            current_dir, depth = stack.pop()

            if depth > max_depth:
                continue

            try:
                # Add explicit permission check
                if not os.access(current_dir, os.R_OK | os.X_OK):
                    continue

                for item in current_dir.iterdir():
                    if item.is_dir() and item.name not in (".git", "__pycache__", ".venv", "venv", "env"):
                        if os.access(item, os.R_OK | os.X_OK):
                            stack.append((item, depth + 1))
                    elif item.is_file() and item.suffix == ".py" and os.access(item, os.R_OK):
                        count += 1
                        yield item
                        if count >= max_files:
                            break
            except (PermissionError, OSError):
                continue

    def _parse_file(self, file_path: Path) -> ast.Module | None:
        """Parses a python file into an AST module with size limits."""
        try:
            # Check file size before reading to prevent DoS via large files
            if file_path.stat().st_size > settings.ast_analyzer.max_file_size_bytes:
                return None
            content = file_path.read_text(encoding="utf-8")
            return ast.parse(content, filename=str(file_path))
        except (SyntaxError, Exception):
            return None

    def find_duplicates(self) -> list[list[dict[str, Any]]]:
        """
        Finds identical or structurally highly similar functions across the codebase.
        Returns a list of duplicate groups. Each group is a list of dicts with 'file' and 'function'.
        """
        hash_to_funcs: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for file_path in self._get_python_files():
            module = self._parse_file(file_path)
            if not module:
                continue

            for node in module.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Ignore short functions to avoid noise (e.g., getters/setters or pass)
                    if len(node.body) <= 2:
                        continue

                    # Remove docstrings for comparison
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        node.body = node.body[1:]

                    if not node.body:
                        continue

                    func_hash = self._hash_ast(node)
                    hash_to_funcs[func_hash].append(
                        {
                            "file": str(file_path),
                            "function": node.name,
                        }
                    )

        # Filter out hashes that only appear once
        return [funcs for funcs in hash_to_funcs.values() if len(funcs) > 1]

    def find_complex_functions(self, max_complexity: int = 10) -> list[dict[str, Any]]:
        """
        Finds functions that exceed the specified maximum McCabe complexity.
        Returns a list of dicts with 'file', 'function', and 'complexity'.
        """
        complex_funcs = []

        for file_path in self._get_python_files():
            module = self._parse_file(file_path)
            if not module:
                continue

            for node in module.body:
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_mccabe_complexity(node)
                    if complexity > max_complexity:
                        complex_funcs.append(
                            {
                                "file": str(file_path),
                                "function": node.name,
                                "complexity": complexity,
                            }
                        )

        return complex_funcs
