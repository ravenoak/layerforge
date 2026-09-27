# Marks chosen per pair of adjacent layers (#63, TR-9)

Status: draft, awaiting owner review.

## Context

The alignment core is the product's promise: every layer must align to its neighbours in
exactly one way (TR-1 to TR-4), and #92's pre-write check needs a real symmetry test to
enforce it (#60). That check needs shared marks that are genuinely local to a pair of layers.
Today they are not.

`SlicerService.slice_model` (`src/layerforge/models/slicing/slicer_service.py:73-90`) runs one
forward loop with a single `ReferenceMarkManager` for the whole run
(`reference_marks/reference_mark_manager.py`). Slice *i*'s marks are chosen by
`ReferenceMarkCalculator.get_stable_marks` (`reference_marks/reference_mark_calculator.py:80-148`)
against **every** stored mark of the run, not only its neighbour's, and at most one mark is
picked per polygon (`FR15_AtMostOneMarkPerContour`, `specs/layerforge.allium:513`). Nothing ever
removes a mark from the manager's list, so a mark the adjuster drops for one slice
(`reference_mark_adjuster.py`) still blocks nearby points in every later slice
(`reference_mark_calculator.py:140`). This is gap G-7 (#63), and #107 shows it directly: a
sheared cylinder loses its mark from slice 7 on, once tolerance is comparable to the shear.

`adjacent_pairs` (`src/layerforge/models/slicing/adjacency.py:47-90`) already computes, for
each pair of adjacent layers, the overlap of every two touching pieces and that overlap shrunk
by a clearance. No production code calls it yet (#185's note: "not yet used by the command").

This spec is TR-9: marks local to pairs of layers, retired when they no longer fit, chosen
inside each pair's shrunk overlap.

## Goals

- A shared mark is chosen inside the shrunk overlap of the two pieces that share it, and its
  centre is at least `min_distance` from each piece's own outline (TR-2, TR-5, TR-9).
- A mark is retired the moment it stops fitting the next pair's shrunk overlap. Once retired,
  it is gone: nothing looks further back than the immediate neighbour (owner's decision — see
  Non-goals for why the alternative, a trailing window, was not chosen).
- A piece with two neighbours (one below, one above) can hold two marks, one shared with each,
  matching TR-9's "no alignment mark is a hole in every layer of a stack of three or more
  layers".
- `choose_shape` runs before a new mark's point is sampled, so the calculator's disc uses that
  shape's own reach, not the largest reach over every listed shape (#198).
- `adjacent_pairs` gets its first production caller, so its invalid-polygon gap becomes
  reachable and is closed in the same change (#185, item 1 only; item 2, the `STRtree`
  performance idea, and item 3, the zero-`min_overlap_area` decision, stay open).
- The sheared cylinder of #107 becomes an end-to-end test: every slice gets a mark, and no two
  distinct marks in the run lie within tolerance of each other.

## Non-goals (phase 2, a follow-up issue for session H)

- **TR-8's two-marks-differ clause is not enforced.** Two marks freshly chosen on the same
  middle piece (one for the pair below, one for the pair above) can pick the same shape, since
  `choose_shape` has no notion of what else is already on a piece. This is a real gap against
  TR-8, called out here so it is not mistaken for done. `choose_shape` will need a
  `used_on_piece` argument, matching #63's own issue comment.
- **#203** (`rotation_symmetry`'s O(n³) cost on symmetric sets) is not addressed. It matters
  once #92 calls the function once per pair, not before.
- **A trailing retirement window** was considered (letting a piece that briefly loses room pick
  up its old mark again a few slices later) and rejected: it adds state and a setting for a
  case with no evidence it occurs in practice, and the strict neighbour-only rule is the literal
  reading of TR-9 ("local to pairs of layers").
- **#185 items 2 and 3** (an `STRtree` for the all-pairs comparison, and revisiting
  `min_overlap_area`'s default of 0) stay open; this change does not add enough pieces per
  layer to make either urgent.

## Design

### Shrinking by the pair's clearance

`AdjacentPair.shrunk` is `overlap.buffer(-clearance)`. This phase calls `adjacent_pairs` with
`clearance = min_distance` (the run's resolved `ReferenceMarkConfig.min_distance`). Because
erosion of an intersection is a subset of the intersection of the erosions — for any point *p*
whose radius-`min_distance` ball lies inside `shrunk`, that ball also lies inside `overlap`,
hence inside both the lower and the upper piece — every point in `shrunk` is automatically at
least `min_distance` from **both** pieces' own outlines. That covers the first half of the
existing `clear_of_outline` check (`reference_mark_calculator.py:101-103`). The second half,
`edge >= radius + min_web`, depends on the mark's disc radius, which is not known until a shape
is chosen (see below), so it is still checked per candidate point against the **two individual
piece polygons** (`contours[i][pair.lower]` and `contours[i+1][pair.upper]`), not only against
`shrunk`'s own boundary.

`min_overlap_area` is a new setting, `checks.min_overlap_area` (TR-16, matching the Terms table
of `docs/alignment_requirements.md`), defaulting to 0.0, added as a `ChecksSettings` model in
`settings.py` alongside `MarkSettings`, `OutputSettings` and `NumberSettings` — no command-line
option, the same treatment as `marks.min_web_ratio`.

### Replacing the manager with per-boundary state

`ReferenceMarkManager` is removed. `find_mark_in_polygon` is already dead code (no callers); the
rest of its job — "what marks exist to inherit from" — becomes explicitly scoped to one pair
boundary instead of the whole run.

A new module, `reference_marks/pair_marking.py`, holds the planning step:

```python
def plan_marks(
    contours: list[list[Polygon]],  # contours[i] = the pieces of slice i
    config: ReferenceMarkConfig,
) -> list[list[ReferenceMark]]:  # result[i] = the marks belonging to slice i
    ...
```

It is called once from `SlicerService.slice_model`, after every slice's contours are cut and
before any `Slice` is built — the loop that cuts contours and the loop that marks them are no
longer the same pass. `slice_model` passes `result[i]` to `Slice(...)` as its initial
`ref_marks`, and `Slice.adjust_marks()` still runs per slice exactly as today.

Inside `plan_marks`:

1. `pairs = adjacent_pairs(contours, min_overlap_area=cfg.min_overlap_area, clearance=cfg.min_distance)`.
2. Walk boundaries `i = 0 .. len(contours) - 2` in order. Two dicts, both keyed by a piece's
   index in `contours[i]`, carry state forward one step: `carried[p]` is what boundary `i - 1`
   decided for slice `i`'s piece `p` (empty if `p` had no incoming pair, e.g. it is new at this
   slice or `i == 0`), and `already_on_slice[p]` is every mark already committed on piece `p` by
   boundary `i - 1` (the same marks as `carried[p]`, kept under its own name because its role
   here is spacing, not inheritance — see below).
3. For each `AdjacentPair` in `pairs[i]`:
   - `candidates = carried.get(pair.lower, [])`, `avoid = already_on_slice.get(pair.lower, [])`.
   - Run the existing `_sample_points` / `clear_of_outline` / `clear_of` logic
     (`reference_mark_calculator.py:101-147`), scoped to `pair.shrunk` instead of the whole
     piece, checking each point's clearance against **both** `contours[i][pair.lower]` and
     `contours[i + 1][pair.upper]`. `avoid` is folded into the "already taken" spacing set for
     **both** steps: a candidate from `carried` that now sits too close to an `avoid` mark is
     treated as not fitting (retired), the same as one that left the shrunk overlap; a fresh
     point is likewise kept clear of `avoid`. This way the two pairings of one piece never
     silently collide and leave the adjuster's "earlier mark wins" rule to decide by accident.
   - A candidate from `candidates` that no longer fits — whether from leaving `pair.shrunk`, or
     from the `avoid` check above — is retired: it is simply not carried forward. No mark is
     ever mutated or explicitly deleted; "retired" means "excluded from the next `carried`".
   - If nothing in `candidates` fits and the shrunk overlap still needs a mark,
     `choose_shape(cfg.available_shapes)` picks the shape **first**, its `mark_reach` sets the
     disc radius for this one candidate search (fixing #198), and a new point is sampled.
   - **Known limitation, left as phase 1's simplification:** if neither a candidate nor any
     fresh point can satisfy this pair's clearance *and* stay clear of `avoid`, this pairing
     gets no mark on this piece, even though the piece keeps its mark from the other pairing.
     `_warn_about_unmarked_contours` does not catch this (it only asks whether a piece has any
     mark at all). Worth a code comment; not worth a new mechanism until a real model shows it,
     per YAGNI. #92's pre-write check (TR-2: at least one shared mark per pair) is the backstop
     that would actually fail a run in this state.
4. Record the outcome on both sides: append to `result[i]` (as `pair.lower`'s piece) and
   `result[i + 1]` (as `pair.upper`'s piece), and set `next_carried[pair.upper]` and
   `next_already_on_slice[pair.upper]` to `[that mark]`, for boundary `i + 1` to read.
5. A piece with no incoming pair (the first appearance of a piece, or slice 0) simply has
   `candidates = []`; a piece with no outgoing pair (the last slice, or a piece that vanishes)
   contributes nothing to a next boundary.

TR-10 (a shared mark has identical coordinates, shape, size and angle in both layers) holds
because the recorded `ReferenceMark` object — not a copy built from `(x, y)` — is appended to
both `result[i]` and `result[i + 1]`.

### `choose_shape` before the point

`choose_shape(cfg.available_shapes)` (`reference_marks/shape_choice.py:15`) is unchanged in
signature and behaviour; only the call site moves earlier, from after a point is picked
(today's `slicing/slice.py:106`) to before the point is sampled, so `mark_reach` on that one
shape sets the disc radius for that search. An inherited mark keeps its own shape and size
(TR-8, TR-10) and is never re-chosen.

### `SlicerService.slice_model`

```python
contours = [model.calculate_slice_contours(p) for p in slice_positions]
marks = plan_marks(contours, cfg)
slices = [
    Slice(index=i, position=p, contours=c, ref_marks=m, config=cfg, layer_height=model.layer_height)
    for i, (p, c, m) in enumerate(zip(slice_positions, contours, marks))
]
for slice_ in slices:
    slice_.adjust_marks()
```

`Slice.__init__` gains `ref_marks: list[ReferenceMark] = ()` (keyword, defaulting to empty for
existing callers) and drops `mark_manager`. `Slice.process_reference_marks` and
`ReferenceMarkService` are deleted; their job is `plan_marks`. `ReferenceMarkManager` is
deleted.

### Adjuster

`ReferenceMarkAdjuster.adjust_marks` (`reference_mark_adjuster.py:12-57`) needs no change. It
already keeps the earlier mark and drops a later one that overlaps it
(`:47-53`), which now correctly applies to two independently-chosen marks on one piece instead
of assuming there is at most one.

### #185, item 1: invalid polygons in `adjacent_pairs`

`adjacent_pairs` becomes reachable from the command for the first time, so a self-intersecting
slice contour reaching `lower.intersects(upper)` or `lower.intersection(upper)`
(`slicing/adjacency.py:82,84`) can now raise a bare `shapely.errors.GEOSException` with no
context. Fix: validate with `shapely.is_valid`/`make_valid` before the intersection call (the
same pattern `_sample_points` already uses, `reference_mark_calculator.py:52-57`), and on an
unrepairable polygon raise `ValueError` naming the layer index and piece index.

## Error handling

- A tolerance, `min_distance` or `min_overlap_area` that is not finite and non-negative is
  refused by the existing pydantic validators (`ReferenceMarkConfig`, `ChecksSettings`) before
  `plan_marks` runs.
- `choose_shape` on an empty `available_shapes` list cannot occur: `ReferenceMarkConfig`
  already refuses an empty list (`config.py:40-45`).
- An invalid contour polygon is handled per #185 above, with the offending slice and piece
  index in the message.

## Testing

- **Rewrite** `tests/test_slice_mark_inheritance.py`. Today's
  `test_mark_shape_and_position_inherited` asserts one mark is byte-identical across *every*
  slice of a straight cylinder — the opposite of retirement. It becomes: a shared mark is
  identical between the two slices of one pair (TR-10), checked by reading the marks back from
  the written SVGs (closing part of #79's "no test reads marks back from SVG files" gap).
- **New, #107's acceptance test:** the sheared cylinder (radius 20, height 60, sheared 0.5 in x
  per z, layer height 3, `tolerance=25`, `min_distance=10`, from #107's own evidence) gets a
  mark in every slice, and no two distinct marks in the whole run lie within tolerance.
- **New, TR-9's core invariant:** a stack of at least 5 layers whose cross-section changes
  enough to force at least one retirement; assert no single mark (by identity, not by value) is
  a hole in every layer.
- **New, #198's table:** the four rows in the issue (10 mm cube at layer height 5, 6.000 /
  6.003 / 6.004 mm boxes at layer height 3) give the stated mark counts for the default shape
  list and for `--available-shapes triangle` alone, and agree with each other now that the disc
  matches the chosen shape.
- **New, #185 item 1:** a self-intersecting contour reaching `adjacent_pairs` through the
  command raises a `ValueError` naming the slice and piece, not a `GEOSException`.
- **Removed:** tests of `ReferenceMarkManager` (`tests/test_reference_mark_manager.py`) and of
  `Slice.process_reference_marks` / `ReferenceMarkService` as their own units
  (`tests/test_slice_process_reference_marks.py`), replaced by tests of `plan_marks` directly
  and by the end-to-end tests above. `tests/test_calculator_get_potential_marks.py` and
  `tests/test_reference_mark_calculator.py` are adapted to call the pair-scoped calculator
  logic instead of `get_stable_marks`.
- Full local run: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`,
  `./scripts/check_specs.sh`, `uv run mkdocs build --strict`.

## Spec changes

- `specs/alignment.allium`: replace the comment at `:312-316` ("This spec has no such lifecycle
  yet") with a rule for retirement (a mark stays only while it fits the next pair's shrunk
  overlap), and write the TR-9 "no mark is a hole in every layer of a stack of three or more"
  invariant that the comment at `:509-511` currently defers.
- `specs/layerforge.allium`: `FR15_AtMostOneMarkPerContour` (`:513-517`) is rewritten as "at
  most one mark per piece per neighbour pair", since a piece can now hold one mark per side.
  `FR15_FR21_PlaceMarks` (`:354-412`) and `FR22_AdjustMarks` (`:414-437`) are rewritten for the
  pair-driven flow; the "shared by every slice, not only neighbours (G-7)" line at `:410-411`
  is removed, since that is exactly what this change fixes.
- Run `allium:weed` after every spec edit, prose or not (per the backlog's own rule, taken from
  the #149 lesson).

## Documentation and changelog

- `docs/requirements.md`: FR-15 through FR-22 (however they are renumbered by the rewrite) get
  new prose and the "Status" column of TR-9 in `docs/alignment_requirements.md` changes from
  "Choosing marks in it comes with #63" to built.
- `CHANGELOG.md`: **Breaking.** Marks are no longer inherited from anywhere in the run; only
  from the immediate neighbour slice. A model whose marks used to skip a pinch point and
  reappear later now gets a new mark instead. The disc radius for a new mark now matches the
  chosen shape, not the largest listed shape (#198), so some small pieces that got no mark
  before now get one, and vice versa where a bigger, unused shape was in the list. Include the
  #198 table as the measured example.
- `docs/backlog.md`: tick #63, #107, #198, and #185 item 1 in the Session G paragraph and in
  issue #98; leave #185's items 2 and 3 open with a note that they were not touched.

## Rollout

One PR for this phase (the module boundary — `pair_marking.py` replacing the manager and the
per-slice marking calls — does not split cleanly into smaller independently-mergeable pieces
without an awkward intermediate state). Branch, TDD per test group above, mutation-check
`plan_marks`'s retirement and shape-before-point logic, `/code-review`, then the PR text states
the **Breaking** changes with measured before/after numbers (the #198 table, and a run on the
sheared cylinder). Phase 2 (TR-8's two-marks-differ clause) is filed as a new issue referencing
this spec, not folded into this PR.
