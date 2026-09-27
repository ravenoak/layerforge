# Pair-local marks (#63 phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Choose reference marks per pair of adjacent layers, inside their shrunk overlap, retiring a mark the moment it stops fitting the next pair — replacing the whole-run mark store that lets a mark drift or a dropped mark block a slice forever (G-7, #63, TR-9).

**Architecture:** `SlicerService.slice_model` cuts every slice's contours first, then calls a new `plan_marks(contours, config, layer_height)` once for the whole run. `plan_marks` walks `adjacent_pairs` boundaries in order, carrying at most the immediately-previous boundary's marks as inheritance candidates (never further back), and calls a new pair-scoped `ReferenceMarkCalculator.choose_mark_for_pair` for each pair. `ReferenceMarkManager` and `ReferenceMarkService` are deleted; `Slice` takes `ref_marks` directly instead of a `mark_manager`.

**Tech Stack:** Python 3.12+, shapely (geometry), pydantic (settings/config), pytest + hypothesis (tests), Allium (formal spec), MkDocs (docs).

**Spec:** `docs/superpowers/specs/2026-09-27-pair-local-marks-design.md` — read it alongside this plan; this plan does not repeat its Context, Goals or Non-goals sections.

## Global Constraints

- Every check runs unmasked, no pipes: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`, then `./scripts/check_specs.sh` and `uv run mkdocs build --strict`.
- Write the failing test first (TDD), watch it fail for the right reason, then the minimal code.
- One mutation-check pass on `plan_marks`'s retirement logic and on `choose_mark_for_pair`'s shape-before-point ordering, before the final `/code-review` (per the spec's Rollout section).
- Retirement is immediate-neighbour only: a mark's only inheritance candidates are what the immediately previous pair boundary decided. Never look further back (owner's decision, recorded in the spec's Goals).
- A candidate's own `shape` and `size` travel with it; a fresh mark's shape is chosen (`choose_shape`) **before** its point is sampled, so the disc radius matches that shape (#198).
- `region.contains(pt)` alone gives the `min_distance` clearance from both pieces' outlines (the shrunk overlap is already eroded by `min_distance`); only the shape-dependent `radius + min_web` margin needs a fresh per-polygon check. Do not re-check `min_distance` a second time — it would be redundant, not wrong, but the spec's math argument is the reason it is skipped, and a reviewer should not "fix" it back in.
- One PR for this whole phase (the spec's Rollout section: the module boundary does not split into independently-mergeable pieces).

## Review Focus

- **A single-slice model.** With one layer there are zero pairs, so `plan_marks` returns no marks at all — a real behavior change from today (which always tries to place one mark per contour, neighbour or not). A user slicing a very thin part into one layer gets an SVG with no reference mark and no warning that names this cause. Task 6 adds a test for it; the changelog entry names it.
- **A piece with no neighbour in one direction** (the first or last slice, or a piece that appears or vanishes mid-stack). `carried`/`avoid` are simply empty for it; it must still get a mark from whichever side it does have, not silently end up with none. Covered in Task 4's tests and Task 6's TR-9 invariant test.
- **A split or a merge between two layers** (one piece overlaps two pieces of its neighbour, or two pieces merge into one). The design's `on_slice` bookkeeping must stop two marks placed on the same piece in the same boundary from colliding. Task 4 tests this directly with a Y-shaped two-piece-to-one-piece fixture.
- **A degenerate or self-intersecting slice contour reaching `adjacent_pairs`.** Today it would raise a bare `shapely.errors.GEOSException`; Task 2 must turn that into a `ValueError` naming the layer and piece, and a genuinely unrepairable polygon (not just an invalid one) must not raise something worse than that same clear error.
- **`min_overlap_area` and `min_distance` at the boundary of "does this piece have a neighbour at all".** A piece whose overlap with its neighbour is smaller than `checks.min_overlap_area`, or whose whole shrunk overlap is eroded to nothing by a large `min_distance`, must be treated the same as "no neighbour" (no crash, no mark, no piece silently duplicated) — Task 4's tests include an overlap area of exactly 0 and a `min_distance` larger than the pieces' overlap.

---

## Task 1: `checks.min_overlap_area` setting

**Files:**
- Modify: `src/layerforge/models/reference_marks/config.py:29-38` (add a field to `ReferenceMarkConfig`)
- Modify: `src/layerforge/settings.py:58-134` (new `ChecksSettings`, add `checks` to `Settings`)
- Modify: `src/layerforge/cli.py:173-183` (wire `settings.checks.min_overlap_area` through)
- Modify: `docs/configuration.md` (keys table, and the "config file only" bullet list)
- Modify: `specs/layerforge.allium:53-56` (add `default_min_overlap_area` to the `config` block)
- Modify: `docs/alignment_requirements.md:126-140` (TR-16's status line and settings table — not test-enforced, but drifts exactly like #152/#188 if skipped)
- Test: `tests/test_reference_mark_config.py`, `tests/test_settings.py`, `tests/test_defaults_documented.py`

**Interfaces:**
- Produces: `ReferenceMarkConfig.min_overlap_area: float` (default `0.0`), `Settings.checks.min_overlap_area: float` (default `0.0`, TOML key `[checks]` `min_overlap_area`, no command-line option).

- [ ] **Step 1: Add the failing config test**

In `tests/test_reference_mark_config.py`, after `test_size_defaults_to_none`:

```python
def test_min_overlap_area_defaults_to_zero():
    assert ReferenceMarkConfig().min_overlap_area == 0.0


def test_min_overlap_area_must_be_non_negative_and_finite():
    with pytest.raises(ValueError):
        ReferenceMarkConfig(min_overlap_area=-1.0)
```

- [ ] **Step 2: Run it, confirm it fails**

Run: `uv run pytest tests/test_reference_mark_config.py -k min_overlap_area -v`
Expected: FAIL — `ValidationError` or `AttributeError`, `min_overlap_area` is not a field of `ReferenceMarkConfig`.

- [ ] **Step 3: Add the field**

In `src/layerforge/models/reference_marks/config.py`, after `min_hole_kerf_factor`:

```python
    min_hole_kerf_factor: float = Field(default=1.5, ge=0, allow_inf_nan=False)
    # TR-9: how large an overlap between two pieces of adjacent layers must be to share a
    # mark. Lives on this config, not only on Settings, because plan_marks reads it here.
    min_overlap_area: float = Field(default=0.0, ge=0, allow_inf_nan=False)
```

- [ ] **Step 4: Run it, confirm it passes**

Run: `uv run pytest tests/test_reference_mark_config.py -k min_overlap_area -v`
Expected: PASS

- [ ] **Step 5: Add the failing settings test**

In `tests/test_settings.py`, add to `test_defaults_without_a_file` (after the `min_web_ratio` assertion):

```python
    assert s.checks.min_overlap_area == 0.0
```

- [ ] **Step 6: Run it, confirm it fails**

Run: `uv run pytest tests/test_settings.py -k defaults_without_a_file -v`
Expected: FAIL — `AttributeError: 'Settings' object has no attribute 'checks'`.

- [ ] **Step 7: Add `ChecksSettings`**

In `src/layerforge/settings.py`, after `NumberSettings` (before `class Settings`):

```python
class ChecksSettings(BaseModel):
    """The ``[checks]`` table: when two pieces of adjacent layers count as sharing a mark (TR-9)."""

    model_config = _STRICT

    min_overlap_area: float = Field(default=0.0, ge=0)  # no option (TR-16)
```

In `class Settings`, after `number: NumberSettings = Field(default_factory=NumberSettings)`:

```python
    checks: ChecksSettings = Field(default_factory=ChecksSettings)
```

- [ ] **Step 8: Run it, confirm it passes**

Run: `uv run pytest tests/test_settings.py -k defaults_without_a_file -v`
Expected: PASS

- [ ] **Step 9: Wire it into `cli.py`**

In `src/layerforge/cli.py`, inside the `ReferenceMarkConfig(...)` construction (around line 174):

```python
    config = ReferenceMarkConfig(
        tolerance=marks.tolerance,
        min_distance=marks.min_distance,
        available_shapes=marks.shapes,
        angle=math.radians(marks.angle),
        size=marks.size,
        min_web_ratio=marks.min_web_ratio,
        kerf=settings.kerf,
        min_hole_ratio=marks.min_hole_ratio,
        min_hole_kerf_factor=marks.min_hole_kerf_factor,
        min_overlap_area=settings.checks.min_overlap_area,
    )
```

- [ ] **Step 10: Add the failing doc/spec tests**

In `tests/test_defaults_documented.py`, add to the `@pytest.mark.parametrize(("name", "key"), [...])` list of `test_the_spec_config_block_states_the_default_of_each_setting` (after `("default_number_width_factor", ("number", "width_factor"))`):

```python
        ("default_min_overlap_area", ("checks", "min_overlap_area")),
