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
| 8 | #96 | Calibrate the proposed defaults | owner | none (use with #87) | Turns proposed numbers into measured ones. Do it any time after rank 7, or in parallel. The generated sheet of #141 does the cutting part for any machine. | **yes**: cut the sheet of #141 and record the numbers |
| 9 | #74 | Units and physical SVG size (done, #147: `--units`, the `units` key, `width` and `height` with the unit) | M | #87 | Laser software may import at the wrong size. High value. | no |
| 10 | #84 | Shape contract (done, #156: `outline()` and `symmetry_order` on each shape; the square and triangle are smaller at the same size) | M | none | Closed outlines, one size, anchor and angle. Needed by 11, 15, 17. | confirm angle 0 = +x, size = circumscribed diameter (already chosen) |
| 11 | #85 | Clearance uses the whole hole (done, #159: the footprint, the web `marks.min_web_ratio`, and item 2 of #108; the number clause stays with #75) | S to M | #84 | Cheap once outlines exist. | no |
| 12 | #62 + #76 | Mark size and default distance from thickness and kerf (done, #170: size = the larger of 1 x layer height and 1.5 x kerf, `--kerf`, the defaults of layer height and kerf follow `--units`) | S to M | #87 | Small once settings exist. Makes small models get marks. | no |
| 13 | #75 | Number placement and fit (moved to session E with #83, which shares the fill colour and `font-size` of TR-14) | M | #87, #85 | The number is now load-bearing (TR-3). It also sits on the first hole today. | no |
| 14 | #83 | SVG for the laser | M | #87, #74 | Colour groups, hairline, number only. Removes `--mark-color`. Colour does not set the operation in every program (TR-17). | no: red cut and black engrave stay as default groups. The probe of #141 shows what your software does. |
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
| 26 | #93 | Design dowel holes | M | #96, #87 | Later. Design work, no code. A machine-neutral design is proposed in TR-15. | **yes**: review TR-15 (position and count are open) |
| 27 | #106 | Non-finite option values (`nan`, `inf`) pass the input checks (done, #112) | S | none | Found after #71: `nan` gives a traceback or a silent wrong run. #87 reuses the check. Cheap: do it before rank 7. | no |
| 28 | #110 | Pull request template with the changelog and checks list (done, #113) | S | #97 | The reminders live in this page and the dev notes only. Cheap: do it before rank 7. | no |
| 29 | #109 | Run `allium check` in CI and clear or accept its warnings (done, #114: CI runs `scripts/check_specs.sh`; the three warnings on `layerforge.allium` are accepted) | S to M | none | The check is manual today, and its exit code is 1 on warnings. Investigate the CI install first. | no |
| 30 | #108 | Harden the mark snapping path (done, #159 and #169: one tolerance from the slice's config, and `taken` built once per contour) | S | #103 | One tolerance source, a containment check in the adjuster. Fits with rank 11 and 12. | no |
| 31 | #107 | Stored marks never retire (acceptance for #63) | part of #63 | #63 | Not separate work: add its sheared-cylinder test to rank 19 and 21. | no |
| 32 | #120 | The test suite reads a `layerforge.toml` in the working directory (done, #129) | S | none | Found after #87. A plausible file fails 2 to 46 tests. Do it before session C adds more keys. | no |
| 33 | #117 | G-25: The scale and target conflict check tests truthiness (done, #130) | S | none | `0`, `-1` and `nan` give different exit codes for the same pair. | decided in session A3: the conflict comes before a bad value, and a bad config file comes before the conflict (#131) |
| 34 | #118 | G-26: A config file is read without a message (done, #132: the file name only) | S | none | A stray `layerforge.toml` changes a run silently. | no |
| 35 | #119 | G-27: A bad config file is reported after the STL prompt (done, #131: an eager `--config` callback) | S | none | Investigate an eager `--config` first. | no |
| 36 | #121 | Harden settings.py: the second-stage error lookup (done, #133) | S | none | Latent `KeyError`. Do it before #62 adds the first key without an option. | no |
| 37 | #125 | Defaults are written by hand in six places (done, #158: the help text follows `Settings()`, and one test compares the keys table, the spec block and the help text) | S to M | none | Do it before #62 and #76 change the defaults. | no |
| 38 | #122 | Test scripts/check_specs.sh and find out what `findings` hold | S | #114 | The CI gate is proven only by hand. | no |
| 39 | #123 | Verify the allium install in CI; make the bump routine (done, #127: upstream signs nothing, so the pin is checked against the tarball its release run built; the bump steps are in `docs/development.md`) | S | #114 | The pinned hash was trust-on-first-use. There are no attestations. | optional: tell upstream about the empty `sha256` for x86_64 in its Homebrew formula |
| 40 | #124 | The spec does not model most option checks | S to M | none | Weed found spec faults in #115 only because it was run by hand. | no |
| 41 | #135 | G-28: Bad option values and the scale and target conflict are reported after the STL prompt (done, #146: `--stl-file` has no `prompt=`, `cli` asks after the checks) | S to M | none | #119 fixed only the config file. Do it before session C, which adds `--units` and more options that need the same early checks. Investigate option callbacks against moving the prompt. | no |
| 42 | #136 | Tidy the eager `--config` callback: a double read and three small inconsistencies (done, #146: `--config` is not eager, the file is read once, `--help` wins over a bad file) | S | none | Found by `/code-review` on #131 and by running the command. Low priority. | decided 2026-09-25 by best practice: `--help` wins over everything, as [clig.dev](https://clig.dev) says ("you should be able to add `-h` to the end of anything and it should show help") |
| 43 | #137 | `getting_started.md` lists error messages the command does not print (done, #148) | S | none | Two lines are wrong and the two most common messages are missing. Can be folded into #95. | no |
| 44 | #138 | The PR template has no way to say a box does not apply (done, #148) | S | #110 | One line. | no |
| 45 | #141 | Write a calibration sheet SVG so any machine can measure its own kerf, hole, fit and number sizes | M | #74, #83 | Machine-neutral way to get the numbers of #96 and the dowel fit of #93. | cut it on your machine |
| 46 | #142 | Implement dowel holes (TR-15), after the design in #93 is accepted | M | #93, #84, #83, #74, #89, #141 | Later. Do not start before #93 is accepted. | no |
| 47 | #144 | G-29: An output folder that is a file ends in a traceback after slicing (done, #146) | S | none | Found by probing the class of #135. | no |
| 48 | #145 | G-30: A bad `--mark-color` ends in a traceback while the SVG is drawn | S | #83 | #83 removes `--mark-color` and adds `--cut-color` and `--engrave-color`. Build the colour check there, for all three. | no |
| 49 | #149 | G-31: An output folder that cannot be written ends in a traceback, and an empty one points at the root (done, #160: a temporary file in the nearest folder that exists, no folder made early; a too-long name too) | S | none | Same class as #144. Can go any time. | no |
| 50 | #151 | `getting_started.md` shows five files for the 20 mm cube, the command writes four (done, the PR of this row) | S | none | Found in the second retrospective pass: the example was wrong since #70. | no |
| 51 | #152 | Documented examples are not checked against a run | S to M | none | Same cause as #137 and #151. Fits session A4 or #95. | no |
| 52 | #153 | Tidy after #146: repeated check sequence, unused `load_settings`, a test that patches a private name (done, #161: two accepted and written down, one test changed) | S | none | Do it with the next change to `cli.py`. | no |
| 53 | #154 | SVG size edge cases: no viewBox leaves 100%, a float can print in exponent notation, and a mark at x = 0 prints `cx="-0.0"` (measured, older than #170) | S | #74 (done) | Investigation. Do it before #83 and #141, which draw on the same root. | no |
| 54 | #157 | Circle outline is a polygon just outside the drawn circle: decide what the footprint check uses (done, #167: keep the polygon, the calculator's radius is the largest reach, `mark_reach`) | S | #84, #85 (done) | Found in the review of #85. The calculator's disc and the circle outline differ by 0.12%. Decide before #75 and #90 use the outline. | decide 0.12% or exact |
| 55 | #162 | An unregistered shape name makes the adjuster skip every check for the whole slice (done, #168: the error reaches the caller) | S | #85 (done) | Found by probing the class of #85. Not reachable from the command. Can go any time. | no |
| 56 | #164 | The spec `config` block has no default for the mark angle, so the defaults test cannot see it (done, #170) | S | #125 (done) | Found in the second retrospective of session C2. The test compares 8 settings with the table and 6 with the spec. Do it with #62. | no |
| 57 | #165 | Tidy after #85: a Slice without `layer_height` has no web, and tests call a private size method (done, #167 and #170) | S | #85 (done) | Found in the same pass. Do it with the next change to `slice.py` (#62 or #75). | no |
| 58 | #171 | Two broad excepts hide errors: the calculator's candidate test and the label position | S | none | Same class as #162. The label one goes with #75. | no |
| 59 | #172 | Remove the unused `Model.origin` and `Slice.origin` | S | none | Unused since #170. Check #75 first. | no |
| 60 | #173 | Tidy after #62: the calculator's config fallback and where the small-size warning lives | S | none | Found by `/code-review` of #170. | no |
| 61 | #175 | The small-mark-size warning names an internal requirement ID (TR-6) | S | none | Found by the second retrospective of session D. I wrote the message. | no |

