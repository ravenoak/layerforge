# The pre-write alignment check and `--allow-unaligned` (#92, TR-12)

Status: draft, awaiting owner review.

## Context

The tool's promise is that layers stack in exactly one way (TR-1 to TR-4). Today nothing checks
it. `Slice.adjust_marks` logs a warning for a piece with no mark, and the command writes the
files and exits 0 whatever the marks are. `rotation_symmetry` (#90, #91) and `adjacent_pairs`
(#89) exist, and `plan_marks` (#63) chooses at most one mark for each pair of overlapping pieces
(`pair_marking.py:73`), but no production code asks "does this pair align one way only?".

This spec is TR-12 for TR-2: after slicing and before any file is written, check every pair of
adjacent pieces. If one fails, write nothing and exit 1. `--allow-unaligned` turns the errors
into warnings.

On 2026-10-09 the owner decided that a number that does not fit stays a warning (TR-3 is
removed from TR-12's list of errors; see Decisions). So this check has one job: TR-2.

## Measured before the design

Defaults (layer height 3, kerf 0.3, number height 5), `SlicerService.slice_model`:

| Model | Slices | Pairs sharing no mark | Number does not fit |
|---|---|---|---|
| cube 10, cube 20, cylinder r30 h30, tube r20/r12 h30 | 4 to 10 | none | none |
| sphere r20 | 14 | none | slice 13 |
| cone r20 h30 | 10 | 7-8 and 8-9 | slices 7, 8, 9 |
| tube r20/r18 h30 (2 mm wall) | 10 | all 9 | all 10 |
| plate 40x40x2 (one layer) | 1 | no pairs | none |

In these models every pair of adjacent slices shares 0 or 1 marks, and every mark is a triangle
(counted per slice pair; the code gives each pair of pieces at most one mark, `pair_marking.py:73`).
A triangle has a direction, so those pairs pass TR-2. The check therefore changes the result for
the cone, the thin tube and models like them. It should also fail a run with
`--available-shapes circle` or `square`, since one circle or square fixes position and not
rotation. That case is expected, not measured; the end-to-end tests below measure it.

## Goals

Each goal says whether the design forces it or only allows it.

| Goal | Forced by | Test |
|---|---|---|
| No file is written when a pair fails and `--allow-unaligned` is not set | The check runs in `_run` before `generate_svgs` and raises `click.ClickException` | End to end: exit 1, output folder holds no `.svg` |
| A pair whose shared marks leave a turn other than none is refused | `rotation_symmetry(...).has_nonidentity`, which is true for a lone circle (unlimited) and a lone square (order 4) | A pair with one circle fails. A pair with one triangle passes |
| A pair with no shared mark is refused | An empty shared set is tested first, so it is never read as "unlimited" | The thin tube and the cone fail with the no-shared-mark reason |
| `--allow-unaligned` writes the files and exits 0, with each failure as a warning | The same failures are logged with `logging.warning` and the check does not raise | End to end: exit 0, all files, one warning per failure |
| Every layer of the stack aligns in one way | **Not forced.** The check is per pair of adjacent layers (TR-2 as written). It cannot see a stack whose pairs each pass but whose pieces float with no neighbour | Out of scope. Stated in Non-goals |

## Non-goals

- **TR-3 and the number clause of TR-5.** A number that does not fit, or that would overprint a
  mark's cut, stays the warning from `SliceSVGDrawer.draw_slice` (#75, #194). Decided by the owner.
- **TR-4, the short baseline.** A pair shares at most one mark today, so a baseline cannot exist.
  TR-4 stays unbuilt until a pair can hold two marks (#213, #215).
- **A piece with no neighbour.** In a model of one layer, or a floating piece that overlaps nothing
  above or below, there is no pair, so TR-2 says nothing. No error, and no warning. The old
  warning "This model has only one layer" is removed with `_warn_about_unmarked_contours`.
- **Changing which marks are chosen.** `plan_marks` is untouched. Forced retirement is #215.
- **A cheaper symmetry test** (#203). A pair passes at most one mark.

## Design

### The check: `check_alignment`

New module `src/layerforge/models/slicing/alignment_check.py`.

```python
@dataclass(frozen=True)
class AlignmentFailure:
    lower_slice: int
    lower_piece: int
    upper_slice: int
    upper_piece: int
    reason: Literal["no_shared_mark", "rotation_not_fixed"]
    detail: str  # the message tail, for the person


def check_alignment(slices: Sequence[Slice]) -> list[AlignmentFailure]: ...
```

For each pair of adjacent slices `(a, b)` and each `AdjacentPair` of
`adjacent_pairs([a.contours, b.contours], min_overlap_area=cfg.min_overlap_area)`:

1. The shared marks are the marks that are in `a.ref_marks` **and** in `b.ref_marks` (the
   same object: the adjuster keeps the objects `plan_marks` made, `reference_mark_adjuster.py:55`)
   and whose centre lies inside both pieces. A mark that the adjuster dropped from either slice
   is therefore not shared (TR-5 is enforced there, as today).
2. No shared mark: `no_shared_mark`.
3. Otherwise `rotation_symmetry(shared, tolerance=...)`. If `has_nonidentity`: `rotation_not_fixed`.
   The tolerance is the run's mark tolerance floored at 1e-6, because `rotation_symmetry`
   refuses 0 and `--mark-tolerance 0` is allowed.

`check_alignment` uses only data on the slices, so it has no new input and no I/O.

### The command

`_run` calls `check_alignment(slices)` after `slice_model` and before `generate_svgs`.

- No failures: nothing changes.
- Failures and not `allow_unaligned`: raise `click.ClickException` whose message is one line
  per failure, then a last line "Nothing was written. Use --allow-unaligned to write the files
  anyway." Exit code 1, standard error.
- Failures and `allow_unaligned`: one `logging.warning` per failure (same line), then write.

A failure line names both pieces and gives advice for its reason:

```
slices 7 and 8 (piece 0 and piece 0): the pieces share no mark. Try a smaller
--mark-min-distance or --mark-size (marks.min_distance or marks.size in the config file).
slices 3 and 4 (piece 0 and piece 0): the marks they share are the same after a turn (a circle
or a square alone cannot fix the rotation). Allow a shape with a direction in --available-shapes.
```

### The setting and the option

`checks.allow_unaligned` (bool, default false) in `ChecksSettings`, and `--allow-unaligned`
(a flag). `process_model` takes `allow_unaligned: bool | None = None`, merged like every
option (CLI, then file, then default). The alignment spec already lists the key
(`alignment.allium:106,282`, TR-16 table).

### What is removed

`Slice._warn_about_unmarked_contours` and the `total_slices` argument of `Slice` that only it
reads. A piece with a neighbour and no mark now fails the check with `no_shared_mark`, with the
same advice as the old warning.

### Documentation and specs

- `docs/alignment_requirements.md`: TR-12 lists TR-2 only; the number stays a TR-11 warning;
  Status says what is built. TR-2, TR-4, TR-8 Status lines and the TR-16 table row for
  `checks.allow_unaligned` change to built.
- `docs/requirements.md`: a new FR row for the check; G-4 reworded (also #212).
- `specs/alignment.allium`: `FailureReason` becomes `{ no_shared_mark | rotation_not_fixed }`;
  `Failure` names the pair; the three TR-12 rules keep their shape; the `alignment_failures`
  guidance lists TR-2 only.
- `specs/layerforge.allium`: a rule for the check, and the `allow_unaligned` setting in its
  `config` block (the defaults test reads it).
- `docs/getting_started.md`, `docs/configuration.md`, README: the option, the exit code, the two
  messages. Every example on an edited page is run.
- `CHANGELOG.md`: **Breaking**: a run that used to write files and warn can now exit 1.

## Decisions taken

- **Owner (2026-10-09):** a number that does not fit is a warning, not an error.
- **Mine, for review:** a failure belongs to a pair and names both pieces, where TR-12 says
  "the slice, the piece".
- **Mine:** a model of one layer, and a piece with no neighbour, pass without a message.
- **Mine:** the symmetry tolerance is the mark tolerance floored at 1e-6.
- **Mine:** the check recomputes `adjacent_pairs` instead of changing what `slice_model` returns.
  It costs one more pass of the overlaps and changes no signature.
- **Mine:** the overprint of a cut by a number that does not fit stays a warning with the number
  warning (the owner's decision covers the number; if you want this one stricter, say so).

## Risks

- **A mesh that ran before can now exit 1.** Measured above: the cone and the thin tube. That is
  the purpose, and it is **Breaking**, with the exit code and flag documented.
- **Float noise makes a pair of pieces with a sliver overlap (#185 item 3).** With
  `checks.min_overlap_area` at 0 a sliver counts as a pair, and then needs a mark. Not changed
  here. The re-run of the probe models after the change says whether it occurs (the two boxes
  that share an edge gave a no-mark warning in one slice before this change).
- **Shared marks found by identity.** If a later change makes the adjuster copy a mark, no pair
  would share one and every run would fail. A test pins that a real two-slice run shares a mark.

## Testing

Tests first, each watched failing for the right reason.

- `test_alignment_check.py` (unit, on hand-built slices): a pair with one triangle passes; one
  circle fails `rotation_not_fixed`; one square fails; no shared mark fails `no_shared_mark`; a
  mark in only one slice is not shared; a single slice passes; `--mark-tolerance 0` does not
  raise.
- End to end through `cli`: the 20 mm cube exits 0 and writes all files; the thin tube exits 1,
  writes nothing, and stderr names the slices and pieces; the same with `--allow-unaligned` exits
  0 and writes every file with one warning per failure; `--available-shapes circle` exits 1.
- Option, config key and `--help` are covered by `test_defaults_documented.py`.
- A mutant check: make `check_alignment` skip the empty-set case and see a test fail.