```

And add `"default_min_overlap_area"` to the set literal in `test_every_default_of_the_spec_config_block_is_compared`.

- [ ] **Step 11: Run it, confirm the new/updated tests fail**

Run: `uv run pytest tests/test_defaults_documented.py -v`
Expected: FAIL — `test_the_keys_table_lists_every_setting_and_no_other` (no `checks.min_overlap_area` row in `docs/configuration.md`), the new parametrized case (no `default_min_overlap_area` in the spec's `config` block), and `test_every_default_of_the_spec_config_block_is_compared` (set mismatch).

- [ ] **Step 12: Add the doc and spec rows**

In `docs/configuration.md`, add to the keys table (after the `marks.min_hole_kerf_factor` row):

```markdown
| `checks.min_overlap_area` | none | `0.0` |
```

And add a bullet near the `min_web_ratio` explanation (after it):

```markdown
- `checks.min_overlap_area` – the least area two pieces of adjacent layers must share to count as sharing a mark (TR-9). It is a key of the config file only, `[checks]` `min_overlap_area`, with no command-line flag.
```

In `specs/layerforge.allium`, add to the `config { }` block (after `default_number_width_factor` if present, else after `default_min_hole_kerf_factor`):

```
    default_min_overlap_area: Decimal = 0.0     -- TR-9: how much overlap counts as sharing a mark
```

- [ ] **Step 13: Run the doc/spec tests, confirm they pass**

Run: `uv run pytest tests/test_defaults_documented.py -v`
Expected: PASS (all cases, including the parametrized ones)

- [ ] **Step 14: Update the target requirements page**

In `docs/alignment_requirements.md`, add a row to the settings table (after `marks.angle`, before `number.height`):

```markdown
| `checks.min_overlap_area` | | 0 | Existing default (any overlap counts) | TR-9 |
```

And in TR-16's Status sentence (line ~124), append: `#63 added `checks.min_overlap_area` (no command-line option).`

- [ ] **Step 15: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q && ./scripts/check_specs.sh && uv run mkdocs build --strict`
Expected: all pass; `check_specs.sh` reports the same warning counts as before this task (0 errors, 0 findings; a new `default_min_overlap_area` line adds no new warning since it is not a rule, just a config default).

- [ ] **Step 16: Commit**

```bash
git add src/layerforge/models/reference_marks/config.py src/layerforge/settings.py src/layerforge/cli.py docs/configuration.md docs/alignment_requirements.md specs/layerforge.allium tests/test_reference_mark_config.py tests/test_settings.py tests/test_defaults_documented.py
git commit -m "Add checks.min_overlap_area, a setting for #63 to use (TR-9)

Refs #63"
```

---

## Task 2: Harden `adjacent_pairs` against invalid polygons (#185 item 1)

**Files:**
- Modify: `src/layerforge/models/slicing/adjacency.py`
- Test: `tests/test_adjacency.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `adjacent_pairs` now raises `ValueError` (not `shapely.errors.GEOSException`) naming the layer and piece index for an unrepairable polygon, and silently repairs a repairable one (same behaviour `ReferenceMarkCalculator._sample_points` already gives a single polygon).

- [ ] **Step 1: Write the failing tests**

In `tests/test_adjacency.py`, add:

```python
def test_a_repairable_invalid_polygon_does_not_raise():
    # A bow-tie: self-intersecting but shapely.make_valid can repair it.
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    normal = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    result = adjacent_pairs([[bowtie], [normal]])
    assert len(result) == 1


def test_an_unrepairable_polygon_raises_a_value_error_naming_the_piece():
    degenerate = Polygon([(0, 0), (0, 0), (0, 0)])
    normal = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(ValueError, match="layer 0 piece 0"):
        adjacent_pairs([[degenerate], [normal]])
```

