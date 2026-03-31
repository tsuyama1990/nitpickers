import ast
import os
from collections import defaultdict
from pathlib import Path


class StructuralHashVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.struct: list[str] = []

    def generic_visit(self, node: ast.AST) -> None:
        self.struct.append(node.__class__.__name__)
        # Keep track of specific function calls or attribute accesses to differentiate structure
        if isinstance(node, ast.Name):
            self.struct.append(node.id)
        elif isinstance(node, ast.Attribute):
            self.struct.append(node.attr)
        super().generic_visit(node)


def hash_function_logic(func_node: ast.FunctionDef) -> tuple[str, ...]:
    visitor = StructuralHashVisitor()
    for statement in func_node.body:
        visitor.visit(statement)
    return tuple(visitor.struct)


def find_duplicate_tests(directory: str) -> dict[tuple[str, ...], list[str]]:
    test_hashes: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                path_obj = Path(root) / file
                with path_obj.open(encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=str(path_obj))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                                body_hash = hash_function_logic(node)
                                # Ignore trivial tests like pass or simple assert
                                if len(body_hash) > 10:
                                    test_hashes[body_hash].append(f"{path_obj}::{node.name}")
                    except SyntaxError:
                        pass
    return test_hashes


if __name__ == "__main__":
    hashes = find_duplicate_tests("tests")
    print("=== DUPLICATE TESTS FOUND (AST Structural Match) ===")  # noqa: T201
    count = 0
    for _h, tests in hashes.items():
        if len(tests) > 1:
            count += 1
            print(f"Identical logic group {count} ({len(tests)} tests):")  # noqa: T201
            for t in tests:
                print(f"  {t}")  # noqa: T201
            print()  # noqa: T201
    if count == 0:
        print("No significant duplicates found.")  # noqa: T201