Ranks 27 to 31 were found while doing ranks 1 to 6, and ranks 32 to 40 while doing ranks 7 and 27 to 29. They are appended, so the numbers in the Depends columns stay valid. Ranks 27 to 29 and 32 to 36 are done (session A3 below). Rank 37 goes before #62 (session D). Ranks 41 to 44 were found in the retrospective of session A3 and are done (session A5, PRs #146 and #148). Ranks 47 to 49 were found by probing the class of #135 in the session of 2026-09-25; rank 47 is done. Ranks 50 to 53 were found by a second retrospective pass the same day; rank 50 is done. Ranks 54 and 55 were found in session C2 (below), and ranks 56 and 57 by its second retrospective pass. Ranks 10, 11, 37, 49 and 52 are done (session C2). Ranks 12, 30 and 54 to 57 are done (session D). Ranks 58 to 60 were found in session D and rank 61 by its second retrospective pass; they are open. Ranks 38 to 40 are hygiene and can go any time (session A4).

Issue #98 holds the same list as a checklist. Tick it as items merge, and keep the order in both places the same.

## Suggested session bundles

| Session | Items | Note |
|---|---|---|
| A | #71, #78, #77, #82 + #72, #97 | Done 2026-09-25 as PRs #100 to #104. #73 was decided: document the limit. |
| A2 | #106, #110, #109 | Done 2026-09-25 as PRs #112 to #114. |
| A3 | #120, #117, #118, #119, #121 | Done 2026-09-25 as PRs #129 to #133. #121 moved here from D because #119 reshaped `load_settings`. |
| A4 | #122, #123 (done), #124, #152 | Spec and CI hygiene. No product code. Run `allium:weed` with #124. #152 (check the docs examples) fits here. Can go between any two sessions. |
| A5 | #135, #136, #137, #138 | Done 2026-09-25 as PRs #146 (#135, #136 and #144 together, because removing the eager `--config` callback fixes both) and #148 (#137, #138). |
| B | #87 | Done 2026-09-25 as PR #115, narrow: the mechanism plus keys for today's settings. The example file for #96 is not added; `docs/configuration.md` has an example. |
| C | #74, #84 | Units first, then the shape contract. Done 2026-09-25: #74 as PR #147, #84 as PR #156. |
| D | #157, #162, #108 items 1 and 3, #62 + #76, #164, #165 | Done 2026-09-25 as PRs #167 to #170, one issue group each, oldest first. #75 moved to E: it needs three keys, an option, unit conversion and a drawer rewrite, and it overlaps TR-14 (#83). |
| C2 | #84, #125, #85, #149, #153 | Done 2026-09-25 as PRs #156, #158, #159, #160 and #161, in that order. Chosen because the alignment core had not started after 29 merged PRs (#100 to #155, counted with `gh pr list`) of input checks, config, CI, units and docs: #84 is the root that blocks #85, #90, #61, #141 and #142. #125 went before #85 because #85 adds a default. |
| E | #83, #75, #89, #141 | Laser output, then adjacency. The calibration sheet (#141) follows #83 and #74. |
| F | #90, #91, #61 | Symmetry test and its oracle together, then shape choice. |
| G | #63 | Alone. It is the largest change. Add the sheared-cylinder test from #107. |
| H | #92, #60, #79, #95 | The check, the proof, tests, docs. |