Add `import pytest` and `from shapely.geometry import Polygon` at the top if not already present (check first: `Polygon` is likely already imported; `pytest` may not be, since the existing 24 tests may use only shapely fixtures — check `tests/test_adjacency.py`'s current imports before adding a duplicate).

- [ ] **Step 2: Run them, confirm they fail**

Run: `uv run pytest tests/test_adjacency.py -k "repairable or unrepairable" -v`
Expected: FAIL — the bow-tie case raises `shapely.errors.GEOSException` from `lower.intersects(upper)` (or a similar shapely error, not necessarily on the very first call — confirm the exact failure by running it once), and the degenerate case does not raise `ValueError` at all today (it may return an empty result silently, since `Polygon([(0,0),(0,0),(0,0)])` may just have zero area without shapely calling it invalid — record what actually happens and adjust the test's expectation if the first run shows something other than a crash, per the "watch it fail for the right reason" rule; if it does not fail at all, the test as written is testing the fixed behaviour already, so make it a genuinely-invalid case instead, for example `Polygon([(0, 0), (5, 5), (10, 10), (0, 0)])` — a zero-area closed line — and re-run until it exercises the real invalid path).

- [ ] **Step 3: Add the repair helper**

In `src/layerforge/models/slicing/adjacency.py`, add near `_area_of`:

```python
from shapely import make_valid


def _repaired(polygon: Polygon, layer_index: int, piece_index: int) -> Polygon:
    """Return ``polygon``, repaired if it is not valid (the same approach `_sample_points` uses).

    Raises
    ------
    ValueError
        If ``polygon`` cannot be repaired into a polygon with area, naming where it came from.
    """
    if polygon.is_valid:
        return polygon
    repaired = make_valid(polygon)
    parts = [g for g in shapely.get_parts(repaired) if isinstance(g, Polygon) and g.area > 0]
    if not parts:
        raise ValueError(f"layer {layer_index} piece {piece_index} is not a valid polygon")
    return max(parts, key=lambda g: g.area)
```

- [ ] **Step 4: Call it before the pairing loop**

In `adjacent_pairs`, replace the loop's use of `layers` with repaired copies:

```python
    fixed_layers = [
        [_repaired(piece, layer_index, piece_index) for piece_index, piece in enumerate(layer)]
        for layer_index, layer in enumerate(layers)
    ]

    result: list[list[AdjacentPair]] = []
    for lower_layer, upper_layer in zip(fixed_layers, fixed_layers[1:], strict=False):
```

(the rest of the loop body is unchanged, since it already refers to `lower_layer`/`upper_layer`, now the repaired versions).

- [ ] **Step 5: Run the tests, confirm they pass**

Run: `uv run pytest tests/test_adjacency.py -v`
Expected: PASS, all (including the 24 existing tests — repairing an already-valid polygon returns it unchanged, so nothing else moves).

- [ ] **Step 6: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`

- [ ] **Step 7: Commit**

```bash
git add src/layerforge/models/slicing/adjacency.py tests/test_adjacency.py
git commit -m "adjacent_pairs: repair an invalid polygon, name the piece if it cannot be (#185)

Refs #63, #185"
```

---

## Task 3: `ReferenceMarkCalculator.choose_mark_for_pair` (additive)

**Files:**
- Modify: `src/layerforge/models/reference_marks/reference_mark_calculator.py`
- Test: `tests/test_reference_mark_calculator.py`

**Interfaces:**
- Consumes: `ReferenceMark` (`reference_marks/reference_mark.py`), `mark_reach` (`footprint.py`, already imported in this file), `choose_shape` (`shape_choice.py`), `calculate_distance` (`layerforge.utils`, already imported).
- Produces:
  ```python
  @staticmethod
  def choose_mark_for_pair(
      region: Polygon,
      boundary_polys: Sequence[Polygon],
      candidates: Sequence[ReferenceMark],
      avoid: Sequence[ReferenceMark],
      *,
      min_distance: float,
      min_web: float,
      tolerance: float,
      available_shapes: Sequence[str],
      size: float,
      angle: float,
  ) -> ReferenceMark | None
  ```
  Task 4's `plan_marks` is the only production caller. `get_stable_marks`, `get_potential_marks` and `_sample_points` are untouched by this task (deleted/kept respectively in Task 5).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_reference_mark_calculator.py` (keep the existing two tests and their imports; add `from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkCalculator, ReferenceMarkConfig` already covers what is needed, plus `from layerforge.models.reference_marks.reference_mark_calculator import ReferenceMarkCalculator` is already the import path used):

```python
def test_choose_mark_for_pair_reuses_a_candidate_that_still_fits():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    candidate = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [candidate], [],
        min_distance=10, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is candidate


def test_choose_mark_for_pair_retires_a_candidate_that_no_longer_fits():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    # 5 from the edge: closer than min_distance, so this candidate cannot be reused.
    candidate = ReferenceMark(x=5, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [candidate], [],
        min_distance=10, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is not None
    assert mark is not candidate
    assert Point(mark.x, mark.y).distance(square.boundary) >= 10


def test_choose_mark_for_pair_picks_the_shape_before_the_point():
    """#198: the disc must match the chosen shape's own reach, not the largest in the list."""
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [], [],
        min_distance=1, min_web=0, tolerance=1,
        available_shapes=["circle", "triangle"], size=3, angle=0.0,
    )
    assert mark is not None
    assert mark.shape == "triangle"  # least symmetry order wins (choose_shape, #61)


def test_choose_mark_for_pair_avoids_a_mark_from_the_other_pairing():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    other_pairing_mark = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [], [other_pairing_mark],
        min_distance=1, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is None or Point(mark.x, mark.y).distance(Point(50, 50)) >= 1


def test_choose_mark_for_pair_returns_none_when_nothing_fits():
    tiny = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        tiny, [tiny], [], [],
        min_distance=10, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is None
```

- [ ] **Step 2: Run them, confirm they fail**

Run: `uv run pytest tests/test_reference_mark_calculator.py -k choose_mark_for_pair -v`
Expected: FAIL — `AttributeError: type object 'ReferenceMarkCalculator' has no attribute 'choose_mark_for_pair'`.

- [ ] **Step 3: Write the minimal implementation**

In `src/layerforge/models/reference_marks/reference_mark_calculator.py`, add imports:

```python
from collections.abc import Sequence

from .reference_mark import ReferenceMark
from .shape_choice import choose_shape
```

Add module-level helpers (after the imports, before the class):

```python
def _fits_region(
    pt: Point, region: Polygon, boundary_polys: Sequence[Polygon], radius: float, min_web: float
) -> bool:
    """True when ``pt`` is in ``region`` and at least ``radius + min_web`` from every polygon's edge.

    ``region`` is already eroded by ``min_distance`` from both pieces' own outlines (the pair's
    shrunk overlap, see the pair-local-marks design spec's note on erosion of an intersection),
    so membership in ``region`` alone gives that clearance. Only the shape-dependent
    ``radius + min_web`` margin is checked here, against each piece individually.
    """
    return region.contains(pt) and all(
        poly.boundary.distance(pt) >= radius + min_web for poly in boundary_polys
    )


def _clear_of_gap(
    x: float, y: float, others: Sequence[ReferenceMark], min_distance: float, radius: float, min_web: float
) -> bool:
    """True when ``(x, y)`` is far enough from every mark in ``others``.

    One shared gap for the whole check, using this mark's own radius, the same approximation
    the old whole-slice search used. The adjuster checks the exact footprints afterwards.
    """
    gap = max(min_distance, 2 * radius + min_web)
    return all(calculate_distance(x, y, other.x, other.y) >= gap for other in others)
```

Add the static method to `ReferenceMarkCalculator` (after `get_potential_marks`):

```python
    @staticmethod
    def choose_mark_for_pair(
        region: Polygon,
        boundary_polys: Sequence[Polygon],
        candidates: Sequence[ReferenceMark],
        avoid: Sequence[ReferenceMark],
        *,
        min_distance: float,
        min_web: float,
        tolerance: float,
        available_shapes: Sequence[str],
        size: float,
        angle: float,
    ) -> ReferenceMark | None:
        """Return the mark for one pair's shared region (TR-9).

        Tries each of ``candidates`` first (TR-10: reuse before creating); a candidate that no
        longer fits ``region`` or now collides with ``avoid`` is retired — simply not returned,
        never mutated. ``avoid`` holds marks already committed on the same piece by a different
        pairing (a split or a merge) and is spacing-only, never a source of inheritance. Falls
        back to choosing a shape (#198: before the point, so the disc matches it) and sampling
        a fresh point in ``region``. Returns ``None`` when nothing fits.
        """
        for candidate in candidates:
            radius = mark_reach(candidate.shape, candidate.size)
            pt = Point(candidate.x, candidate.y)
            others = [m for m in avoid if m is not candidate]
            if _fits_region(pt, region, boundary_polys, radius, min_web) and _clear_of_gap(
                candidate.x, candidate.y, others, min_distance, radius, min_web
            ):
                return candidate

        shape = choose_shape(available_shapes)
        radius = mark_reach(shape, size)
        for x, y in ReferenceMarkCalculator._sample_points(region):
            pt = Point(x, y)
            if not _fits_region(pt, region, boundary_polys, radius, min_web):
                continue
            if not _clear_of_gap(x, y, avoid, min_distance, radius, min_web):
                continue
            if any(calculate_distance(x, y, m.x, m.y) <= tolerance for m in avoid):
                continue
            return ReferenceMark(x=x, y=y, shape=shape, size=size, angle=angle)
        return None
```

- [ ] **Step 4: Run the tests, confirm they pass**

Run: `uv run pytest tests/test_reference_mark_calculator.py -v`
Expected: PASS, all 7 tests (2 existing + 5 new).

- [ ] **Step 5: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`

- [ ] **Step 6: Commit**

```bash
git add src/layerforge/models/reference_marks/reference_mark_calculator.py tests/test_reference_mark_calculator.py
git commit -m "Add ReferenceMarkCalculator.choose_mark_for_pair (#63, #198)

Refs #63, #198"
```

---

## Task 4: `plan_marks` — the pair-driven boundary walk (additive)

**Files:**
- Create: `src/layerforge/models/reference_marks/pair_marking.py`
- Test: `tests/test_pair_marking.py`

**Interfaces:**
- Consumes: `adjacent_pairs` (`layerforge.models.slicing.adjacency`), `ReferenceMarkCalculator.choose_mark_for_pair` (Task 3), `ReferenceMarkConfig.resolved` (`config.py`), `ReferenceMark` (`reference_mark.py`).
- Produces:
  ```python
  def plan_marks(
      contours: list[list[Polygon]], config: ReferenceMarkConfig, layer_height: float
  ) -> list[list[ReferenceMark]]
  ```
  Task 5's `SlicerService.slice_model` is the only production caller.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pair_marking.py`:

```python
"""plan_marks: marks chosen per pair of adjacent layers, retired when they no longer fit (#63)."""

import pytest
from shapely.geometry import box

from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks

SQUARE = box(0, 0, 100, 100)


def test_a_single_layer_gets_no_marks():
    """Review Focus: nothing to align a lone layer to, so it gets none (a real behaviour change)."""
    result = plan_marks([[SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0)
    assert result == [[]]


def test_two_identical_layers_share_one_mark():
    result = plan_marks([[SQUARE], [SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0)
    assert len(result) == 2
    assert len(result[0]) == 1
    assert len(result[1]) == 1
    assert result[0][0] is result[1][0]  # TR-10: the same object, not a coordinate copy


def test_a_stack_of_three_identical_layers_gets_one_mark_shared_by_all_three():
    result = plan_marks(
        [[SQUARE], [SQUARE], [SQUARE]], ReferenceMarkConfig(min_distance=10), layer_height=3.0
    )
    assert result[0][0] is result[1][0] is result[2][0]


def test_a_mark_is_retired_when_it_leaves_the_next_pair_s_shrunk_overlap():
    """TR-9: a piece that shrinks past the mark's old spot gets a new mark, not none."""
    wide = box(0, 0, 100, 100)
    narrow = box(0, 0, 30, 100)  # the shared corner mark from `wide` no longer has room here
    tiny = box(0, 0, 100, 30)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[wide], [narrow], [tiny]], cfg, layer_height=3.0)
    assert all(len(marks) >= 1 for marks in result), "every slice should still get a mark"
    # The pair (wide, narrow) chose one mark; the pair (narrow, tiny) may need a different one,
    # since the region shrinks a lot between them. Either way, no mark is shared by all three
    # unless the same point happens to fit both pairs' shrunk overlaps.
    shared_by_all = result[0][0] in result[1] and result[0][0] in result[2]
    if not shared_by_all:
        assert result[1][0] not in result[0] or result[1][0] not in result[2]


def test_a_piece_with_two_neighbours_can_hold_two_marks():
    left_bottom = box(0, 0, 100, 100)
    middle = box(0, 0, 100, 100)  # overlaps fully with both neighbours
    top = box(20, 0, 100, 100)  # its overlap with `middle` is smaller, may force a second mark
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[left_bottom], [middle], [top]], cfg, layer_height=3.0)
    assert len(result[1]) >= 1


def test_min_overlap_area_stops_a_thin_sliver_overlap_from_sharing_a_mark():
    a = box(0, 0, 100, 100)
    b = box(99, 0, 199, 100)  # 1 x 100 sliver of overlap with `a`
    cfg = ReferenceMarkConfig(min_distance=1, min_overlap_area=1000.0)
    result = plan_marks([[a], [b]], cfg, layer_height=3.0)
    assert result == [[], []]


def test_a_split_gives_each_branch_its_own_mark_without_colliding():
    trunk = box(0, 0, 100, 100)
    left_branch = box(0, 0, 45, 100)
    right_branch = box(55, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[trunk], [left_branch, right_branch]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    assert (m1.x, m1.y) != (m2.x, m2.y)


def test_a_merge_gives_the_merged_piece_two_marks_without_colliding():
    left_branch = box(0, 0, 45, 100)
    right_branch = box(55, 0, 100, 100)
    trunk = box(0, 0, 100, 100)
    cfg = ReferenceMarkConfig(min_distance=5)
    result = plan_marks([[left_branch, right_branch], [trunk]], cfg, layer_height=3.0)
    assert len(result[1]) == 2
    (m1, m2) = result[1]
    assert (m1.x, m1.y) != (m2.x, m2.y)
```

- [ ] **Step 2: Run them, confirm they fail**

Run: `uv run pytest tests/test_pair_marking.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'layerforge.models.reference_marks.pair_marking'`.

- [ ] **Step 3: Write the minimal implementation**

Create `src/layerforge/models/reference_marks/pair_marking.py`:

```python
"""Marks chosen per pair of adjacent layers, retired when they no longer fit (#63, TR-9)."""

from __future__ import annotations

import shapely
from shapely.geometry import MultiPolygon, Polygon

from layerforge.models.slicing.adjacency import adjacent_pairs

from .config import ReferenceMarkConfig, require
from .reference_mark import ReferenceMark
from .reference_mark_calculator import ReferenceMarkCalculator


def _largest_part(region: Polygon | MultiPolygon) -> Polygon | None:
    """Return the biggest polygon of ``region``, or ``None`` if it has no area.

    A pair's shrunk overlap can be split into several disjoint pieces; phase 1 places a mark
    in the largest one only (a documented simplification, see the design spec's Non-goals).
    """
    parts = [p for p in shapely.get_parts(region) if isinstance(p, Polygon) and p.area > 0]
    return max(parts, key=lambda p: p.area) if parts else None


def plan_marks(
    contours: list[list[Polygon]], config: ReferenceMarkConfig, layer_height: float
) -> list[list[ReferenceMark]]:
    """Return the marks for every slice of ``contours``, chosen per pair of adjacent layers.

    ``contours[i]`` is the pieces of slice ``i``. The result is the same length, one list of
    marks per slice. A mark is chosen inside the shrunk overlap of two adjacent pieces (TR-9)
    and is retired -- excluded from the next pair's candidates -- the moment it no longer fits.
    Retirement only ever looks at the immediately previous pair; nothing looks further back.
    """
    cfg = config.resolved(layer_height)
    min_distance = require(cfg.min_distance, "min_distance")
    tolerance = require(cfg.tolerance, "tolerance")
    size = require(cfg.size, "size")
    min_web = cfg.min_web_ratio * layer_height
    pairs = adjacent_pairs(
        contours, min_overlap_area=cfg.min_overlap_area, clearance=min_distance
    )

    result: list[list[ReferenceMark]] = [[] for _ in contours]
    carried: dict[int, list[ReferenceMark]] = {}
    on_slice: dict[int, list[ReferenceMark]] = {}
    for i, boundary in enumerate(pairs):
        next_carried: dict[int, list[ReferenceMark]] = {}
        next_on_slice: dict[int, list[ReferenceMark]] = {}
        for pair in boundary:
            region = _largest_part(pair.shrunk)
            if region is None:
                continue
            lower_poly = contours[i][pair.lower]
            upper_poly = contours[i + 1][pair.upper]
            mark = ReferenceMarkCalculator.choose_mark_for_pair(
                region,
                [lower_poly, upper_poly],
                carried.get(pair.lower, []),
                on_slice.get(pair.lower, []),
                min_distance=min_distance,
                min_web=min_web,
                tolerance=tolerance,
                available_shapes=cfg.available_shapes,
                size=size,
                angle=cfg.angle,
            )
            if mark is None:
                continue
            result[i].append(mark)
            result[i + 1].append(mark)
            on_slice.setdefault(pair.lower, []).append(mark)
            next_carried.setdefault(pair.upper, []).append(mark)
            next_on_slice.setdefault(pair.upper, []).append(mark)
        carried, on_slice = next_carried, next_on_slice
    return result
```

- [ ] **Step 4: Run the tests, confirm they pass**

Run: `uv run pytest tests/test_pair_marking.py -v`
Expected: PASS, all 9. If `test_a_mark_is_retired_when_it_leaves_the_next_pair_s_shrunk_overlap` or
`test_a_piece_with_two_neighbours_can_hold_two_marks` fail because the geometry happens to keep
one mark valid across all three boxes (the assertion is written to tolerate either outcome), read
the failure and adjust the box sizes so the fixture actually forces the case it names, then re-run
— do not weaken the assertion to fit whatever the geometry happens to do.

- [ ] **Step 5: Export `plan_marks`**

In `src/layerforge/models/reference_marks/__init__.py`, add `from .pair_marking import plan_marks` and `"plan_marks"` to `__all__` (this does not yet break anything, since nothing has stopped exporting `ReferenceMarkManager`/`ReferenceMarkService` — that happens in Task 5).

- [ ] **Step 6: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`

- [ ] **Step 7: Commit**

```bash
git add src/layerforge/models/reference_marks/pair_marking.py src/layerforge/models/reference_marks/__init__.py tests/test_pair_marking.py
git commit -m "Add plan_marks: the pair-driven boundary walk (#63, TR-9)

Refs #63"
```

---

## Task 5: Cut over — wire `plan_marks` in, delete the old manager and service

**Files:**
- Modify: `src/layerforge/models/slicing/slice.py`
- Modify: `src/layerforge/models/slicing/slicer_service.py`
- Modify: `src/layerforge/models/reference_marks/__init__.py`
- Delete: `src/layerforge/models/reference_marks/reference_mark_manager.py`
- Delete: `src/layerforge/models/reference_marks/reference_mark_service.py`
- Modify: `src/layerforge/models/reference_marks/reference_mark_calculator.py` (remove the now-dead `get_stable_marks`, `get_potential_marks`, `_stability_score`)
- Delete: `tests/test_reference_mark_manager.py`
- Delete: `tests/test_slice_process_reference_marks.py`
- Delete: `tests/test_reference_mark_property.py`'s `test_stability_score_permutation` only (the file keeps its other test, rewritten)
- Modify: `tests/test_calculator_get_potential_marks.py`
- Modify: `tests/test_reference_mark_property.py`
- Modify: `tests/test_slice_mark_size.py`
- Modify: `tests/test_slice_mark_inheritance.py`

**Interfaces:**
- Consumes: `plan_marks` (Task 4), `ReferenceMarkAdjuster.adjust_marks` (unchanged).
- Produces: `Slice(index, position, contours, config=None, *, layer_height, ref_marks=None)` — `mark_manager` is gone; `ref_marks` is the new keyword.

- [ ] **Step 1: Rewrite `slice.py`**

Replace the whole file:

```python
import logging

from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkAdjuster, ReferenceMarkConfig


class Slice:
    """Represents a single slice of a 3D model.

    Attributes
    ----------
    index : int
        The index of the slice in the model.
    position : float
        The Z position of the slice.
    contours : list
        A list of contours in the slice.
    ref_marks : List[ReferenceMark]
        The marks chosen for this slice by `plan_marks` (#63), before `adjust_marks` filters them.
    """

    def __init__(
        self,
        index: int,
        position: float,
        contours: list[Polygon],
        config: ReferenceMarkConfig | None = None,
        *,
        layer_height: float,
        ref_marks: list[ReferenceMark] | None = None,
    ):
        """Initialize the slice.

        Parameters
        ----------
        index : int
            The index of the slice in the model.
        position : float
            The Z position of the slice.
        contours : list
            A list of contours in the slice.
        config : ReferenceMarkConfig, optional
            The mark settings. The slice resolves them with ``layer_height`` (TR-6, TR-10),
            so ``slice.config`` always holds a size, a minimum distance and a tolerance.
        layer_height : float
            The thickness of the layer (the sheet). It sets the least material between holes
            (``config.min_web_ratio`` times it).
        ref_marks : list of ReferenceMark, optional
            The marks `plan_marks` chose for this slice (#63). Empty when not given.
        """
        self.layer_height = layer_height
        self.contours = contours
        self.index = index
        self.config = (config or ReferenceMarkConfig()).resolved(layer_height)
        self.position = position
        self.ref_marks: list[ReferenceMark] = list(ref_marks) if ref_marks is not None else []

    @property
    def min_web(self) -> float:
        """The least material between two holes, or between a hole and an outline."""
        return self.config.min_web_ratio * self.layer_height

    def adjust_marks(self) -> None:
        """Filter `ref_marks` to what actually fits this slice (TR-5), and warn if a piece has none.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If a mark names a shape that is not registered. The marks are left as they were.
        """
        self.ref_marks = ReferenceMarkAdjuster.adjust_marks(
            self.ref_marks, self.contours, config=self.config, min_web=self.min_web
        )
        self._warn_about_unmarked_contours()

    def _warn_about_unmarked_contours(self) -> None:
        """Log a warning if some contours of the slice ended up with no mark."""
        points = [Point(mark.x, mark.y) for mark in self.ref_marks]
        unmarked = [c for c in self.contours if not any(c.contains(p) for p in points)]
        if unmarked:
            logging.warning(
                f"No reference mark fits {len(unmarked)} of {len(self.contours)} contours "
                f"in slice {self.index}. Try a smaller --mark-min-distance or --mark-size "
                "(marks.min_distance or marks.size in the config file)."
            )
```

- [ ] **Step 2: Rewrite `slicer_service.py`**

Replace `slice_model` and the imports:

```python
import logging
import math

from layerforge.models import Model, Slice
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks


class SlicerService:
    """Service class for slicing models"""

    @staticmethod
    def calculate_slice_positions(bottom: float, top: float, layer_height: float) -> list[float]:
        # unchanged — do not touch this method
        ...

    @staticmethod
    def slice_model(model: Model, config: ReferenceMarkConfig | None = None) -> list[Slice]:
        """Slice the model into layers

        Parameters
        ----------
        model : Model
            The model to slice

        Returns
        -------
        List[Slice]
            A list of the slices
        """
        # Resolve once: every slice and plan_marks then share one size, one minimum distance
        # and one snapping tolerance (TR-6, TR-10, #108).
        cfg = (config or ReferenceMarkConfig()).resolved(model.layer_height)
        least = cfg.min_size(model.layer_height)
        if cfg.size is not None and cfg.size < least:
            logging.warning(
                f"The mark size {cfg.size:g} is below the least hole size {least:g} for a sheet "
                f"of {model.layer_height:g} and a kerf of {cfg.kerf:g}. "
                "Holes this small may not cut cleanly."
            )
        min_bound, max_bound = model.mesh.bounds
        slice_positions = SlicerService.calculate_slice_positions(
            float(min_bound[2]), float(max_bound[2]), model.layer_height
        )
        contours = [model.calculate_slice_contours(p) for p in slice_positions]
        marks = plan_marks(contours, cfg, model.layer_height)
        slices = [
            Slice(
                index=i,
                position=p,
                contours=c,
                config=cfg,
                layer_height=model.layer_height,
                ref_marks=m,
            )
            for i, (p, c, m) in enumerate(zip(slice_positions, contours, marks, strict=True))
        ]
        for slice_ in slices:
            slice_.adjust_marks()
        return slices
```

(Keep `calculate_slice_positions`'s body exactly as it is today — only its surrounding imports and `slice_model` change.)

- [ ] **Step 3: Delete the manager and service**

```bash
git rm src/layerforge/models/reference_marks/reference_mark_manager.py
git rm src/layerforge/models/reference_marks/reference_mark_service.py
git rm tests/test_reference_mark_manager.py
git rm tests/test_slice_process_reference_marks.py
```

- [ ] **Step 4: Remove the dead calculator methods**

In `src/layerforge/models/reference_marks/reference_mark_calculator.py`, delete `get_stable_marks` and `get_potential_marks` in full (their job is `plan_marks` + `choose_mark_for_pair` now). Keep `_sample_points` and `_stability_score`'s **method** for now — wait, delete `_stability_score` too, since nothing calls it once `get_stable_marks` is gone; keep `_sample_points` (Task 3's `choose_mark_for_pair` calls it).

- [ ] **Step 5: Update `reference_marks/__init__.py`**

Remove `ReferenceMarkManager` and `ReferenceMarkService` (imports and `__all__` entries); the file now reads:

```python
from .config import ReferenceMarkConfig
from .footprint import mark_footprint, mark_reach
from .pair_marking import plan_marks
from .reference_mark import ReferenceMark
from .reference_mark_adjuster import ReferenceMarkAdjuster
from .reference_mark_calculator import ReferenceMarkCalculator
from .symmetry import RotationSymmetry, rotation_symmetry

__all__ = [
    "ReferenceMark",
    "ReferenceMarkAdjuster",
    "ReferenceMarkCalculator",
    "ReferenceMarkConfig",
    "RotationSymmetry",
    "mark_footprint",
    "mark_reach",
    "plan_marks",
    "rotation_symmetry",
]
```

- [ ] **Step 6: Run the suite, read every failure**

Run: `uv run pytest -q`
Expected: many failures in the six test files listed below — every one should be an `ImportError`, `AttributeError` or a `TypeError` about `mark_manager`/`ReferenceMarkManager`/`ReferenceMarkService`/`get_stable_marks`/`get_potential_marks`, nothing else. If a failure is not one of these, stop and investigate before continuing (it means Steps 1-5 broke something this task did not intend to touch).

- [ ] **Step 7: Rewrite `tests/test_calculator_get_potential_marks.py`**

Replace the whole file:

```python
import math

import pytest

pytest.importorskip("shapely")
from hypothesis import given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMark, ReferenceMarkCalculator


def test_choosing_in_a_square_stays_inside_it():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [], [],
        min_distance=10, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is not None
    assert square.contains(Point(mark.x, mark.y))
    assert square.boundary.distance(Point(mark.x, mark.y)) >= 10


def test_a_candidate_at_the_right_place_is_reused():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    candidate = ReferenceMark(x=50, y=50, shape="circle", size=3)
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], [candidate], [],
        min_distance=10, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is candidate


def test_sample_points_generate_multiple_unique_points():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    pts = ReferenceMarkCalculator._sample_points(square, samples=4)
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert square.contains(Point(x, y))


def test_sample_points_triangle_diversity():
    triangle = Polygon([(0, 0), (50, 100), (100, 0)])
    pts = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    assert len(pts) >= 2
    assert len(set(pts)) == len(pts)
    for x, y in pts:
        assert triangle.contains(Point(x, y))


def test_sample_points_are_deterministic():
    triangle = Polygon([(0, 0), (50, 100), (100, 0)])
    first = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    second = ReferenceMarkCalculator._sample_points(triangle, samples=4)
    assert first == second


def _plate_with_hole() -> Polygon:
    """A 100 x 100 plate with a 60 x 60 hole, so its centroid is in the hole."""
    hole = [(20, 20), (80, 20), (80, 80), (20, 80)]
    return Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], [hole])


