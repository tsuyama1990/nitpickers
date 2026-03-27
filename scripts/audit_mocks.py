import ast
import sys
from pathlib import Path


class MockHunterVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[str] = []
        self.allowed_mocks = {"respx", "aioresponses", "pyfakefs"}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "unittest.mock":
            for alias in node.names:
                if alias.name in ("patch", "AsyncMock", "MagicMock", "Mock"):
                    self.violations.append(
                        f"{self.filename}:{node.lineno} - Prohibited import: from {node.module} import {alias.name}"
                    )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.startswith("unittest.mock"):
                self.violations.append(
                    f"{self.filename}:{node.lineno} - Prohibited import: import {alias.name}"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in ("patch", "AsyncMock", "MagicMock", "Mock"):
                # if it's patch, check if it's patching an internal module
                if node.func.id == "patch" and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        if first_arg.value.startswith("src."):
                            self.violations.append(
                                f"{self.filename}:{node.lineno} - Prohibited usage: {node.func.id}('{first_arg.value}')"
                            )
                        elif any(allowed in first_arg.value for allowed in self.allowed_mocks):
                            pass # allowed
                else:
                    self.violations.append(
                        f"{self.filename}:{node.lineno} - Prohibited usage: {node.func.id}()"
                    )
        elif isinstance(node.func, ast.Attribute) and node.func.attr in ("patch", "AsyncMock", "MagicMock", "Mock"):
            self.violations.append(
                f"{self.filename}:{node.lineno} - Prohibited usage: .{node.func.attr}()"
            )
        self.generic_visit(node)


def audit_mocks(target_dir: str) -> bool:
    path = Path(target_dir)
    if not path.exists():
        return False

    all_violations = []

    for py_file in path.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        visitor = MockHunterVisitor(str(py_file))
        visitor.visit(tree)
        all_violations.extend(visitor.violations)

    if all_violations:
        sys.stderr.write("\n=== INTEGRITY VIOLATION DETECTED ===\n")
        sys.stderr.write("The following mock usage violates the Zero-Mock Integration testing policy:\n\n")
        for _v in all_violations:
            sys.stderr.write(f"  - {_v}\n")
        sys.stderr.write("\nPlease refactor these tests to use real instances or approved boundary stubs.\n")
        return False

    sys.stdout.write("\n✓ Audit passed. No internal mock usage detected.\n")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit tests for prohibited mock usage.")
    parser.add_argument(
        "target_dir",
        nargs="?",
        default="tests/nitpick/integration/",
        help="Directory to audit"
    )
    args = parser.parse_args()

    success = audit_mocks(args.target_dir)
    sys.exit(0 if success else 1)