## Rules for every session

Start:
1. Read the project memory index (`MEMORY.md`), then every linked file, including the gotchas. In session B I read four and repeated a zsh slip that the gotchas file lists.
2. `git checkout main && git pull --ff-only`, then confirm the tree is clean and that no other branches or worktrees are left.
3. Read the issue and its TR rows in [Alignment requirements](alignment_requirements.md). Follow the acceptance list in the issue.
4. Use plan mode before coding. Use the brainstorming, test-driven-development and verification-before-completion skills by name.

While working:
- When a fix names one member of a class of inputs, probe the rest of the class before you close the issue. #119 moved a bad config file before the `--stl-file` prompt and left bad option values and the option conflict after it (G-28, #135). Test each member of the class, as with `nan` and `inf` in #106.
- Before a comment, a spec sentence or a doc line says "every" or "before any", run the case. "Before every other check" was false in #131 (an unknown option is refused first), and a code comment in #133 claimed a case that no test reached.
- When a check moves or a step is split, compare what the command prints and on which stream, not only the exit code. In #146 the `Using settings from <file>` line stopped printing on a run that failed a later check. My tests covered the success run, and `/code-review` found the loss. Now a test covers it.
- When a change makes a call raise inside a loop, read the `except` around the loop. #85 made the adjuster build each footprint with `ShapeFactory.get_shape`, which raises for an unknown name, and a `except ValueError` in `Slice.adjust_marks` (from #53) swallowed it and skipped every check (#162).
- When you break code to prove a test, restore it from a copy, not with `git checkout -- <file>` on a file that holds uncommitted work. In session C2 that removed one of my own edits (I saw it in `git diff --stat` and redid it).
- When a fix covers an option that names a resource (a file, a folder), probe the whole class: missing, a directory where a file is wanted, a file where a directory is wanted, inside a file, a dangling symlink, not writable, empty text. #144 covered a file and a path inside one. A dangling symlink came from the review, and #149 holds the unwritable and empty cases.
- When you edit a docs page, run every command and example on that page and copy the numbers from the run. #148 edited the error list of `getting_started.md` and left a cube example above it that had been wrong since #70 (#151).
- After a PR text says "N new tests", "N notes" or "N callers", count them with the tool (`--collect-only`, `git show --stat`, `grep -c`). Four PR texts in three sessions held a wrong count (#115, #146 twice, #150).
- One branch and one PR per issue. Commit message ends with `Fixes #N`, or `Refs #N` when part of the issue stays open.
- Write the failing test first, and watch it fail for the right reason. A property test that passes on the first run proves nothing: shrink the input space until it fails on the bug. Run the checks without pipes: `uv run ruff format && uv run ruff check && uv run pyright && uv run pytest -q`.
- In the same PR: update the FR row in `docs/requirements.md`, remove the fixed Known gaps row, and update `specs/layerforge.allium`. Add or update the matching target row if the target changed. Run `./scripts/check_specs.sh` and `uv run mkdocs build --strict`.
- Run `allium:weed` after spec edits, and `/code-review` before opening the PR.
- Run `allium:weed` for a prose-only spec edit too. It was skipped for #149 because the edit was a guarantee sentence, and the late pass found the FR-5 message wording wrong (`<name>` is the whole folder text, and other lookup errors use it).
- A retrospective that says "no wrong claim found" must list what it ran. The first pass on session C2 re-read five PR texts and missed "the disc holds every outline", which a two-line measure (`max(hypot)` over `exterior.coords`, 5.00603 for the circle) disproves. Test every "every", "any" and "never" in a PR text or a docstring with one number.
- Before `gh pr merge`, re-read the PR text against the issues it names and against the run. Session D's #170 text said "the rest of #165 stays open" when item 3 had merged in #167, and said a follow-up was "filed" before I filed it. I edited, marked ready and merged in one command, so the re-read came after. Look at the issue itself for every `Refs`. Write "filed" only after the issue number exists.
- A PR that bundles issues says why in its text. #170 held four issues in 34 files, against the one-PR-per-issue rule, and the text was silent. Split it, or give the reason (here: one change to the defaults that would leave `main` half-migrated).
- A review note is a lead. Read the code behind each one and write what you saw, as for any agent report. The reviewer of #170 did not run the tests or read callers outside `src`. I judged four notes "documented" and one "real" from the note text and confirmed the real one (`config or ReferenceMarkConfig()` before, `(config or layer.config).resolved(...)` after) only in the retrospective.
- Run the case the docs promise before the merge, not in the retrospective. `docs/configuration.md` says `--kerf 0` suits a CNC router. I ran it only after #170 merged (it works: size 3 at layer height 3, size 0.2 at layer height 0.2).
- Read your new user-facing message as the person who runs the command. `grep -rnE "TR-|FR-|G-[0-9]"` over the strings in `src`. The warning of #170 names `TR-6` (#175).
- In zsh, define `lf() { uv run --project <repo> layerforge "$@"; }` before the first probe. The `L=...; $L` slip happened a fifth time in session D, after it was in the gotchas file.
- After a merge, check the run on `main` (`gh run list --branch main`) and the docs workflow in it. It runs on push only, so the PR checks do not cover it.
- Ask before pushing, merging or editing issues unless the owner has said to. The owner allowed push, PR and squash-merge on green for the session of 2026-09-25 only.
- Write the PR text after the checks and CI have run, and copy numbers from their output. In session A2 and B three PR texts had a wrong or stale claim (a template that did not show, a CI job "not run yet" that had passed by merge, a test count off by one). Each was caught by re-reading.
- A plan step that says "check that X shows" needs a way to check it. Test the way first.
- When a change adds or retypes a field, search the spec for the concept (`grep size`) and read every invariant that mentions it. `allium check` does not catch a wrong type in an invariant.
- State in the docs, the changelog and the PR text only what was measured. "Unchanged at the defaults" was true for one model and false in general (session A, #103).
- `allium check` exits 1 on warnings, even on `main`. `scripts/check_specs.sh` fails only on an `error` diagnostic or a finding, and CI runs it. The accepted warnings are listed in [Development](development.md) (#109).
- Merge with squash, oldest PR first. After `gh pr merge`, `mergeable` reads `UNKNOWN` for about 15 s: run `git fetch` and look again in a separate command. Two PRs that each delete one of two adjacent Known-gaps rows conflict. Drop both rows and continue the rebase.

Finish:
- Merge on green CI, delete the branch (local and remote), confirm a clean tree.
- Update the memory file `project-layerforge-backlog.md`. Add a memory only for facts a future session cannot get from the repo.

## Known traps

See memory `layerforge-tooling-gotchas` and [Development](development.md) (Working Notes): trimesh `section` argument order, `to_2D` re-centring, no triangulation engine, BSD `sed -i`, `qlmanage` hangs (use `rsvg-convert`), `| tail` hiding failed checks, and zsh not splitting an unquoted `$var` (three slips in one day: use one explicit call per case). In shell heredocs, do not put backslashes before backticks: build issue and PR bodies in Python or from a file.

## Status

Sessions A, A2 and B are done (2026-09-25). A: ranks 1 to 5 merged as #100 to #104, and rank 6 (#73) was decided as a documented limit (#105). A2: #106, #110 and #109 merged as #112 to #114. B: #87 merged as #115, with the mechanism and the keys that exist today (`layer_height`, `marks.size`, `marks.tolerance`, `marks.min_distance`, `marks.shapes`, `marks.angle`). Retrospective 2026-09-25: nine new issues, #117 to #125 (ranks 32 to 40). Session A3 is done (2026-09-25): #120, #117, #119, #118 and #121 merged as #129 to #133. The retrospective found four more issues, #135 to #138 (ranks 41 to 44). The next work is #135 (session A5), then session C (#74, #84), or A4 (#122, #124) first. Each later issue adds its own config keys and its own row in TR-16; the default `marks.tolerance` of 0.1 x mark size comes with #62. Session A5 and #74 are done (2026-09-25): #135, #136 and #144 merged as #146, #74 as #147, #137 and #138 as #148. The retrospective found #145 (G-30) and #149 (G-31). A second pass found #151 to #154. The next work is #84 (session C), then session D with #125 first.

Session C2 is done (2026-09-25): #84, #125, #85, #149 and #153 merged as #156, #158, #159, #160 and #161. #84 gave each shape `outline()` and `symmetry_order`, so the arrow is now a closed polygon. #85 made the adjuster and the calculator check the whole hole and the web (`marks.min_web_ratio`, config file only, default 0.5), and closed item 2 of #108. The retrospective found #157 (the circle outline) and #162 (an unregistered shape name skips every check), ranks 54 and 55, and I commented on #83 (the arrow's default colour equals the outline's), #124 (a proposed cap on its acceptance list) and #152 (another drifted example). Session D followed (below). Session A4 (#122, #124, #152) can go between any two sessions. A second retrospective pass found #164 and #165 (ranks 56 and 57, both go with #62), and one wrong claim in the text of #159, which it corrected (the calculator's disc does not hold the circle's `outline()` polygon; #157). It also ran the `allium:weed` check that was skipped for #149: no code bug, one wording gap in FR-5, fixed here.

Session D is done (2026-09-25): #157, #162, #108 (items 1 and 3), #62, #76, #164 and #165 merged as #167 to #170. The mark size now follows the sheet and the kerf, not the place: a 10 mm cube at the defaults goes from 0 marks to 4 in 4 slices (measured on `main` before and on the branch after). `layer_height` and the kerf default in mm and follow `--units`. `Slice` needs `layer_height`. The retrospective found #171 to #173 (ranks 58 to 60) and commented on #63 (the calculator's radius is one number for every mark). The next work is session E (#83, #75, #89, #141) or A4 (#122, #124, #152).

A second retrospective pass on session D (2026-09-26) ran the repo-wide grep for the old rule (no stale text), and the probes `--kerf 0`, `--units cm`, `--mark-min-distance 0`, a 100 mm sheet and 6.003 and 6.004 mm cubes (each matches the docs; 6.003 gets no mark in 3 slices and 6.004 gets one in each). It found #175 (rank 61), a negative zero in the SVG that predates #170 (comment on #154), the spec side of #172 (comment), and three wrong or late statements in the text of #170, which I corrected. Main was green after #174 (tests and docs).

## Open decisions and owner inputs

| Decision | Blocks | Needed by |
|---|---|---|
| Laser and material numbers (#96): kerf, smallest clean hole, number height, hairline behavior. Cut the sheet of #141 on your machine. | Final defaults in #87, #62, #75 | Before the proposed defaults are final |
| Colours and stroke conventions of the laser software (#83): answered in part by TR-17. Red cut and black engrave stay as defaults. The probe of #141 shows what your software does. | #83 | Session E |
| Dowel hole design (#93): review the proposal in TR-15, mainly position and count | #93, #142 | Later |
| Config key names in TR-16 | Later keys | Each issue that adds a key. The six built in #87 follow TR-16 as written, so the owner may still rename them. |

## What is settled

Overlapping shells in one mesh are a documented limit (#73, decided 2026-09-25): the even-odd rule stays, users merge bodies before export, and a later opt-in `manifold3d` union is possible. Marks are holes. Every layer aligns to the one below and the one above in exactly one way. The number fixes the flip. Mark shape fixes rotation. Units default to mm. Failing to align is an error before writing, and `--allow-unaligned` overrides it. Angle 0 points along +x, counter-clockwise. Mark size is the diameter of the smallest circle that holds the outline. Marks are chosen per pair of adjacent layers. Every laser, material and judgment number is a setting. Dowel holes are a later feature.
