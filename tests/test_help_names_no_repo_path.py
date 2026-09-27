"""No message a person can read names a path of this repository (#178).

A person who installed with `pip` or `uv tool install` has no `docs/` folder. A string that
the code prints or raises, and the `--help` text, may not send them to one. Comments and
docstrings may name paths.
"""

import ast
import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from layerforge.cli import cli

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "layerforge"
REPO_PATH = re.compile(r"(?<![\w/.])(?:docs|specs|src|tests|scripts)/|\.(?:md|allium)\b")


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


def test_no_string_in_src_names_a_repo_path() -> None:
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and REPO_PATH.search(node.value)
            ):
                hits.append(f"{path.relative_to(SRC)}:{node.lineno}: {node.value!r}")
    assert hits == []


def test_help_text_names_no_repo_path() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert REPO_PATH.findall(result.output) == []


@pytest.mark.parametrize("width", [60, 80, 120])
def test_help_gives_the_published_page_whole(width: int) -> None:
    from layerforge.cli import _MARK_OPTIONS_URL

    result = CliRunner().invoke(cli, ["--help"], terminal_width=width)
    assert result.exit_code == 0
    assert _MARK_OPTIONS_URL in result.output


def test_the_linked_heading_exists_in_the_docs() -> None:
    from layerforge.cli import _MARK_OPTIONS_URL

    page, _, anchor = _MARK_OPTIONS_URL.removeprefix(
        "https://ravenoak.github.io/layerforge/"
    ).partition("#")
    source = (ROOT / "docs" / f"{page.rstrip('/')}.md").read_text(encoding="utf-8")
    slugs = {
        re.sub(r"[^\w\s-]", "", line.lstrip("# ").strip().lower()).replace(" ", "-")
        for line in source.splitlines()
        if line.startswith("#")
    }
    assert anchor in slugs
