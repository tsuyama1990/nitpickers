import textwrap
from pathlib import Path

from src.services.ast_analyzer import ASTAnalyzer


def test_ast_analyzer_find_duplicates(tmp_path: Path) -> None:
    """Test that the AST Analyzer correctly identifies structurally identical functions."""
    file_a = tmp_path / "file_a.py"
    file_b = tmp_path / "file_b.py"

    code_a = textwrap.dedent(
        '''
        def add_two_numbers(a, b):
            """Adds two numbers."""
            result = a + b
            return result
    '''
    )

    code_b = textwrap.dedent(
        '''
        def sum_values(x, y):
            """Returns the sum of x and y."""
            total = x + y
            return total
    '''
    )

    code_c = textwrap.dedent(
        """
        def multiply(x, y):
            return x * y
    """
    )

    file_a.write_text(code_a)
    file_b.write_text(code_b + code_c)

    analyzer = ASTAnalyzer(base_dir=tmp_path)
    duplicates = analyzer.find_duplicates()

    # Should find one duplicate group containing add_two_numbers and sum_values
    assert len(duplicates) == 1
    dup_group = duplicates[0]
    assert len(dup_group) == 2

    funcs = [item["function"] for item in dup_group]
    assert "add_two_numbers" in funcs
    assert "sum_values" in funcs
    assert "multiply" not in funcs


def test_ast_analyzer_mccabe_complexity(tmp_path: Path) -> None:
    """Test that the AST Analyzer correctly flags high McCabe complexity."""
    file_a = tmp_path / "complex.py"

    # 10 ifs/elifs > complexity 10
    code_complex = textwrap.dedent(
        """
        def highly_complex_function(x):
            if x == 1:
                return 1
            elif x == 2:
                return 2
            elif x == 3:
                return 3
            elif x == 4:
                return 4
            elif x == 5:
                return 5
            elif x == 6:
                return 6
            elif x == 7:
                return 7
            elif x == 8:
                return 8
            elif x == 9:
                return 9
            elif x == 10:
                return 10
            elif x == 11:
                return 11
            return 0
    """
    )

    file_a.write_text(code_complex)

    analyzer = ASTAnalyzer(base_dir=tmp_path)
    complex_funcs = analyzer.find_complex_functions(max_complexity=10)

    assert len(complex_funcs) == 1
    assert complex_funcs[0]["function"] == "highly_complex_function"
    assert complex_funcs[0]["complexity"] > 10


def test_ast_analyzer_no_duplicates(tmp_path: Path) -> None:
    """Test AST analyzer with completely distinct functions."""
    file_a = tmp_path / "distinct.py"

    code = textwrap.dedent(
        """
        def first():
            print("First")

        def second(x):
            return x * 2
    """
    )

    file_a.write_text(code)

    analyzer = ASTAnalyzer(base_dir=tmp_path)
    assert len(analyzer.find_duplicates()) == 0


def test_ast_analyzer_parse_error(tmp_path: Path) -> None:
    """Test AST analyzer gracefully handles files with syntax errors."""
    file_a = tmp_path / "invalid.py"

    # Missing colon in function definition
    code = textwrap.dedent(
        """
        def broken_function()
            print("No colon")
    """
    )

    file_a.write_text(code)

    analyzer = ASTAnalyzer(base_dir=tmp_path)

    # Test _parse_file directly
    assert analyzer._parse_file(file_a) is None

    # Test that these methods gracefully handle the unparseable file
    assert len(analyzer.find_duplicates()) == 0
    assert len(analyzer.find_complex_functions()) == 0
