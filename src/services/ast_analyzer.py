import ast
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.config import settings


class ASTAnalyzer:
    """Analyzes Python files to find structural duplicates and high complexity functions."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.paths.src

    def _hash_ast(self, node: ast.AST) -> str:
        """
        Creates a hash of the AST structure, ignoring names and specific values
        to find structurally identical functions even if variables were renamed.
        """
        class StructuralVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.structure: list[str] = []

            def generic_visit(self, node: ast.AST) -> None:
                self.structure.append(type(node).__name__)
                super().generic_visit(node)

        visitor = StructuralVisitor()
        visitor.visit(node)
        structure_str = ",".join(visitor.structure)
        return hashlib.sha256(structure_str.encode("utf-8")).hexdigest()

    def _calculate_mccabe_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculates McCabe cyclomatic complexity of a function.
        Complexity is 1 + number of decision points.
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
                    ast.With,
                    ast.AsyncFor,
                    ast.AsyncWith,
                    ast.Assert,
                    ast.IfExp,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                    ast.Match,
                ),
            ):
                complexity += 1
        return complexity

    def _get_python_files(self) -> list[Path]:
        """Returns all python files in the base directory."""
        if not self.base_dir.exists():
            return []
        return [p for p in self.base_dir.rglob("*.py") if p.is_file() and "__pycache__" not in str(p)]

    def _parse_file(self, file_path: Path) -> ast.Module | None:
        """Parses a python file into an AST module."""
        try:
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
