# The pre-write alignment check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After slicing and before any file is written, refuse a stack in which two adjacent pieces can be assembled in more than one way (exit 1, nothing written), unless `--allow-unaligned` is given.

**Architecture:** A pure function `check_alignment(slices)` in `models/slicing/alignment_check.py` finds, for each pair of overlapping pieces in adjacent slices, the marks both slices hold (same object, centre inside both pieces), and fails the pair if there are none or if `rotation_symmetry` finds a turn that maps them onto themselves. `_run` calls it between `slice_model` and `generate_svgs`. A new boolean setting `checks.allow_unaligned` with the flag `--allow-unaligned` turns failures into warnings. The old per-slice warning `Slice._warn_about_unmarked_contours` and its `total_slices` argument are removed.

**Tech Stack:** Python 3.12+, shapely, click 8.5, pydantic (strict), pytest, ruff, pyright, Allium specs (`allium check`, `./scripts/check_specs.sh`), MkDocs.

**Spec:** `docs/superpowers/specs/2026-10-09-pre-write-alignment-check-design.md`. Read it first. The owner approved it on 2026-10-09 ("proceed").

## Global Constraints

- Only TR-2 is an error. A number that does not fit (TR-3, TR-11) and a number that would overprint a mark (TR-5) stay warnings in `SliceSVGDrawer.draw_slice`. Do not touch the drawer.
- `plan_marks` and `adjacent_pairs` are not changed.
- Shared marks are found by object identity (`m is other`), not by equality. The adjuster keeps the objects (`reference_mark_adjuster.py:55`).
- Symmetry tolerance is `max(slice.config.tolerance, 1e-6)`: `rotation_symmetry` raises for 0 and `--mark-tolerance 0` is allowed.
- A model of one layer, and a piece that overlaps nothing in the next layer, have no pair: no error and no warning.
- Message wording: `slices A and B (piece P and piece Q): ...`, indices are 0-based like every existing message. Names never contain a requirement ID (`TR-`, `FR-`, `G-`): a test greps `src` strings.
- Failure output goes to stderr through `click.ClickException` (`Error: ...`, exit 1). With the flag, one `logging.warning` per failure, exit 0.
- Checks run without pipes: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`; with docs or specs: also `./scripts/check_specs.sh` and `uv run mkdocs build --strict`.
- Edit scripts: plain `str.replace` with an `assert s.count(old) == 1`. Never write `if False`. Restore a mutated file from a copy in the scratchpad, never `git checkout -- <file>`.
- zsh: quote variables, one explicit call per case. Write scratch files in the scratchpad directory only.
- This is **Breaking**: a run that used to write files and warn can now exit 1. The changelog says so.

## Review Focus

Input classes the spec implies and the tasks must pin with a test, most likely first:

1. A model of one layer (a flat plate): exit 0, one file, no message (Task 3 test 5).
2. `--mark-tolerance 0`: no traceback (Task 1 test, Task 3 test 7).
3. A split piece (one lower piece, two upper pieces) where only one pair shares the mark: one failure naming the other upper piece (Task 1).
4. A piece in the upper slice that overlaps nothing below: no failure (Task 1).
5. All failures are listed, not only the first, and the output folder is not created (Task 3 test 2).
6. A quoted `"yes"` for `checks.allow_unaligned` in the config file is refused with exit 2 (Task 2).

## File Structure

| File | Responsibility |
|---|---|
| `src/layerforge/models/slicing/alignment_check.py` (new) | `AlignmentFailure`, `check_alignment`. No I/O. |
| `src/layerforge/settings.py` | `ChecksSettings.allow_unaligned`, option key |
| `src/layerforge/cli.py` | `--allow-unaligned`, the call to `check_alignment`, failure output |
| `src/layerforge/models/slicing/slice.py`, `slicer_service.py` | remove the old warning and `total_slices` |
| `tests/test_alignment_check.py` (new) | unit tests on hand-built slices |
| `tests/test_allow_unaligned_setting.py` (new) | setting, flag, config file |
| `tests/test_alignment_check_cli.py` (new) | end to end through `cli` |
| `tests/test_end_to_end.py`, `tests/test_slice_unmarked_contour_warning.py` | one test rewritten, one file deleted |
| docs, specs, `CHANGELOG.md`, `docs/backlog.md` | Task 4 |

---

### Task 1: `check_alignment`

**Files:**
- Create: `src/layerforge/models/slicing/alignment_check.py`
- Test: `tests/test_alignment_check.py`

**Interfaces:**
- Consumes: `Slice` (`.index`, `.contours: list[Polygon]`, `.ref_marks: list[ReferenceMark]`, `.config: ReferenceMarkConfig` with `.tolerance` and `.min_overlap_area`), `adjacent_pairs(contours, *, min_overlap_area=0.0, clearance=0.0) -> list[list[AdjacentPair]]` (each `AdjacentPair` has `.lower`, `.upper` piece indices), `rotation_symmetry(marks, *, tolerance) -> RotationSymmetry` (has `.has_nonidentity`), `require(value, name) -> float`.
- Produces: `AlignmentFailure(lower_slice: int, lower_piece: int, upper_slice: int, upper_piece: int, reason: Literal["no_shared_mark", "rotation_not_fixed"])` with `.message() -> str`; `check_alignment(slices: Sequence[Slice]) -> list[AlignmentFailure]`. Task 3 imports both.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_alignment_check.py`:

```python
"""check_alignment: adjacent pieces share a mark and no turn maps the shared marks onto themselves.

TR-2 and TR-12 (#92). The slices are built by hand, so each case states the marks it holds.
"""

import pytest
from shapely.geometry import box

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkConfig
from layerforge.models.slicing.alignment_check import AlignmentFailure, check_alignment
from layerforge.models.slicing.slice import Slice

LAYER_HEIGHT = 3.0
SQUARE = box(0, 0, 20, 20)


def _slice(index, contours, marks, tolerance=None):
    config = ReferenceMarkConfig(tolerance=tolerance)
    return Slice(index, float(index), contours, config, layer_height=LAYER_HEIGHT, ref_marks=marks)


def _mark(shape, x=10.0, y=10.0):
    return ReferenceMark(x=x, y=y, shape=shape, size=3.0)


def test_a_pair_that_shares_one_triangle_passes():
    mark = _mark("triangle")
    assert check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])]) == []


@pytest.mark.parametrize("shape", ["circle", "square"])
def test_a_pair_that_shares_one_circle_or_square_does_not_fix_the_rotation(shape):
    mark = _mark(shape)
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [mark])])
    assert failures == [AlignmentFailure(0, 0, 1, 0, "rotation_not_fixed")]


def test_a_pair_with_no_marks_shares_no_mark_and_is_not_read_as_unlimited_symmetry():
    failures = check_alignment([_slice(0, [SQUARE], []), _slice(1, [SQUARE], [])])
    assert failures == [AlignmentFailure(0, 0, 1, 0, "no_shared_mark")]


def test_a_mark_in_only_one_slice_is_not_shared():
    mark = _mark("triangle")
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE], [])])
    assert [f.reason for f in failures] == ["no_shared_mark"]


def test_a_mark_outside_the_upper_piece_is_not_shared():
    mark = _mark("triangle", x=5.0, y=5.0)
    upper = box(10, 10, 30, 30)  # overlaps SQUARE, but (5, 5) is not inside it
    failures = check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [upper], [mark])])
    assert [f.reason for f in failures] == ["no_shared_mark"]


def test_one_slice_and_no_slices_pass():
    assert check_alignment([_slice(0, [SQUARE], [])]) == []
    assert check_alignment([]) == []


def test_a_mark_tolerance_of_zero_does_not_raise():
    mark = _mark("circle")
    slices = [_slice(0, [SQUARE], [mark], tolerance=0.0), _slice(1, [SQUARE], [mark], tolerance=0.0)]
    assert [f.reason for f in check_alignment(slices)] == ["rotation_not_fixed"]


def test_each_pair_of_a_split_is_checked_on_its_own():
    left, right = box(0, 0, 10, 20), box(12, 0, 22, 20)
    mark = _mark("triangle", x=5.0, y=10.0)  # inside the left piece only
    lower = _slice(0, [box(0, 0, 22, 20)], [mark])
    upper = _slice(1, [left, right], [mark])
    assert check_alignment([lower, upper]) == [AlignmentFailure(0, 0, 1, 1, "no_shared_mark")]


def test_a_piece_that_overlaps_nothing_has_no_pair_and_passes():
    mark = _mark("triangle")
    far = box(100, 100, 110, 110)
    assert check_alignment([_slice(0, [SQUARE], [mark]), _slice(1, [SQUARE, far], [mark])]) == []


def test_the_messages_name_both_pieces_and_the_remedy():
    none = AlignmentFailure(3, 0, 4, 2, "no_shared_mark").message()
    assert none.startswith("slices 3 and 4 (piece 0 and piece 2): ")
    assert "--mark-min-distance" in none and "--mark-size" in none
    turn = AlignmentFailure(3, 0, 4, 2, "rotation_not_fixed").message()
    assert turn.startswith("slices 3 and 4 (piece 0 and piece 2): ")
    assert "--available-shapes" in turn
```

- [ ] **Step 2: Run the tests, see them fail**

Run: `uv run pytest tests/test_alignment_check.py -q`
Expected: collection error `ModuleNotFoundError: No module named 'layerforge.models.slicing.alignment_check'`. That is the right reason (the module is missing).

- [ ] **Step 3: Write the module**

Create `src/layerforge/models/slicing/alignment_check.py`:

```python
"""The check before any file is written: do adjacent pieces align in exactly one way? (TR-2, TR-12)

For each pair of overlapping pieces in adjacent slices, the marks both slices hold must exist,
and no turn other than none may map them onto themselves (`rotation_symmetry`). A model of one
layer, and a piece that overlaps nothing, have no pair, so nothing is checked for them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from shapely.geometry import Point

from layerforge.models.reference_marks.config import require
from layerforge.models.reference_marks.symmetry import rotation_symmetry

from .adjacency import adjacent_pairs
from .slice import Slice

# `rotation_symmetry` refuses a tolerance of 0, and `--mark-tolerance 0` is allowed.
_MIN_SYMMETRY_TOLERANCE = 1e-6

Reason = Literal["no_shared_mark", "rotation_not_fixed"]


@dataclass(frozen=True)
class AlignmentFailure:
    """A pair of overlapping pieces that can be assembled in more than one way.

    Attributes
    ----------
    lower_slice, lower_piece : int
        The index of the lower slice and of the piece in it.
    upper_slice, upper_piece : int
        The index of the upper slice and of the piece in it.
    reason : {"no_shared_mark", "rotation_not_fixed"}
        ``no_shared_mark``: no mark is a hole in both pieces. ``rotation_not_fixed``: a turn
        other than none maps the shared marks onto themselves.
    """

    lower_slice: int
    lower_piece: int
    upper_slice: int
    upper_piece: int
    reason: Reason

    def message(self) -> str:
        """Return one line for the person: which pieces, what is wrong, what to try."""
        where = (
            f"slices {self.lower_slice} and {self.upper_slice} "
            f"(piece {self.lower_piece} and piece {self.upper_piece})"
        )
        if self.reason == "no_shared_mark":
            return (
                f"{where}: the pieces share no mark. Try a smaller --mark-min-distance or "
                "--mark-size (marks.min_distance or marks.size in the config file)."
            )
        return (
            f"{where}: the marks they share look the same after a turn, so the layers could be "
            "stacked turned. A circle or a square alone cannot fix the rotation. Allow a shape "
            "with a direction in --available-shapes (marks.shapes in the config file)."
        )


def check_alignment(slices: Sequence[Slice]) -> list[AlignmentFailure]:
    """Return every pair of adjacent pieces that does not align in exactly one way.

    The slices must already be adjusted (`SlicerService.slice_model` does that), because a mark
    that the adjuster dropped from either slice is not a hole in both pieces.

    Parameters
    ----------
    slices : Sequence of Slice
        The slices of one run, lowest first.

    Returns
    -------
    list of AlignmentFailure
        One per failing pair, lowest slice first. Empty when every pair aligns.
    """
    failures: list[AlignmentFailure] = []
    for lower, upper in zip(slices, slices[1:], strict=False):
        tolerance = max(require(lower.config.tolerance, "tolerance"), _MIN_SYMMETRY_TOLERANCE)
        boundary = adjacent_pairs(
            [lower.contours, upper.contours], min_overlap_area=lower.config.min_overlap_area
        )[0]
        for pair in boundary:
            lower_piece = lower.contours[pair.lower]
            upper_piece = upper.contours[pair.upper]
            shared = [
                mark
                for mark in lower.ref_marks
                if any(mark is other for other in upper.ref_marks)
                and lower_piece.contains(Point(mark.x, mark.y))
                and upper_piece.contains(Point(mark.x, mark.y))
            ]
            reason: Reason
            if not shared:
                reason = "no_shared_mark"
            elif rotation_symmetry(shared, tolerance=tolerance).has_nonidentity:
                reason = "rotation_not_fixed"
            else:
                continue
            failures.append(
                AlignmentFailure(lower.index, pair.lower, upper.index, pair.upper, reason)
            )
    return failures
```

- [ ] **Step 4: Run the tests, see them pass**

Run: `uv run pytest tests/test_alignment_check.py -q`
Expected: all pass (10 tests: the parametrized one counts twice).

- [ ] **Step 5: Mutation check**

Copy `alignment_check.py` to the scratchpad. In the real file, change `if not shared:` to `if len(shared) < 0:`. Run `uv run pytest tests/test_alignment_check.py -q`. Expected: the "no marks" tests fail (an empty set is read as unlimited symmetry, reason `rotation_not_fixed`). Restore from the copy and re-run: all pass.

- [ ] **Step 6: Format, lint, types, commit**

```bash
uv run ruff format && uv run ruff check && uv run pyright
git add src/layerforge/models/slicing/alignment_check.py tests/test_alignment_check.py
git commit -m "Add check_alignment: adjacent pieces share a mark and no turn maps the marks onto themselves (#92)"
```

---

### Task 2: The setting `checks.allow_unaligned` and the flag `--allow-unaligned`

**Files:**
- Modify: `src/layerforge/settings.py` (`_OPTION_KEYS` near line 42, `ChecksSettings` near line 114)
- Modify: `src/layerforge/cli.py` (`resolve_settings` signature and overrides dict, the `cli` options and function, `process_model`)
- Modify: `docs/configuration.md` (keys table, bullet under `checks.min_overlap_area`)
- Modify: `specs/layerforge.allium` (`config` block)
- Modify: `tests/test_defaults_documented.py` (two lists)
- Test: `tests/test_allow_unaligned_setting.py`