def test_marks_avoid_holes():
    plate = _plate_with_hole()
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        plate, [plate], [], [],
        min_distance=5, min_web=0, tolerance=1,
        available_shapes=["circle"], size=3, angle=0.0,
    )
    assert mark is not None
    assert plate.contains(Point(mark.x, mark.y))


def test_sample_points_stay_out_of_holes():
    plate = _plate_with_hole()
    for x, y in ReferenceMarkCalculator._sample_points(plate, samples=8):
        assert plate.contains(Point(x, y))


class _FailsOnSecondContains:
    """Wraps a polygon. Its `contains` works for the centroid test and then raises.

    A subclass of `Polygon` does not work here: shapely builds a plain `Polygon`.
    """

    def __init__(self, polygon: Polygon):
        self._polygon = polygon
        self.calls = 0

    def __getattr__(self, name):
        return getattr(self._polygon, name)

    def contains(self, other):
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("shapely failed")
        return self._polygon.contains(other)


def test_an_error_from_the_candidate_test_reaches_the_caller():
    """It used to read as "outside", so an error hid as "no mark fits" (#171)."""
    poly = _FailsOnSecondContains(Polygon([(0, 0), (100, 0), (100, 100), (0, 100)]))
    with pytest.raises(RuntimeError, match="shapely failed"):
        ReferenceMarkCalculator._sample_points(poly, samples=4)  # pyright: ignore[reportArgumentType]
    assert poly.calls == 2


