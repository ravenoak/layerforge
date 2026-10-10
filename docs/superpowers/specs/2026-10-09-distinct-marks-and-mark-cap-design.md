# Marks that look different, and a cap on how many layers one mark spans (#213 item 1, #215, TR-8, TR-9)

Status: draft 2026-10-09, for the owner's review. Nothing is built.

## Context

Two clauses of the alignment target are not built, and ordinary models break both.

- **TR-8, second sentence.** "Two marks on a piece differ in shape, or use shapes with a
  direction." The wording is wrong: two triangles both have a direction, and a person can still
  lay the next layer shifted so that the wrong two holes line up. `check_alignment` (#92) does
  not see this, because it only asks whether a turn maps the *shared* marks onto themselves.
- **TR-9, last clause.** "In a stack of three or more layers, no alignment mark is a hole in
  every layer." Nothing forces a mark to retire while it still fits, so a straight shape gets
  one mark that goes through the whole stack (#215).

The owner decided on 2026-10-09: TR-8 is built strictly now, and TR-9 gets a soft cap.

## Measured before the design

`SlicerService.slice_model` on `main` at bb31723, layer height 3, the defaults
(`scratchpad/probe_tr8.py`, `probe_merge.py`):

| Model | Slices | Marks | Layers each mark spans |
|---|---|---|---|
| 20 mm cube | 7 | 1 | 7 (every layer) |
| cylinder r30 h30 | 10 | 1 | 10 (every layer) |
| icosphere r20 | 14 | 1 | 14 (every layer) |
| tube r20/r10 h30 | 10 | 1 | 10 (every layer) |
| cone r20 h30 | 10 | 1 | 8 |
| sheared cylinder (#107) | 20 | 2 | 9 and 12; slice 11 holds **two triangles** on one piece |
| two legs into one top (`plan_marks` on boxes, 4 slices) | 4 | 2 | each leg carries a triangle into the top, which then holds **two triangles** |

`check_alignment` passes the last two rows today. Only the triangle and the arrow have a
direction (`symmetry_order` 1). The square has order 4 and the circle none.

## Goals

1. For every pair of overlapping pieces, a hole in the lower piece and a hole in the upper piece
   have the same shape only if they are the same mark (the rule below; as in `check_alignment`,
   "the same mark" is the same object).
2. `plan_marks` builds marks that meet the rule when enough shapes with a direction are listed.
3. `check_alignment` fails a pair that breaks the rule, with a message that says what to do.
4. In a stack of three or more layers no mark is a hole in every layer, unless nothing else
   fits, and then the run warns (soft cap).
5. Both are measured on the models in the table.

## Non-goals

- **More shapes with a direction.** Two exist. Models that need three or more at one piece (a
  stool, a hand) fail the check at the defaults after this change. That follows from the rule
  and has not been run: the first run is a test in the TR-8 PR. #230, ranked high, tracks
  adding shapes (outline, `symmetry_order`, drawing, docs).
- **Pieces that do not overlap.** The engraved number is the slice index, so every piece of a
  slice carries the same number. A piece can be laid on a different piece of the slice below
  that it does not overlap, if that one has a hole of the same shape. The rule covers
  overlapping pieces only. #231 tracks this.
- **TR-4** (baseline of two shared marks, #224) and **#213 item 2 and the spread bias**.
- **A hard cap** (a layer that cannot get a fresh mark fails the check). The owner chose soft.

## Design

### The rule (replaces TR-8's second sentence)

Take two overlapping pieces L (lower) and U (upper) in adjacent layers. For every hole `a` in L
and every hole `b` in U that are not the same mark, `a` and `b` have different shapes.

Size and angle are fixed for a run, so shape decides how a hole looks. The rule assumes that,
that the person matches hole edges, and that a mark is "the same" by centre, shape, size and
angle (TR-10). If a later change lets size or angle vary, the rule must compare them too.

Every mark on a piece is also a hole in a neighbour of that piece, so two different marks on
one piece fall under the rule and differ in shape. Distinct shapes on each piece are not
enough, though: L {A triangle, B arrow} under U {B arrow, C triangle} breaks the rule, since C
is not A and looks like it. The rule is about pieces that meet.

### In `plan_marks` (`models/reference_marks/pair_marking.py`)

Built once from `pairs`: for each piece `(layer, index)` its neighbours (the pieces it overlaps
in the layer below and above), and a list of the **real holes** on it. The avoid-only positions
that `on_slice` carries across a boundary with no mark (`pair_marking.py:69` and `:87`) are not
holes and play no part in shapes.

`taken(pair)` is the set of shapes of every hole on the pair's two pieces and on every
neighbour of either, leaving out the mark under test. Any mark placed later near these pieces
sees this one, so each conflicting pair is checked when the later of its two marks is placed.
That includes siblings at the same boundary (merges and splits), which a set built only from
the two pieces and the slice below would miss.

- **Reuse.** A carried candidate whose shape is in `taken` is retired, like one that no longer
  fits. This is what stops two legs from carrying a triangle each into one top.
- **Fresh mark.** `choose_shape(available, exclude=taken)` returns the best shape with a
  direction that is not excluded (least symmetry order, then the larger outline, then the
  name). It returns `None` when the list holds shapes with a direction and all are excluded.
  When the list holds none (`--available-shapes circle`), it returns the plain choice, as
  today, and the check reports `rotation_not_fixed`.
- **No free shape.** The pair falls back to today's choice (reuse the carried candidate if it
  fits, otherwise the plain choice). The look-alike stays, so the check reports
  `marks_look_alike`, which names the cause. A pair with no mark at all would report
  `no_shared_mark`, which sends the person to the wrong remedy.

### In `check_alignment` (`models/slicing/alignment_check.py`)

New reason `marks_look_alike`: for a pair, some hole of L and some hole of U that are different
marks (not the same object) have the same shape, size and angle. The place is the centre of
the look-alike hole in U (model coordinates, as #223). The check runs after the two existing
reasons, so a pair with no shared mark or a symmetric one keeps its present reason.

Message: `slices 3 and 4 (pieces 0 and 1, at x ..., y ... in the model): two holes on these
layers look the same, so the layers could be laid shifted. N of the listed shapes have a
direction and every one is already used here. Use --allow-unaligned to write the files anyway.`
It must not promise a remedy the defaults cannot give: only two shapes with a direction
exist, and the message says how many are listed.

### The cap (TR-9)

- **Setting.** `marks.max_layers`, an integer of at least 3, default 4 (proposed, to be set by
  a test cut). Config file only, no option, as `marks.min_web_ratio`. Added to
  `ReferenceMarkConfig`, `Settings`, the keys table in `docs/configuration.md`, the `config`
  block of `specs/layerforge.allium` and TR-16. `tests/test_defaults_documented.py` reads all
  three places. Below 3 is refused: a cap of 2 needs three different shapes on every layer.
- **Effective cap.** `min(max_layers, slices - 1)` for a stack of three or more layers, so a
  short stack also has no mark in every layer. A stack of one or two layers has no cap.
- **Count.** `plan_marks` counts the layers each mark is a hole in: 2 when it is made, plus 1
  for each reuse. A candidate at the cap is not offered for reuse. It joins `avoid` (so a fresh
  point keeps the gap and tolerance of TR-10) and its shape is in `taken`.
- **Soft.** If no free shape or no point fits, the capped mark is reused and one warning says
  so: `slices 3 and 4: the mark could not be replaced after 4 layers, so it continues
  (marks.max_layers)`. Nothing that passes the check today starts failing for the cap alone.
- **Sampling.** `_sample_points` tries 4 points. A capped mark usually holds the centroid, so a
  replacement gets 3 random tries. Measure the warnings on the models in the table; raise the
  count only if a piece with room warns.
- **Identity.** A replacement can land on the centre of a mark retired two or more layers
  below, with its shape. No pair of layers holds both, so it is a new mark. The spec says so
  beside TR-10.

### Documentation and specs

- `docs/alignment_requirements.md`: TR-8 (new sentence and status), TR-9 (status: the cap is
  built; the clause holds up to the effective cap), TR-12 (the third reason), TR-16 (the key).
- `docs/requirements.md`: FR-32 (third reason), FR for the cap, G-4 (the through-hole half is
  gone), the keys table. `docs/getting_started.md`: the error list, from a run.
- `specs/alignment.allium`: `TR8_MarksOnAdjacentPiecesLookDifferent` (new invariant),
  `TR9_NoMarkInEveryLayer` becomes the rule for the cap, TR-10 note on identity.
  `specs/layerforge.allium`: the config key and FR-32's guidance. `allium:weed` after each.
- `CHANGELOG.md`: **Breaking**, twice. More holes per run, and models with three or more
  pieces meeting at one piece now fail the check at the defaults.

## Decisions taken

| Decision | Why | Undo |
|---|---|---|
| Strict TR-8 now, not a warning | The owner chose it (2026-10-09). A warning would leave the ambiguity possible, which is the thing the tool promises to prevent. | Make `marks_look_alike` a warning in `check_alignment`. |
| Soft cap, default 4 | The owner chose it. It aims to remove the through-hole on the models in the table without failing a run. To be measured. | Set a large `marks.max_layers`. |
| `max_layers` at least 3 | A cap of 2 needs three different shapes on every layer and cannot be met with two. | Lower the bound. |
| The full neighbourhood in `taken` | A review (a separate model) found that a set built from two pieces and the slice below misses merges and splits. | None needed. |
| Fall back to today's choice when no shape is free | A clear `marks_look_alike` beats a misleading `no_shared_mark`. | None needed. |

## Risks

- **Models that pass today fail.** Any model with three or more pieces meeting at one piece
  (three towers on a base, a hand) needs three shapes with a direction and has two. Measure
  the models in the table plus a stool and a hand, and report which fail. The new-shapes issue
  is the remedy; `--allow-unaligned` writes the files meanwhile.
- **The cap adds holes.** More marks per piece, so more warnings that a number does not fit
  (TR-3). Measure on the table.
- **A replacement can fail to fit** on a small piece. That is the soft path and warns once.
- **`:g` rounding and positions** in messages are unchanged from #223.

## Testing

Written first and watched red for the right reason:

- `choose_shape`: `exclude` skips shapes; every shape with a direction excluded gives `None`;
  a list with none behaves as today.
- `plan_marks`: the sheared cylinder's two-mark piece gets two shapes; two legs into a top get
  a triangle and an arrow; three legs fall back and keep the look-alike; the
  triangle, arrow, triangle alternation cannot occur; avoid-only positions do not use up
  shapes.
- `check_alignment`: hand-built slices with look-alike holes fail with `marks_look_alike`; the
  two-legs output of `main` fails it (red on `main`).
- The cap: cube 20, cylinder r30 h30, icosphere r20 and tube at layer height 3 have no mark that
  spans every layer, and every pair passes. A three-slice stack. A large cap. A piece too
  small for a second mark keeps its mark and warns. `max_layers` 2 is refused.
- Update `_has_a_direction` in `tests/test_alignment_end_to_end.py`: it accepts three corners
  only, and the arrow has seven.
- Mutation checks on `taken`, the reuse retirement and the cap counter.
- Both probes rerun on `main` and on the branch, with the tables in the PR text.

## Delivery

Two PRs, oldest first: TR-8 (the rule, `taken`, `exclude`, the third reason), then the cap
(the setting, the count, the warning). The cap needs TR-8, because a replacement must differ in
shape from the mark it replaces.