**Interfaces:**
- Consumes: `merge_settings(file_settings, overrides)`, where `overrides` is keyed by option name and `None` means not given.
- Produces: `Settings().checks.allow_unaligned: bool` (default `False`); `resolve_settings(..., allow_unaligned: bool | None = None)`; `process_model(..., allow_unaligned: bool | None = None)`; the click flag `--allow-unaligned` (value `None` when absent, `True` when given). Task 3 reads `settings.checks.allow_unaligned`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_allow_unaligned_setting.py`:

```python
"""checks.allow_unaligned and --allow-unaligned (TR-12, #92): default, flag, file."""

from click.testing import CliRunner

from layerforge.cli import cli
from layerforge.settings import Settings, merge_settings


def test_allow_unaligned_is_off_by_default():
    assert Settings().checks.allow_unaligned is False


def test_the_flag_turns_it_on():
    assert merge_settings(Settings(), {"allow_unaligned": True}).checks.allow_unaligned is True


def test_the_file_value_stands_when_the_flag_is_absent():
    file_settings = Settings.model_validate({"checks": {"allow_unaligned": True}})
    merged = merge_settings(file_settings, {"allow_unaligned": None})
    assert merged.checks.allow_unaligned is True


def test_help_lists_the_flag():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--allow-unaligned" in result.output