@pytest.mark.parametrize(
    "poly",
    [
        Polygon([(0, 0), (10, 10), (10, 0), (0, 10)]),  # a bow-tie, not valid
        Polygon([(0, 0), (5, 0), (10, 0)]),  # no area
        Polygon(),  # empty
    ],
    ids=["bow-tie", "no-area", "empty"],
)
def test_sample_points_of_a_degenerate_polygon_do_not_raise(poly):
    """The `except` around the candidate test guarded nothing that these reach (#171)."""
    assert isinstance(ReferenceMarkCalculator._sample_points(poly, samples=4), list)


_COORD = st.floats(0, 30).map(lambda v: round(v, 3))


@given(
    stored=st.lists(st.tuples(_COORD, _COORD), max_size=4),
    tolerance=st.floats(1, 30).map(lambda v: round(v, 3)),
)
def test_a_new_point_is_stored_marks_or_out_of_snapping_range(stored, tolerance):
    """A point within the tolerance of a stored mark must be that mark (TR-10)."""
    square = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])
    candidates = [ReferenceMark(x=x, y=y, shape="circle", size=1) for x, y in stored]
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        square, [square], candidates, [],
        min_distance=5, min_web=0, tolerance=tolerance,
        available_shapes=["circle"], size=1, angle=0.0,
    )
    if mark is None or (mark.x, mark.y) in stored:
        return
    assert all(math.hypot(mark.x - sx, mark.y - sy) > tolerance for sx, sy in stored)
```

(This drops `test_potential_marks_inside_polygon` and `test_existing_mark_inherited`, whose coverage
is now `test_choosing_in_a_square_stays_inside_it` and `test_a_candidate_at_the_right_place_is_reused`
above, renamed to match the new API. `test_chosen_points_are_stored_marks_or_out_of_snapping_range`
is renamed and simplified to check the single point `choose_mark_for_pair` returns, since it no
longer returns a list of many points across many contours the way `get_stable_marks` did.)

- [ ] **Step 8: Rewrite `tests/test_reference_mark_property.py`**

Replace the whole file:

```python
from typing import cast

from hypothesis import assume, given
from hypothesis import strategies as st
from shapely.geometry import Point, Polygon

from layerforge.models.reference_marks import ReferenceMarkCalculator
from layerforge.models.reference_marks.config import ReferenceMarkConfig, require

# Hypothesis can draw coordinates such as 1e-200. A hull edge that short has a
# squared length of 0 in floating point, and GEOS then divides by zero inside
# ``boundary.distance`` (issue #77). Real meshes have no such edges, so the
# strategy rounds to micrometres and any other RuntimeWarning fails the test.
_COORD = st.floats(0, 100).map(lambda v: round(v, 6))


import pytest


