"""No message a person can read names an internal requirement ID (#175).

A person who runs the command has no TR-6, FR-2 or G-23 to look up. Comments and
docstrings may name them. A string that the code prints or raises, and the `--help` text,
may not.
"""

import ast
import re
from pathlib import Path

from click.testing import CliRunner

from layerforge.cli import cli

SRC = Path(__file__).resolve().parent.parent / "src" / "layerforge"
REQUIREMENT_ID = re.compile(r"\b(?:N?FR|TR|G)-\d+\b")


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return the ids of the string nodes that are docstrings."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                found.add(id(first.value))
    return found


def test_no_string_in_src_names_a_requirement_id() -> None:
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and REQUIREMENT_ID.search(node.value)
            ):
                hits.append(f"{path.relative_to(SRC)}:{node.lineno}: {node.value!r}")
    assert hits == []


def test_help_text_names_no_requirement_id() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert REQUIREMENT_ID.findall(result.output) == []