def test_a_quoted_value_in_the_config_file_is_refused_with_exit_2(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[checks]\nallow_unaligned = "yes"\n')
    result = CliRunner().invoke(cli, ["--config", str(bad), "--stl-file", "unused.stl"])
    assert result.exit_code == 2
    assert "checks.allow_unaligned" in result.output
```

- [ ] **Step 2: Run the tests, see them fail**

Run: `uv run pytest tests/test_allow_unaligned_setting.py -q`
Expected: `test_allow_unaligned_is_off_by_default` fails with `AttributeError` on `allow_unaligned`; `test_the_flag_turns_it_on` fails with `KeyError: 'allow_unaligned'`; the help test fails on the missing flag. Read each failure: they must be about the missing field and option, not a typo in the test.

- [ ] **Step 3: Settings**

In `src/layerforge/settings.py`, add to `_OPTION_KEYS` after `"number_height": ("number", "height"),`:

```python
    "allow_unaligned": ("checks", "allow_unaligned"),
```

Replace the `ChecksSettings` class with:

```python
class ChecksSettings(BaseModel):
    """The ``[checks]`` table: when two pieces count as sharing a mark (TR-9), and whether a
    stack that cannot be aligned in one way is still written (TR-12).
    """

    model_config = _STRICT

    min_overlap_area: float = Field(default=0.0, ge=0)  # no option (TR-16)
    allow_unaligned: bool = False
```

- [ ] **Step 4: Command line**

In `src/layerforge/cli.py`:

1. `resolve_settings`: add the parameter `allow_unaligned: bool | None = None,` after `number_height`, and the entry `"allow_unaligned": allow_unaligned,` in the dict after `"number_height": number_height,`.
2. After the `--number-height` option, before `def cli(`, add:

```python
@click.option(
    "--allow-unaligned",
    is_flag=True,
    default=None,
    help="Write the files even when two adjacent layers could be stacked in more than one way. "
    "Each such pair is then a warning and the exit code is 0. Without it nothing is written "
    "and the exit code is 1.",
)
```

3. Add `allow_unaligned: bool | None,` as the last parameter of `cli`, and `allow_unaligned=allow_unaligned,` as the last argument of its `resolve_settings` call.
4. `process_model`: add `allow_unaligned: bool | None = None,` after `number_height`, a docstring entry after the `number_height` one:

```
    allow_unaligned : bool, optional
        Write the files even when two adjacent layers could be stacked in more than one way.
        Falls back to the config file, then its default (off).
```

and `allow_unaligned=allow_unaligned,` as the last argument of its `resolve_settings` call.

- [ ] **Step 5: Docs table, bullet and spec default**

`docs/configuration.md`: after the row `| \`checks.min_overlap_area\` | none | \`0.0\` |` add

```
| `checks.allow_unaligned` | `--allow-unaligned` | `false` |
```

and after the bullet that starts `- \`checks.min_overlap_area\``, add

```
- `checks.allow_unaligned` – write the files even when two adjacent layers could be stacked in more than one way (TR-12). Each such pair is then a warning and the exit code is 0. It is the same as `--allow-unaligned`. Default `false`.
```

`specs/layerforge.allium`, in the `config { ... }` block after `default_min_overlap_area`, add

```
    default_allow_unaligned: Boolean = false    -- TR-12: write the files although a pair is not aligned
```

`tests/test_defaults_documented.py`: add `("default_allow_unaligned", ("checks", "allow_unaligned")),` after the `default_min_overlap_area` tuple in the parametrize list, and `"default_allow_unaligned",` after `"default_min_overlap_area",` in the set of `test_every_default_of_the_spec_config_block_is_compared`.

- [ ] **Step 6: Run the tests, see them pass**

Run: `uv run pytest tests/test_allow_unaligned_setting.py tests/test_defaults_documented.py tests/test_cli_checks_before_prompt.py -q`
Expected: pass. If `test_the_keys_table_names_the_option_of_each_setting` fails for the new key, the row's option cell does not equal `--allow-unaligned`.

- [ ] **Step 7: Full checks and commit**

```bash
uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q
./scripts/check_specs.sh
git add -A src tests docs specs
git commit -m "Add checks.allow_unaligned and --allow-unaligned (#92)"
```

---

### Task 3: The command checks before it writes

**Files:**
- Modify: `src/layerforge/cli.py` (`_run`, import)
- Modify: `src/layerforge/models/slicing/slice.py` (remove `_warn_about_unmarked_contours`, `total_slices`)
- Modify: `src/layerforge/models/slicing/slicer_service.py` (drop `total_slices=len(slice_positions),`)
- Delete: `tests/test_slice_unmarked_contour_warning.py`
- Modify: `tests/test_end_to_end.py` (`test_cli_warns_when_no_mark_fits`)
- Test: `tests/test_alignment_check_cli.py`

**Interfaces:**
- Consumes: `check_alignment`, `AlignmentFailure.message()` (Task 1); `settings.checks.allow_unaligned` (Task 2).
- Produces: nothing new for other tasks.

- [ ] **Step 1: Write the failing end-to-end tests**

Create `tests/test_alignment_check_cli.py`:

```python
"""The command checks every pair of adjacent layers before it writes (TR-2, TR-12, #92)."""

import logging

import pytest
import trimesh
from click.testing import CliRunner

from layerforge.cli import cli


def _stl(tmp_path, mesh, name):
    path = tmp_path / f"{name}.stl"
    mesh.export(path)
    return path


@pytest.fixture
def cube_stl(tmp_path):
    return _stl(tmp_path, trimesh.creation.box(extents=(20, 20, 20)), "cube")


@pytest.fixture
def cone_stl(tmp_path):
    return _stl(tmp_path, trimesh.creation.cone(radius=20, height=30), "cone")


def _invoke(stl, out, *extra):
    return CliRunner().invoke(cli, ["--stl-file", str(stl), "--output-folder", str(out), *extra])


def test_an_aligned_stack_is_written_and_exits_0(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out)
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 7
    assert "Nothing was written" not in result.stderr


def test_a_stack_with_pairs_that_share_no_mark_writes_nothing_and_exits_1(cone_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cone_stl, out)
    assert result.exit_code == 1
    assert not out.exists()
    assert "Traceback" not in result.stderr
    assert "slices 7 and 8 (piece 0 and piece 0): the pieces share no mark" in result.stderr
    assert "slices 8 and 9 (piece 0 and piece 0): the pieces share no mark" in result.stderr
    assert result.stderr.count("the pieces share no mark") == 2  # every failure, not the first
    assert "Nothing was written. Use --allow-unaligned" in result.stderr


def test_allow_unaligned_writes_every_file_and_warns_once_per_failure(cone_stl, tmp_path, caplog):
    out = tmp_path / "out"
    with caplog.at_level(logging.WARNING):
        result = _invoke(cone_stl, out, "--allow-unaligned")
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10
    messages = [r.getMessage() for r in caplog.records if "share no mark" in r.getMessage()]
    assert len(messages) == 2


def test_the_config_file_can_allow_it(cone_stl, tmp_path):
    config = tmp_path / "allow.toml"
    config.write_text("[checks]\nallow_unaligned = true\n")
    out = tmp_path / "out"
    result = _invoke(cone_stl, out, "--config", str(config))
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10


def test_a_list_with_no_shape_that_has_a_direction_fails_every_pair(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out, "--available-shapes", "circle")
    assert result.exit_code == 1
    assert not out.exists()
    assert result.stderr.count("look the same after a turn") == 6  # 7 slices, 6 pairs


def test_a_model_of_one_layer_passes_without_a_message(tmp_path):
    plate = _stl(tmp_path, trimesh.creation.box(extents=(40, 40, 2)), "plate")
    out = tmp_path / "out"
    result = _invoke(plate, out)
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 1
    assert "share no mark" not in result.stderr
    assert "Nothing was written" not in result.stderr


def test_a_mark_tolerance_of_zero_does_not_end_in_a_traceback(cube_stl, tmp_path):
    out = tmp_path / "out"
    result = _invoke(cube_stl, out, "--mark-tolerance", "0")
    assert result.exit_code == 0, result.stderr
    assert "Traceback" not in result.stderr
```

- [ ] **Step 2: Run them, see them fail**

Run: `uv run pytest tests/test_alignment_check_cli.py -q`
Expected: the cone tests fail because the command exits 0 and writes files (the check is not called); the circle test fails the same way. The cube, plate and tolerance tests pass already. That split is the right red: only the refusal is missing.

- [ ] **Step 3: Call the check in `_run`**

In `src/layerforge/cli.py` add to the imports (after the `adjacency` import from #211):

```python
from layerforge.models.slicing.alignment_check import check_alignment
```

In `_run`, directly after the `try`/`except UnrepairableContourError` block that assigns `slices`, add:

```python
    failures = check_alignment(slices)
    if failures:
        lines = [failure.message() for failure in failures]
        if not settings.checks.allow_unaligned:
            raise click.ClickException(
                "\n".join(
                    [
                        *lines,
                        "Nothing was written. Use --allow-unaligned to write the files anyway.",
                    ]
                )
            )
        for line in lines:
            logging.warning(line)
```

- [ ] **Step 4: Run them, see them pass**

Run: `uv run pytest tests/test_alignment_check_cli.py -q`
Expected: pass. If `== 7` or `== 10` or `== 6` or the slice numbers 7/8/9 differ, the model's slicing differs from the probe: print `result.stderr`, and state the measured number in the test only after reading it.

- [ ] **Step 5: Remove the old warning**

`src/layerforge/models/slicing/slice.py`: delete the method `_warn_about_unmarked_contours`, its call at the end of `adjust_marks`, the `total_slices` parameter, its docstring entry and `self.total_slices = total_slices`; change the `adjust_marks` docstring first line to `Filter `ref_marks` to what actually fits this slice (TR-5).`. Run `uv run ruff check` and remove the imports it reports as unused (`logging`, `Point`).

`src/layerforge/models/slicing/slicer_service.py`: delete the line `total_slices=len(slice_positions),`.

Delete `tests/test_slice_unmarked_contour_warning.py` (`git rm`). Its subject no longer exists.

- [ ] **Step 6: Rewrite the old end-to-end test**

In `tests/test_end_to_end.py` replace `test_cli_warns_when_no_mark_fits` with two tests that keep its arguments (`LAYER_HEIGHT`, `--target-height 10`):

```python
def test_cli_refuses_when_no_mark_fits(box_stl: Path, tmp_path: Path) -> None:
    """At layer height 5 the default mark (size 5, web 2.5) does not fit a 10 mm cube."""
    out = tmp_path / "out"
    result = _run_cli(
        "--stl-file",
        str(box_stl),
        "--layer-height",
        str(LAYER_HEIGHT),
        "--output-folder",
        str(out),
        "--target-height",
        "10",
    )
    assert result.returncode == 1
    assert "--mark-min-distance" in result.stderr
    assert "--allow-unaligned" in result.stderr
    assert not list(out.glob("slice_*.svg"))


def test_cli_writes_with_a_warning_when_no_mark_fits_and_allow_unaligned(
    box_stl: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    result = _run_cli(
        "--stl-file",
        str(box_stl),
        "--layer-height",
        str(LAYER_HEIGHT),
        "--output-folder",
        str(out),
        "--target-height",
        "10",
        "--allow-unaligned",
    )
    assert result.returncode == 0, result.stderr
    assert "--mark-min-distance" in result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 2
```

- [ ] **Step 7: Full suite, decide each failure**

Run: `uv run pytest -q`. For each failing test, read it and decide: it expects the old behavior (a warning and exit 0 for a stack that now fails) and is updated with the reason in a comment, or it exposes a fault in `check_alignment` (stop and report, do not edit the test). List every changed test in the commit message.

- [ ] **Step 8: Mutation checks**

Copy `cli.py` to the scratchpad. Remove the `raise click.ClickException(...)` block (leave the loop of warnings) and run `uv run pytest tests/test_alignment_check_cli.py -q`: the refusal tests must fail. Restore from the copy and re-run: pass.

- [ ] **Step 9: Full checks and commit**

```bash
uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q
git add -A src tests
git commit -m "Check that adjacent layers align in one way before writing (#92)"
```

---

### Task 4: Documentation, specs, changelog, backlog

**Files:**
- Modify: `docs/alignment_requirements.md`, `docs/requirements.md`, `docs/getting_started.md`, `docs/configuration.md`, `README.md`, `CHANGELOG.md`, `docs/backlog.md`, `specs/alignment.allium`, `specs/layerforge.allium`, `docs/superpowers/specs/2026-10-09-pre-write-alignment-check-design.md`

**Interfaces:**
- Consumes: the behavior of Tasks 1 to 3. Run it before you describe it.
- Produces: none.

- [ ] **Step 1: Measure what the docs will quote**

Write `cube10.stl` (a 10 mm cube) and run, from a scratchpad folder:
`uv run --project <repo> layerforge --stl-file cube10.stl --layer-height 5 --output-folder out_a` and the same with `--allow-unaligned`. Copy the first stderr line of each, the exit code and the file count into the docs below. Run `--available-shapes circle` on a 20 mm cube and copy that line too. Do not write a message from memory.

- [ ] **Step 2: `docs/alignment_requirements.md`**

Replace the TR-12 row text with:

```
| TR-12 | After slicing and before writing any file, the tool checks TR-2 for every pair of adjacent pieces. If one fails, it writes nothing, prints to stderr the slices and pieces of the pair and the reason, and exits with code 1. `--allow-unaligned` (`checks.allow_unaligned`) turns these errors into warnings, writes the files and exits with 0. A number that does not fit (TR-3, TR-11) and a number that would overprint a mark (TR-5) are warnings, not errors (owner's decision, 2026-10-09). A short baseline (TR-4) is always a warning. Status: built in #92. `check_alignment` (`models/slicing/alignment_check.py`) finds the marks two slices share (the same mark in both, with its centre inside both pieces) and fails a pair that shares none (`no_shared_mark`) or whose shared marks a turn maps onto themselves (`rotation_not_fixed`). A model of one layer, and a piece that overlaps nothing, have no pair and pass without a message. | G-4 (#60) |
```

In TR-2: replace `Nothing calls either yet. The rest comes with #60 and #92.` with `` `check_alignment` calls both for every pair before any file is written (#92). The end-to-end proof for several models is #60.``. In TR-8: replace `Nothing yet warns when the list holds no shape with a direction (#92).` with `With no shape that has a direction in the list, every pair fails the check of TR-12 (#92).` In TR-4 add at the end of its Status (or after the last sentence): `Not built: a pair shares at most one mark today, so no baseline exists (#213, #215).`

- [ ] **Step 3: `docs/requirements.md`**

Add after the FR-31 row:

```
| FR-32 | After slicing and before any file is written, every pair of overlapping pieces in adjacent slices is checked. The marks both slices hold, with the centre inside both pieces, are the pair's shared marks. A pair with none, or whose shared marks a turn other than none maps onto themselves, is a failure. Without `--allow-unaligned` (`checks.allow_unaligned`) the command prints one line per failure and `Nothing was written. Use --allow-unaligned to write the files anyway.` to stderr, writes no file and exits with code 1. With it, each failure is a warning, the files are written and the exit code is 0. A model of one layer passes without a message. A number that does not fit stays a warning of the drawer. | `models/slicing/alignment_check.py`, `cli.py::_run` | `test_alignment_check`, `test_alignment_check_cli`, `test_allow_unaligned_setting` |
```

Replace the sentence in FR-22 `If a slice then has a contour with no mark, one warning is logged for the slice (\`No reference mark fits N of M contours in slice I. Try a smaller --mark-min-distance or --mark-size.\`). The slice is still written.` with `If a piece is left with no mark, the pair it belongs to fails the check of FR-32.` Replace the last sentence of the Purpose paragraph (`The tool does not check that yet (see G-4).`) with `The tool checks each pair of adjacent layers before it writes (FR-32); G-4 says what it does not check.` Replace the whole G-4 row with:

```
| G-4 (#60) | The check of FR-32 looks at each pair of adjacent layers on its own. It does not prove that a whole stack rebuilds one way, and a straight shape still gets one mark that is a hole in every layer (TR-9, #215). A pair shares at most one mark, so the baseline of TR-4 is not checked. | `check_alignment`, `plan_marks`, `ReferenceMarkCalculator.choose_mark_for_pair`. | A stack can pass the check and still have a bore through every layer. Target: TR-1, TR-4, TR-9. |
```

Add the `Slice` change to nothing else. Grep `docs`, `README.md`, `specs` for `total_slices`, `No reference mark fits` and `only one layer` and fix every hit that is not history.

- [ ] **Step 4: User docs**

`docs/getting_started.md`: replace the bullet that starts with ``` ``WARNING:root:No reference mark fits 1 of 1 contours ``` with two bullets, using the lines measured in Step 1 (exit code 1, the final `Nothing was written` line, the `--allow-unaligned` path, and what a person does: use a smaller `--mark-size` or `--mark-min-distance`, or allow a shape with a direction). `README.md`: add after the `--number-height` bullet: `` - `--allow-unaligned` – write the files even when two adjacent layers could be stacked in more than one way. Without it the command prints the pairs, writes nothing and exits with 1. Same as `checks.allow_unaligned`. `` Run every command on both pages.

- [ ] **Step 5: `CHANGELOG.md`**

Under `## [Unreleased]` / `### Changed`, as the first item, wrapped at 100 columns:

```
- **Breaking:** The command checks, before it writes any file, that every pair of adjacent
  layers can be stacked in one way only (TR-2, TR-12, #92). A pair whose pieces share no mark,
  or whose shared marks a turn maps onto themselves (one circle or one square), now stops the
  run: one line per pair on stderr, no file written, exit code 1. `--allow-unaligned`
  (`checks.allow_unaligned`) writes the files anyway and logs each pair as a warning. The
  warning `No reference mark fits N of M contours in slice I` is gone: a piece with a
  neighbour and no mark fails the check, and a model of one layer passes without a message.
  A number that does not fit stays a warning. `Slice` no longer takes `total_slices`.
```

- [ ] **Step 6: `specs/alignment.allium`**

Replace `enum FailureReason { not_alignable | number_does_not_fit | mark_misplaced }` and the comment above it with:

```
-- TR-12: the two ways a pair of pieces fails the check. A number that does not fit (TR-3)
-- and a number that would overprint a mark (TR-5) are warnings, not failures (owner's
-- decision, 2026-10-09).
enum FailureReason { no_shared_mark | rotation_not_fixed }
```

Change `value Failure` to hold `pair: AdjacentPair` and `reason: FailureReason` (read lines 57 to 62 and keep its comment style). In the three TR-12 rules replace `layer: failure.layer, piece: failure.piece,` by `pair: failure.pair,` (and the same in the `FailureReported` and `FailureWarned` names' arguments if they are declared). In the guidance of `TR12_WriteAlignedStack` replace the sentence listing the three failures with: `alignment_failures runs after slicing and before any file is written. It reports, for every pair of adjacent pieces: no shared mark (no_shared_mark) and a turn that maps the shared marks onto themselves (rotation_not_fixed). Built as check_alignment (#92).` Update the file header STATUS paragraph with one sentence: `TR-12 is built for TR-2 only (#92).` Run `allium check specs/alignment.allium` and `./scripts/check_specs.sh`: the diagnostics by code and count must equal those of `main`.

- [ ] **Step 7: `specs/layerforge.allium`**

Add `allow_unaligned: Boolean` to `Run`, set it in the `Run.created(...)` call with `allow_unaligned: options.allow_unaligned ?? config.default_allow_unaligned` (read the surrounding lines, lines 170 to 190, and follow their style), add `sliced -> rejected` to the `Run` transition graph, and add after `FR22_AdjustMarks`:

```
rule FR32_RefuseUnalignedStack {
    when: run: Run.status becomes sliced
    requires: not run.allow_unaligned
    requires: alignment_failures(run).count > 0
    ensures: run.status = rejected
    @guidance
        -- Every pair of overlapping pieces in adjacent slices is checked: it fails when no
        -- mark is a hole in both pieces, or when a turn other than none maps the shared marks
        -- onto themselves. One line per failure and "Nothing was written. Use
        -- --allow-unaligned to write the files anyway." go to stderr, exit code 1, and no file
        -- is written. A model of one layer has no pair. A number that does not fit is not a
        -- failure (FR-26).
}

rule FR32_WarnUnalignedStack {
    when: run: Run.status becomes sliced
    requires: run.allow_unaligned
    requires: alignment_failures(run).count > 0
    ensures: AlignmentWarned(run: run)
    @guidance
        -- One warning per failure. The files are written and the exit code is 0.
}
```

Replace the last two sentences of the `FR22_AdjustMarks` guidance (`A slice can end with a contour that has no mark. One warning is logged for the slice; it is still written.`) with `A slice can end with a contour that has no mark: the pair it belongs to then fails FR32.` Run `allium check`, `./scripts/check_specs.sh`, then `allium:weed` in check mode on both specs against `alignment_check.py` and `_run`; fix every divergence it reports.

- [ ] **Step 8: The spec of this work**

In `docs/superpowers/specs/2026-10-09-pre-write-alignment-check-design.md` change the first Testing bullet "the thin tube exits 1" to "the cone exits 1" (the thin tube needs a boolean engine that is not a dependency), and the Status line to `Status: approved 2026-10-09, built in #92.` Replace the two example lines under "The command" with the two messages that `AlignmentFailure.message()` returns, copied from a run.

- [ ] **Step 9: Backlog**

In `docs/backlog.md` rank 20 (#92): append `(done, the PR of this row: check_alignment, --allow-unaligned; the number stays a warning, decided 2026-10-09)`; rank 79 (#212): `(done with #92: the G-4 row is rewritten)`; rank 21 (#60): leave. Add a Session H paragraph to the Status section naming the measured cone result (pairs 7-8 and 8-9 fail, ten files with the flag).

- [ ] **Step 10: Checks, review, commit**

```bash
uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q
./scripts/check_specs.sh
uv run mkdocs build --strict
```

Run `/code-review` (medium) on the branch diff and read the code behind each note before acting. Commit:

```bash
git add -A
git commit -m "Document the pre-write alignment check (#92, #212)"
```

---

### Task 5: Branch review and PR

- [ ] **Step 1:** Re-run, bare: `uv run ruff format --check && uv run ruff check && uv run pyright && uv run pytest -q && ./scripts/check_specs.sh && uv run mkdocs build --strict`.
- [ ] **Step 2:** Re-run `probe_defaults.py` and `probe_caps.py` from the scratchpad. Cubes, the cylinder and the sphere must still produce the same marks and pass the check; the cone and the thin tube must now fail. Report each result.
- [ ] **Step 3:** Push, open the PR with `--body-file`, wait for CI (`gh pr checks N --watch`), confirm `gh pr view N --json headRefOid` equals `git rev-parse HEAD`, then write the PR text from the runs (counts from `--collect-only` and `git show --stat`), re-read it against the diff and the issues it names, and only then merge as a separate command (`gh pr merge N --squash --delete-branch`).
- [ ] **Step 4:** After the merge, `gh run list --branch main` shows the tests and the docs workflow green.