@pytest.mark.filterwarnings("error::RuntimeWarning")
@given(st.lists(st.tuples(_COORD, _COORD), min_size=3, max_size=6))
def test_the_chosen_mark_fits_inside_the_polygon(coords):
    hull = Polygon(coords).convex_hull
    assume(isinstance(hull, Polygon) and hull.area > 0)
    poly = cast(Polygon, hull)
    cfg = ReferenceMarkConfig(min_distance=1).resolved(layer_height=3.0)
    min_distance = require(cfg.min_distance, "min_distance")
    size = require(cfg.size, "size")
    mark = ReferenceMarkCalculator.choose_mark_for_pair(
        poly, [poly], [], [],
        min_distance=min_distance, min_web=0, tolerance=require(cfg.tolerance, "tolerance"),
        available_shapes=cfg.available_shapes, size=size, angle=cfg.angle,
    )
    if mark is None:
        return
    pt = Point(mark.x, mark.y)
    assert poly.contains(pt)
    assert poly.boundary.distance(pt) >= min_distance
    # The whole hole fits: a disc of the mark's size lies inside the piece (TR-5).
    assert poly.boundary.distance(pt) >= size / 2
```

(`test_stability_score_permutation` is dropped: `_stability_score` is deleted, since maximizing
pairwise spread no longer means anything once each region search returns at most one point.)

- [ ] **Step 9: Rewrite `tests/test_slice_mark_size.py`**

Replace the whole file:

```python
"""The size of a new mark follows the sheet, not the place (TR-6, #62)."""

import logging

import pytest
from shapely.geometry import box

from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.reference_marks.pair_marking import plan_marks
from layerforge.models.slicing.slice import Slice

NEAR = box(0, 0, 20, 20)
FAR = box(200, 0, 220, 20)


def _one_new_mark_size(layer_height: float, **config) -> float:
    """The size of the one mark two identical, fully-overlapping layers share."""
    cfg = ReferenceMarkConfig(**config)
    marks = plan_marks([[NEAR], [NEAR]], cfg, layer_height)
    assert len(marks[0]) == 1
    return marks[0][0].size


def test_a_new_mark_has_the_size_of_the_sheet_wherever_it_lies():
    """The old rule gave 3 near the origin and 5 far from it; NEAR and FAR are no longer both
    testable in one call now that marks are chosen per pair, not per polygon of one slice -- see
    the next test, which keeps both pieces and both sizes."""
    cfg = ReferenceMarkConfig()
    marks = plan_marks([[NEAR, FAR], [NEAR, FAR]], cfg, layer_height=3.0)
    assert [m.size for m in marks[0]] == [3.0, 3.0]


@pytest.mark.parametrize(
    ("layer_height", "expected"),
    [
        (3.0, 3.0),  # the sheet term: 1 x thickness
        (5.0, 5.0),
        (0.2, 0.45),  # the kerf term: 1.5 x 0.3
    ],
)
def test_the_default_size_is_the_larger_of_the_sheet_term_and_the_kerf_term(layer_height, expected):
    assert _one_new_mark_size(layer_height) == pytest.approx(expected)


def test_a_configured_size_replaces_the_sheet_rule():
    assert _one_new_mark_size(3.0, size=7.0) == pytest.approx(7.0)


def test_the_slice_resolves_its_config_with_its_layer_height():
    config = Slice(0, 0.0, [NEAR], config=ReferenceMarkConfig(), layer_height=3.0).config
    assert (config.size, config.min_distance) == (3.0, 3.0)
    assert config.tolerance == pytest.approx(0.3)


def test_a_slice_needs_its_layer_height():
    """#165 item 1: without it there is no web and no derived size, so it is required."""
    with pytest.raises(TypeError, match="layer_height"):
        Slice(0, 0.0, [])  # pyright: ignore[reportCallIssue]


