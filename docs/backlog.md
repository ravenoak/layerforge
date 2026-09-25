# LayerForge: prioritized backlog for the next sessions

Written 2026-09-24, after PR #88. Tracking issue: [#98](https://github.com/ravenoak/layerforge/issues/98). Requirements: [Alignment requirements](alignment_requirements.md) (TR-1 to TR-16). Formal target: `specs/alignment.allium`. Today's behavior: [Requirements](requirements.md).

Sizes are my estimates: S under an hour, M one session, L several sessions. Nothing below is started when this page is written. Rank is the order I recommend. Change it if the owner's priorities change.

## How the order was chosen

1. **Cheap, independent fixes first.** They shrink the backlog and carry little risk.
2. **Do the changelog (#97) before any breaking change** (#83, #87 change options and defaults).
3. **Foundations before what uses them.** Settings (#87) feed units, sizes, colours and the number. The shape contract (#84) feeds clearance, shape choice and the symmetry test.
4. **The alignment core comes last**, because it needs footprints, sizes, settings and adjacency to be right.
5. **Ask the owner early** for the two decisions that can change the design: #73 (overlapping shells) and #96 (measured laser numbers).

## Ranked list

| Rank | Issue | Title | Size | Depends on | Why here | Owner input |
|---|---|---|---|---|---|---|
| 1 | #71 | Negative mark options end in a traceback (done, #100) | S | none | Small, finishes the input checks from #67. #87 can reuse the validation. | no |
| 2 | #78 | Remove or use `Model.calculate_height` (done, #101) | S | none | Dead code. Quick. | no |
| 3 | #77 | Investigate intermittent shapely warning (done, #102) | S to M | none | Degenerate polygons may hide a real bug in the mark code. Find it before that code is reworked. | no |
| 4 | #82 + #72 | Mark identity: adopt stored coordinates; nearest wins (done, #103) | S to M | none | Same-mark-at-two-places breaks alignment today (TR-10). Small change with a clear test. | no |
| 5 | #97 | Changelog and version policy (done, #104) | S | none | Must exist before #83 and #87 land. | no |
| 6 | #73 | Investigate overlapping shells (decided: document the limit) | M | none | Changes how contours are built, which #89 relies on. Decide before rank 14. | decided 2026-09-25 |
| 7 | #87 | Settings model and config file (done, #115: the mechanism and the six keys that exist today; each later issue adds its own keys) | M to L | #71 helps | Everything else reads its numbers from here (TR-16). | confirm the file format and key names |
| 8 | #96 | Calibrate the proposed defaults | owner | none (use with #87) | Turns proposed numbers into measured ones. Do it any time after rank 7, or in parallel. | **yes**: a test cut |
| 9 | #74 | Units and physical SVG size | M | #87 | Laser software may import at the wrong size. High value. | no |
| 10 | #84 | Shape contract | M | none | Closed outlines, one size, anchor and angle. Needed by 11, 15, 17. | confirm angle 0 = +x, size = circumscribed diameter (already chosen) |
| 11 | #85 | Clearance uses the whole hole | S to M | #84 | Cheap once outlines exist. | no |
| 12 | #62 + #76 | Mark size and default distance from thickness and kerf | S to M | #87 | Small once settings exist. Makes small models get marks. | no |
| 13 | #75 | Number placement and fit | M | #87, #85 | The number is now load-bearing (TR-3). It also sits on the first hole today. | no |
| 14 | #83 | SVG for the laser | M | #87, #74 | Colour by operation, hairline, number only. Removes `--mark-color`. | confirm colours against the laser software |
| 15 | #89 | Adjacent pieces and overlap | M | none (#73 decided) | Foundation for #63 and #92. | no |
| 16 | #90 | Rotational symmetry test | M | #84 | The core safety check (TR-2). | no |
| 17 | #91 | Brute-force oracle for #90 | S to M | #90 | Guards the safety check. Write it in the same session as #90 if possible. | no |
| 18 | #61 | Shape choice by need | M | #90, #84 | Removes the rotation-blind first circle. | no |
| 19 | #63 | Marks for pairs of layers, with look-ahead | L | #89, #85, #62 | The largest change. The one-pass loop must look at the next layer. | decide bores versus pair-local was settled: pair-local |
| 20 | #92 | Pre-write check and `--allow-unaligned` | M | #89, #90, #75, #85 | The promise of the tool: fail rather than write ambiguous layers. | no |
| 21 | #60 | Close out: end-to-end proof of unique alignment | S | 15 to 20 | Cube, cylinder, tube, L-shaped part: each layer aligns in exactly one way. | no |
| 22 | #79 | Test gaps | M | 15 to 20 | Some items (repair path, many-loop cost) matter more after the rework. | no |
| 23 | #95 | Assembly guide and user docs | M | 7, 9, 14, 20 | The guide needs the final behavior. Each feature PR updates its own docs. | review by the owner |
| 24 | #80 | MkDocs 2 notice | S | none | Low priority. | decide whether to pin |
| 25 | #94 | Cut-through numbers, numbers as outlines | M | #75, #83, #87 | Later. | choose an approach |
| 26 | #93 | Design dowel holes | M | #96, #87 | Later. Design work, no code. | **yes**: process and sizes |
| 27 | #106 | Non-finite option values (`nan`, `inf`) pass the input checks (done, #112) | S | none | Found after #71: `nan` gives a traceback or a silent wrong run. #87 reuses the check. Cheap: do it before rank 7. | no |
| 28 | #110 | Pull request template with the changelog and checks list (done, #113) | S | #97 | The reminders live in this page and the dev notes only. Cheap: do it before rank 7. | no |
| 29 | #109 | Run `allium check` in CI and clear or accept its warnings (done, #114: CI runs `scripts/check_specs.sh`; the three warnings on `layerforge.allium` are accepted) | S to M | none | The check is manual today, and its exit code is 1 on warnings. Investigate the CI install first. | no |
| 30 | #108 | Harden the mark snapping path | S | #103 | One tolerance source, a containment check in the adjuster. Fits with rank 11 and 12. | no |
| 31 | #107 | Stored marks never retire (acceptance for #63) | part of #63 | #63 | Not separate work: add its sheared-cylinder test to rank 19 and 21. | no |

Ranks 27 to 31 were found while doing ranks 1 to 6 and appended, so the numbers in the Depends columns stay valid. Ranks 27 to 29 are small and independent, so do them first (see session A2 below).

Issue #98 holds the same list as a checklist. Tick it as items merge, and keep the order in both places the same.

## Suggested session bundles

| Session | Items | Note |
|---|---|---|
| A | #71, #78, #77, #82 + #72, #97 | Done 2026-09-25 as PRs #100 to #104. #73 was decided: document the limit. |
| A2 | #106, #110, #109 | Done 2026-09-25 as PRs #112 to #114. |
| B | #87 | Done 2026-09-25 as PR #115, narrow: the mechanism plus keys for today's settings. The example file for #96 is not added; `docs/configuration.md` has an example. |
| C | #74, #84 | Units first, then the shape contract. |
| D | #85, #62 + #76, #75, #108 | Uses #84 and #87. |
| E | #83, #89 | Laser output, then adjacency. |
| F | #90, #91, #61 | Symmetry test and its oracle together, then shape choice. |
| G | #63 | Alone. It is the largest change. Add the sheared-cylinder test from #107. |
| H | #92, #60, #79, #95 | The check, the proof, tests, docs. |

## Rules for every session

Start:
1. Read the project memory index (`MEMORY.md`), then the linked files.
2. `git checkout main && git pull --ff-only`, then confirm the tree is clean and that no other branches or worktrees are left.
3. Read the issue and its TR rows in [Alignment requirements](alignment_requirements.md). Follow the acceptance list in the issue.
4. Use plan mode before coding. Use the brainstorming, test-driven-development and verification-before-completion skills by name.

While working:
- One branch and one PR per issue. Commit message ends with `Fixes #N`, or `Refs #N` when part of the issue stays open.
- Write the failing test first, and watch it fail for the right reason. A property test that passes on the first run proves nothing: shrink the input space until it fails on the bug. Run the checks without pipes: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`.
- In the same PR: update the FR row in `docs/requirements.md`, remove the fixed Known gaps row, and update `specs/layerforge.allium`. Add or update the matching target row if the target changed. Run `./scripts/check_specs.sh` and `uv run mkdocs build --strict`.
- Run `allium:weed` after spec edits, and `/code-review` before opening the PR.
- Ask before pushing, merging or editing issues unless the owner has said to.
- State in the docs, the changelog and the PR text only what was measured. "Unchanged at the defaults" was true for one model and false in general (session A, #103).
- `allium check` exits 1 on warnings, even on `main`. `scripts/check_specs.sh` fails only on an `error` diagnostic or a finding, and CI runs it. The accepted warnings are listed in [Development](development.md) (#109).
- Merge with squash, oldest PR first. After `gh pr merge`, `mergeable` reads `UNKNOWN` for about 15 s: run `git fetch` and look again in a separate command. Two PRs that each delete one of two adjacent Known-gaps rows conflict. Drop both rows and continue the rebase.

Finish:
- Merge on green CI, delete the branch (local and remote), confirm a clean tree.
- Update the memory file `project-layerforge-backlog.md`. Add a memory only for facts a future session cannot get from the repo.

## Known traps

See memory `layerforge-tooling-gotchas` and [Development](development.md) (Working Notes): trimesh `section` argument order, `to_2D` re-centring, no triangulation engine, BSD `sed -i`, `qlmanage` hangs (use `rsvg-convert`), and `| tail` hiding failed checks. In shell heredocs, do not put backslashes before backticks: build issue and PR bodies in Python or from a file.

## Status

Sessions A, A2 and B are done (2026-09-25). A: ranks 1 to 5 merged as #100 to #104, and rank 6 (#73) was decided as a documented limit (#105). A2: #106, #110 and #109 merged as #112 to #114. B: #87 merged as #115, with the mechanism and the keys that exist today (`layer_height`, `marks.size`, `marks.tolerance`, `marks.min_distance`, `marks.shapes`, `marks.angle`). The next work is session C (#74, #84). Each later issue adds its own config keys and its own row in TR-16; the default `marks.tolerance` of 0.1 x mark size comes with #62.

## Open decisions and owner inputs

| Decision | Blocks | Needed by |
|---|---|---|
| Laser and material numbers (#96): kerf, smallest clean hole, number height, hairline behavior | Final defaults in #87, #62, #75 | Before #83 is merged |
| Colours and stroke conventions of the laser software (#83) | #83 | Session E |
| Dowel hole design (#93) | later work | Later |
| Config key names in TR-16 | Later keys | Each issue that adds a key. The six built in #87 follow TR-16 as written, so the owner may still rename them. |

## What is settled

Overlapping shells in one mesh are a documented limit (#73, decided 2026-09-25): the even-odd rule stays, users merge bodies before export, and a later opt-in `manifold3d` union is possible. Marks are holes. Every layer aligns to the one below and the one above in exactly one way. The number fixes the flip. Mark shape fixes rotation. Units default to mm. Failing to align is an error before writing, and `--allow-unaligned` overrides it. Angle 0 points along +x, counter-clockwise. Mark size is the diameter of the smallest circle that holds the outline. Marks are chosen per pair of adjacent layers. Every laser, material and judgment number is a setting. Dowel holes are a later feature.