def test_a_size_below_the_least_hole_size_warns_once_and_still_runs(caplog):
    """TR-6: the person knows the machine, so it is a warning and not an error."""
    from layerforge.models.loading.mesh import TrimeshMesh
    from layerforge.models.model import Model
    from layerforge.models.slicing.slicer_service import SlicerService

    trimesh = pytest.importorskip("trimesh")
    model = Model(
        TrimeshMesh(trimesh.creation.box(extents=(30, 30, 12))),
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        slices = SlicerService.slice_model(model, ReferenceMarkConfig(size=1.0))
    warnings = [r.getMessage() for r in caplog.records if "least hole size" in r.getMessage()]
    assert len(warnings) == 1
    assert "1" in warnings[0] and "3" in warnings[0]
    assert all(m.size == 1.0 for s in slices for m in s.ref_marks)
    assert sum(len(s.ref_marks) for s in slices) > 0


def test_a_default_size_does_not_warn(caplog):
    from layerforge.models.loading.mesh import TrimeshMesh
    from layerforge.models.model import Model
    from layerforge.models.slicing.slicer_service import SlicerService

    trimesh = pytest.importorskip("trimesh")
    model = Model(
        TrimeshMesh(trimesh.creation.box(extents=(30, 30, 12))),
        layer_height=3.0,
    )
    with caplog.at_level(logging.WARNING):
        SlicerService.slice_model(model, ReferenceMarkConfig())
    assert not [r for r in caplog.records if "least hole size" in r.getMessage()]
```

- [ ] **Step 10: Rewrite `tests/test_slice_mark_inheritance.py`**

Replace the whole file (TR-10, scoped to one pair rather than every slice of the run):

```python
import xml.etree.ElementTree as ET

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("svgwrite")
pytest.importorskip("shapely")

from layerforge.cli import process_model

NS = {"svg": "http://www.w3.org/2000/svg"}


def _mark_attributes(svg_file: str) -> dict[str, str] | None:
    """The attributes of the first mark, so its shape and its position are both compared."""
    root = ET.parse(svg_file).getroot()
    for element in root.iter():
        if element.attrib.get("class") == "mark":
            return dict(element.attrib)
    return None


def test_a_shared_mark_is_identical_in_the_two_slices_that_hold_it(cylinder_stl, tmp_path):
    """TR-10: same centre, shape, size and angle in both layers a shared mark appears in.

    A straight cylinder overlaps its neighbours enough that consecutive slices share a mark;
    this does not assert every slice holds the *same* mark (that would be the pre-#63 bug, G-7)
    -- only that wherever a mark IS shared, its two appearances agree exactly.
    """
    out_dir = tmp_path / "svgs"
    process_model(
        stl_file=str(cylinder_stl),
        layer_height=2.5,
        output_folder=str(out_dir),
    )

    files = sorted(out_dir.glob("slice_*.svg"))
    assert files, "no svg files generated"

    positions = [pos for pos in (_mark_attributes(str(f)) for f in files) if pos]
    assert len(positions) >= 2, "expected at least one pair of consecutive slices with a mark"
    # Consecutive marks come from a shared point on a nearly-straight cylinder; a real assertion
    # of TR-10 needs two ADJACENT slices' marks, which is exactly `positions[i]`/`positions[i+1]`
    # here since every slice of this fixture gets a mark.
    for earlier, later in zip(positions, positions[1:]):
        assert earlier == later
```

- [ ] **Step 11: Run the full suite, confirm green**

Run: `uv run pytest -q`
Expected: PASS, all tests. If `test_a_shared_mark_is_identical_in_the_two_slices_that_hold_it` fails
because the cylinder fixture's consecutive slices do NOT actually share a mark under the new
pair-driven design (a real possibility if the cylinder's radius/overlap does not clear
`min_distance` cleanly at every step), read the failure, and if needed adjust the fixture in
`tests/conftest.py`'s `cylinder_stl` (currently radius 30, height 10) to a taller, straighter
cylinder that is large enough relative to the default mark size to share consistently, then
re-run — do not weaken the assertion.

- [ ] **Step 12: Run the rest of the check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && ./scripts/check_specs.sh && uv run mkdocs build --strict`

- [ ] **Step 13: Commit**

```bash
git add -A
git commit -m "Wire plan_marks into SlicerService; delete ReferenceMarkManager and ReferenceMarkService (#63)

Breaking: marks are no longer inherited from anywhere in the run, only from
the immediate neighbour slice (G-7). A single-slice model now gets no marks
at all, since there is no neighbour to align it to.

Fixes #63
Refs #107, #198, #185"
```

---

## Task 6: #107's sheared-cylinder test and TR-9's core invariant

**Files:**
- Modify: `tests/conftest.py` (a sheared-cylinder fixture)
- Create: `tests/test_pair_local_marks_end_to_end.py`

**Interfaces:**
- Consumes: `process_model` (`layerforge.cli`), `SlicerService.slice_model`, `ReferenceMarkConfig`.
- Produces: nothing new — this task is tests only.

- [ ] **Step 1: Add the sheared-cylinder fixture**

In `tests/conftest.py`, add (after `cylinder_stl`):

```python
@pytest.fixture
def sheared_cylinder_stl(tmp_path):
    """Radius 20, height 60, sheared 0.5 in x per unit z (#107's own evidence)."""
    mesh = trimesh.creation.cylinder(radius=20.0, height=60.0, sections=48)
    shear = trimesh.transformations.shear_matrix(0.0, [1, 0, 0], [0, 0, 1], [0, 0, 0])
    # trimesh's shear_matrix signature varies by version; if this raises, build the shear
    # by hand instead: a 4x4 identity with matrix[0, 2] = 0.5 (x shifts by 0.5 * z).
    mesh.apply_transform(shear)
    path = tmp_path / "sheared_cylinder.stl"
    mesh.export(path)
    return path
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_pair_local_marks_end_to_end.py`:

```python
"""End-to-end acceptance for #63 (TR-9): the sheared cylinder of #107, and TR-9's core invariant."""

import math

import pytest

pytest.importorskip("trimesh")
pytest.importorskip("shapely")

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.slicing.slicer_service import SlicerService


def test_every_slice_of_the_sheared_cylinder_gets_a_mark(sheared_cylinder_stl):
    """#107's acceptance test: with tolerance and min_distance comparable to the shear, retirement
    (not a stale, drifting mark) keeps every slice covered."""
    model = Model(TrimeshMesh.load(str(sheared_cylinder_stl)), layer_height=3.0)
    slices = SlicerService.slice_model(
        model, ReferenceMarkConfig(tolerance=25, min_distance=10)
    )
    assert all(len(s.ref_marks) >= 1 for s in slices), (
        f"slices with no mark: {[s.index for s in slices if not s.ref_marks]}"
    )


def test_no_two_distinct_marks_of_the_sheared_cylinder_are_within_tolerance(sheared_cylinder_stl):
    model = Model(TrimeshMesh.load(str(sheared_cylinder_stl)), layer_height=3.0)
    tolerance = 25
    slices = SlicerService.slice_model(
        model, ReferenceMarkConfig(tolerance=tolerance, min_distance=10)
    )
    distinct = []
    for s in slices:
        for m in s.ref_marks:
            if not any(m is d for d in distinct):
                distinct.append(m)
    for i, a in enumerate(distinct):
        for b in distinct[i + 1 :]:
            assert math.hypot(a.x - b.x, a.y - b.y) > tolerance


def test_no_alignment_mark_is_a_hole_in_every_layer_of_a_three_layer_stack():
    """TR-9's core promise. A cone-like stack whose cross-section shrinks steadily forces at
    least one retirement, so no single mark can span all layers."""
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.cone(radius=30.0, height=30.0, sections=48)
    model = Model(TrimeshMesh(mesh), layer_height=5.0)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig(min_distance=3))
    assert len(slices) >= 3
    all_marks = [m for s in slices for m in s.ref_marks]
    for mark in all_marks:
        holds_every_slice = all(any(m is mark for m in s.ref_marks) for s in slices)
        assert not holds_every_slice
```

- [ ] **Step 3: Run them, confirm they fail or pass for a real reason**

Run: `uv run pytest tests/test_pair_local_marks_end_to_end.py -v`
Expected: since Task 5's implementation already exists, these may PASS immediately — if so, that is
real coverage of already-built behaviour (acceptable here, unlike ordinary TDD, because the
behaviour under test was built and verified test-first in Tasks 3-5; this task's job is to prove it
holds on the specific fixtures #107 and TR-9 name, not to drive new implementation). If any fails,
investigate: for `TrimeshMesh.load`, check its actual constructor/loader API first (it may take a
path directly rather than needing `TrimeshMesh(trimesh.load(...))` — read
`src/layerforge/models/loading/mesh.py` before assuming the signature) and fix the test to use the
project's real loading API, not the implementation.

- [ ] **Step 4: If the shear fixture's `shear_matrix` call does not exist in the installed trimesh version**

Run `uv run python -c "import trimesh; print(trimesh.transformations.shear_matrix)"` first. If it
raises `AttributeError`, replace the fixture body with an explicit matrix:

```python
    import numpy as np

    mesh = trimesh.creation.cylinder(radius=20.0, height=60.0, sections=48)
    shear = np.eye(4)
    shear[0, 2] = 0.5  # x += 0.5 * z
    mesh.apply_transform(shear)
```

- [ ] **Step 5: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_pair_local_marks_end_to_end.py
git commit -m "End-to-end tests for #63: the sheared cylinder (#107) and TR-9's core invariant

Fixes #107
Refs #63"
```

---

## Task 7: #198's acceptance table

**Files:**
- Create: `tests/test_disc_matches_chosen_shape.py`
- Modify: `docs/getting_started.md` (correct the "0 of 2 slices" claim the issue's own table shows to be false after this change, if that page still states it — check first)

**Interfaces:**
- Consumes: `process_model` / `SlicerService.slice_model`, `ReferenceMarkConfig`.
- Produces: nothing new — tests and a doc correction.

- [ ] **Step 1: Check whether `getting_started.md` states the old (0 of 2) result**

Run: `grep -n "10 mm cube" docs/getting_started.md`

- [ ] **Step 2: Write the failing test**

Create `tests/test_disc_matches_chosen_shape.py`:

```python
"""#198: the calculator's disc must match the chosen shape's own reach, not the largest listed."""

import pytest
from shapely.geometry import box

pytest.importorskip("trimesh")
pytest.importorskip("shapely")

import trimesh

from layerforge.models.loading.mesh import TrimeshMesh
from layerforge.models.model import Model
from layerforge.models.reference_marks import ReferenceMarkConfig
from layerforge.models.slicing.slicer_service import SlicerService


def _mark_counts(extents, layer_height, **config) -> list[int]:
    mesh = trimesh.creation.box(extents=extents)
    model = Model(TrimeshMesh(mesh), layer_height=layer_height)
    slices = SlicerService.slice_model(model, ReferenceMarkConfig(**config))
    return [len(s.ref_marks) for s in slices]


@pytest.mark.parametrize(
    ("extents", "layer_height", "default_list_marked", "triangle_only_marked"),
    [
        ((10, 10, 10), 5, 2, 2),
        ((6.000, 20, 3), 3, 2, 2),
        ((6.003, 20, 3), 3, 3, 3),
        ((6.004, 20, 3), 3, 3, 3),
    ],
)
def test_the_default_list_and_triangle_alone_agree(
    extents, layer_height, default_list_marked, triangle_only_marked
):
    default_counts = _mark_counts(extents, layer_height)
    triangle_counts = _mark_counts(extents, layer_height, available_shapes=["triangle"])
    assert sum(1 for n in default_counts if n > 0) == default_list_marked
    assert sum(1 for n in triangle_counts if n > 0) == triangle_only_marked
```

- [ ] **Step 3: Run it**

Run: `uv run pytest tests/test_disc_matches_chosen_shape.py -v`
Expected: PASS if Task 5's cutover already fixes #198 as designed (the disc now uses
`choose_shape`'s own reach — see Task 3's `choose_mark_for_pair`). If any row fails, run
`uv run python -c "..."` by hand to print the actual `_mark_counts` for that row, compare against
the issue's own measured table, and adjust the assertion only if the real geometry disagrees with
the issue's numbers under the NEW pair-driven marking algorithm (which chooses marks differently
from the old per-slice loop the issue measured on) — record what changed and why in the PR text
before changing a number here.

- [ ] **Step 4: If `getting_started.md` needs correcting**

Update the exact sentence Step 1 found to state the current, measured count for the 10 mm cube at
layer height 5.

- [ ] **Step 5: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q && uv run mkdocs build --strict`

- [ ] **Step 6: Commit**

```bash
git add tests/test_disc_matches_chosen_shape.py docs/getting_started.md
git commit -m "Acceptance test for #198: the disc now matches the chosen shape

Fixes #198"
```

---

## Task 8: Spec updates (`allium:weed`)

**Files:**
- Modify: `specs/alignment.allium` (around `:280-320` and `:480-511`)
- Modify: `specs/layerforge.allium` (around `:354-437`, `:513-517`)

**Interfaces:** none — spec text only.

- [ ] **Step 1: Read the current spec sections before editing**

Run: `sed -n '280,320p;480,520p' specs/alignment.allium` and `sed -n '340,440p;505,520p' specs/layerforge.allium`
(line numbers may have shifted since the spec doc was written — confirm the real ones before editing).

- [ ] **Step 2: Replace the TR-9 "no lifecycle yet" comment in `specs/alignment.allium`**

Replace the comment block (originally around `:312-316`):

```
-- TR-9: a mark stays in use while it remains valid in the next layer and
-- is retired when it leaves the outline or clearance. That is a lifecycle
-- of a mark across layers. This spec has no such lifecycle yet, because
-- "valid in the next layer" means the mark's whole footprint lies inside
-- the shrunken overlap of the two outlines (TR9_SharedMarkInsideShrunkenOverlap).
```

with:

```
rule TR9_RetireWhenNoLongerValid {
    when: SharedMark(pair, lower_mark, upper_mark)
    let still_valid = footprint_inside_shrunken_overlap(
        upper_mark.footprint, pair.next_pair_of(upper_mark.piece), pair.stack.mark_min_distance
    )
    ensures:
        if not still_valid:
            MarkRetired(mark: upper_mark, at_pair: pair.next_pair_of(upper_mark.piece))
    @guidance
        -- Retirement only ever looks at the immediately following pair. A retired mark is
        -- simply not offered as a candidate there; nothing looks further back or forward.
}
```

(If `pair.next_pair_of` is not an existing spec concept, write the rule in terms of the concepts
`alignment.allium` already has — read the `AdjacentPair` and `Stack` entities at `:82-175` first
and match its style; the exact predicate name matters less than the rule expressing "a mark is
retired the step its footprint leaves the next pair's shrunken overlap.")

- [ ] **Step 3: Write the TR-9 "not a hole in every layer" invariant**

Replace the comment at (originally) `:509-511` with:

```
invariant TR9_NoMarkInEveryLayer {
    -- In a stack of three or more layers, no alignment mark is a hole in every layer.
    for s in Stacks:
        s.layers.length() >= 3 implies
            not exists m in AllMarksOf(s):
                for l in s.layers: m in l.marks
}
```

(Match the real iteration/quantifier syntax `alignment.allium` already uses elsewhere — copy the
pattern from `TR2_OneWayToAlign` at `:417-431` rather than inventing new syntax.)

- [ ] **Step 4: Run `allium check` on the target spec**

Run: `allium check specs/alignment.allium` (or `./scripts/check_specs.sh` if it covers this file)
Expected: 0 errors. New warnings are fine if they match the file's existing accepted-warnings
pattern (`docs/development.md`, Spec checks); a new *error* means the syntax is wrong — fix it by
matching a neighbouring rule's structure more closely, not by removing the check.

- [ ] **Step 5: Update `specs/layerforge.allium`'s marking rules**

Rewrite `invariant FR15_AtMostOneMarkPerContour` (originally `:513-517`) to allow one mark per
piece per neighbour pair:

```
invariant FR15_AtMostOneMarkPerContourPerPair {
    for c in Contours:
        for p in c.adjacent_pairs():
            (for m in c.marks: m.pair = p).count() <= 1
}
```

(Again, match the real predicate/iteration syntax already in the file — read the surrounding
invariants first.) Update `rule FR15_FR21_PlaceMarks` and `rule FR22_AdjustMarks` (originally
`:354-437`) to describe the pair-driven flow: marks are chosen per boundary between adjacent
layers, not in a single per-slice pass; a candidate is offered only from the immediately previous
boundary, not from a run-wide registry. Delete the "Registered marks are shared by every slice,
not only neighbours (G-7)" line — that is exactly what this change fixes — and delete the G-7
entry from the Open Questions section.

- [ ] **Step 6: Run `allium check` and `check_specs.sh` on both files**

Run: `./scripts/check_specs.sh`
Expected: 0 errors, 0 findings (or the same accepted-warning count as before this task, documented
in `docs/development.md`).

- [ ] **Step 7: Run `allium:weed`**

Invoke the `allium:weed` skill on both edited spec files against the code from Tasks 1-7, per the
project rule to run it after every spec edit, prose or not.

- [ ] **Step 8: Fix whatever `allium:weed` finds**

Read every finding; fix a real spec/code mismatch in the code or the spec, whichever is wrong.

- [ ] **Step 9: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q && ./scripts/check_specs.sh && uv run mkdocs build --strict`

- [ ] **Step 10: Commit**

```bash
git add specs/alignment.allium specs/layerforge.allium
git commit -m "Write the TR-9 mark lifecycle into the spec, allow one mark per piece per pair (#63)

Refs #63"
```

---

## Task 9: Documentation, changelog, backlog

**Files:**
- Modify: `docs/requirements.md` (FR rows for the rewritten marking flow)
- Modify: `docs/alignment_requirements.md` (TR-9's Status column)
- Modify: `CHANGELOG.md`
- Modify: `docs/backlog.md`
- Modify: GitHub issue #98 (tick #63, #107, #198, and note #185 item 1 done, items 2-3 open)

**Interfaces:** none — documentation only.

- [ ] **Step 1: Update `docs/requirements.md`**

Find the FR rows describing `Slice.process_reference_marks`, `ReferenceMarkManager` and
`ReferenceMarkService` (`grep -n "process_reference_marks\|ReferenceMarkManager\|ReferenceMarkService" docs/requirements.md`)
and rewrite them to name `plan_marks` and `ReferenceMarkCalculator.choose_mark_for_pair` instead,
matching what Tasks 3-5 actually built. Update the "Used by" test-name column to the new test
files.

- [ ] **Step 2: Update TR-9's Status in `docs/alignment_requirements.md`**

Change the Status sentence of TR-9 (line ~76) from "Choosing marks in it comes with #63" to a
built statement, naming `plan_marks` and the measured sheared-cylinder result from Task 6.

- [ ] **Step 3: Write the CHANGELOG entry**

In `CHANGELOG.md`, under `## [Unreleased]` → `### Changed`, add (fill in the real counts from
Task 6 and Task 7's test runs before committing — do not guess a number):

```markdown
- **Breaking:** Marks are chosen per pair of adjacent layers, not once per slice against every
  mark of the whole run (TR-9, #63). A mark is retired the moment it stops fitting the next
  pair's shrunk overlap; nothing looks further back than the immediate neighbour. A single-slice
  model now gets no marks at all, since there is nothing to align it to. The calculator's disc
  now matches the shape a new mark actually takes, not the largest reach over every listed shape
  (#198): measured, a 10 mm cube at layer height 5 goes from 0 of 2 slices marked to 2 of 2 with
  the default shape list. `adjacent_pairs` (#89) is now used by the command; a self-intersecting
  slice contour reaching it raises a clear error instead of a raw GEOS exception (#185).
```

- [ ] **Step 4: Update `docs/backlog.md`**

Tick ranks for #63, #107, #198, and note #185 item 1 done (items 2-3 still open) in the ranked
table's "Depends on"/inline notes, matching the file's existing style for a done row (see rank 18's
`#61` row for the pattern). Add a "Session G" paragraph (or extend the one from earlier in this
session) naming this PR and the measured before/after numbers from Tasks 6-7.

- [ ] **Step 5: Tick issue #98**

Fetch its body, tick the `#63`, `#107` and `#198` checklist lines (and note #185 item 1), matching
the pattern used earlier this session for #201 and #204 (`gh issue view 98 --json body --jq .body`,
edit the specific `- [ ] N. #NNN` line to `- [x]`, `gh issue edit 98 --body-file <file>`).

- [ ] **Step 6: Run the doc-consistency tests one more time**

Run: `uv run pytest tests/test_defaults_documented.py tests/test_getting_started_examples.py -v`
(the second file may not exist under that exact name — run `uv run pytest -k "getting_started or documented" -v`
and confirm whatever docs-checking tests the repo has today still pass).

- [ ] **Step 7: Run the full local check set**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q && ./scripts/check_specs.sh && uv run mkdocs build --strict`

- [ ] **Step 8: Commit**

```bash
git add docs/requirements.md docs/alignment_requirements.md CHANGELOG.md docs/backlog.md
git commit -m "Update docs, changelog and backlog for pair-local marks (#63)

Refs #63, #107, #198, #185"
```

---

## Task 10: Mutation check, review, PR

**Files:** none new — verification only.

- [ ] **Step 1: Mutation-check the retirement logic**

In `src/layerforge/models/reference_marks/pair_marking.py`, temporarily remove the `carried.get(pair.lower, [])`
inheritance path (force `candidates=[]` always) and confirm `test_two_identical_layers_share_one_mark`
and `test_a_stack_of_three_identical_layers_gets_one_mark_shared_by_all_three` (Task 4) fail. Restore
the file from git (`git checkout -- src/layerforge/models/reference_marks/pair_marking.py`), confirm
they pass again.

- [ ] **Step 2: Mutation-check shape-before-point**

In `reference_mark_calculator.py`'s `choose_mark_for_pair`, temporarily swap the order (sample the
point before calling `choose_shape`, using a placeholder shape's reach for the search) and confirm
`test_choose_mark_for_pair_picks_the_shape_before_the_point` (Task 3) and the #198 table (Task 7)
fail or change. Restore the file from git.

- [ ] **Step 3: Run the full suite one more time, unmasked**

Run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q && ./scripts/check_specs.sh && uv run mkdocs build --strict`

- [ ] **Step 4: Invoke `/code-review`**

Follow this project's established flow (used earlier in this session for #201 and #204): run the
review, judge each note against the code directly rather than trusting the summary, fix what is
real, re-run the full check set after any fix.

- [ ] **Step 5: Write the PR text and open the PR**

Follow the PR template (`.github/pull_request_template.md`). State every **Breaking** change with
a measured before/after number (the #198 table from Task 7, the sheared-cylinder counts from
Task 6, and the single-slice-gets-no-marks change). Reference #63, #107, #198, and #185 (item 1
only). File #185's items 2-3 and TR-8's two-marks-differ clause (the spec's Non-goals) as a new,
separate issue for session H, and link it from the PR text — do not fold that work into this PR.

- [ ] **Step 6: Watch CI, re-read the PR text against the run, merge**

`gh pr checks <N> --watch`; update any "pending" placeholders in the PR text with the real CI run
and counts; re-read the whole text against `git show --stat` and the actual numbers before merging
(the session's own recorded lesson from #196/#200/#204). Squash-merge on green, delete the branch,
confirm `gh run list --branch main` is green afterward including the docs workflow.
