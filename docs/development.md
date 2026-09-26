# Development

## Requirements

The functional and non-functional requirements, constraints and known gaps are
on the [Requirements](requirements.md) page. The same behavior is written as a
formal Allium specification in `specs/layerforge.allium`. Check it with:

```bash
allium check specs/layerforge.allium
```

## Pseudocode

This is the intended design. Where the code differs, see the known gaps on the
[Requirements](requirements.md#known-gaps) page. The requirements behind the
mark steps are on the [Alignment requirements](alignment_requirements.md) page.

1. Load the 3D Model:
    1. Read an STL file to load the model into the application.
2. Scale the Model:
    1. If a scale factor is provided, scale the model by this factor.
    2. If a target height is provided, calculate the necessary scale factor to achieve this height and apply it to the model, ensuring the aspect ratios are maintained.
3. Slice the Model into Layers:
    1. Determine the positions for each slice based on the specified layer height.
    2. For each determined position:
        1. Slice the model at this position.
        2. Project the resulting slice to a 2D plane.
        3. Create a List of `Polygon`s representing the 2D contours of the slice.
4. For each slice, process the slice:
    1. Calculate Reference Marks:
        1. Evaluate candidate points using a geometric stability metric derived from GDOP.
        2. Choose marks so that each piece can be aligned in exactly one way with each piece it overlaps in the layer above and below, ensuring:
           * Marks are holes, chosen inside the overlap of two adjacent outlines, so each shared mark is a hole in both layers.
           * A mark is reused while it stays valid in the next layer and retired when it does not.
           * Shapes are chosen to remove rotational symmetry: a piece with one mark gets a shape with a direction, and two marks differ in shape.
           * The whole hole lies inside the piece, clear of edges, other holes and the number.
           * The size of the marks follows the sheet thickness (the layer height). It does not follow the model's scale.
           * The distance between marks is large enough to fix rotation with the precision needed.
    2. Adjust Reference Marks:
        1. Adjust the positions of the reference marks to avoid overlaps, using the ReferenceMarkAdjuster.
    3. Check alignment:
        1. Before any file is written, check that every piece can be aligned in exactly one way. If not, stop with an error that names the slice and piece.
    4. Generate SVG File:
        1. Draw the slice contours and the reference marks as cut lines.
        2. Engrave the slice number inside each piece, clear of the marks.
5. Output:
    1. Save the generated SVG files to the specified output directory, with each file representing a slice of the original 3D model.

## Expected Workflow

1. Build a :class:`Model` using :class:`ModelFactory` and the desired mesh loader.
2. Call :meth:`SlicerService.slice_model` to produce a list of :class:`Slice` objects.
3. Use :class:`ReferenceMarkService` to process each slice so reference marks are calculated and adjusted.
4. Pass the processed slices to :class:`SVGGenerator` (via the CLI or directly) to write SVG files.

## Running the Tests

```bash
uv sync
uv run pytest
```

`uv sync` installs the runtime dependencies and the `dev` group (pytest and
hypothesis). Add `--group docs` to build the documentation with
`uv run mkdocs build --strict`.

Every test runs in an empty temporary directory (an autouse fixture in
`tests/conftest.py`), so a `layerforge.toml` in your checkout does not change a
result. A test that needs a file from the repo must use an absolute path.

## Linting and Type Checking

```bash
uv run ruff check
uv run ruff format --check
uv run pyright
```

pyright runs in `strict` mode on `src/` and `standard` mode on `tests/` and `scripts/`.
CI runs all three on every pull request.

The pyright settings are the `[tool.pyright]` table in `pyproject.toml`. The command, CI
and a language server started in the repo root read it (pyright's configuration docs say
the server uses the same file). Keep it in that one place: a `pyrightconfig.json` would
take precedence over the table, and two files drift. The table points at the project
environment (`venvPath` and `venv`, the `.venv` that `uv sync` creates) and at `src`
(`extraPaths`), so an editor needs no extra setting beyond opening the repo root. To see
that a tool used the table, run `uv run pyright --verbose`: its first line reads
`Loading pyproject.toml file at ...`. pyright accepts an unknown key with only a message
(`Config contains unrecognized setting`) and exit code 0, so read the output after you
edit the table.

## Spec checks

`scripts/check_specs.sh` runs `allium check` on every file in `specs/`. It needs
`allium` and `jq` on the path. CI runs it as the `specs` job with a pinned allium
version and a pinned SHA-256 for the Linux tarball, and with a read-only token.

### Where the allium binary comes from

Checked on 2026-09-25 (allium v3.6.1, `juxt/allium-tools`, and the Allium site):

- Upstream does not sign the release binaries. Its README says "not yet signed".
  The release has no signature, no SBOM and no build attestation
  (`gh attestation verify` returns 404), and the workflow has no signing step.
- `SHA256SUMS.txt` in the release lists only the vsix and the LSP tarball, not the
  binaries. The Homebrew formula has an empty `sha256 ""` for both x86_64 targets.
- The site's installation page says nothing about checksums or signing.
- The release workflow builds the binaries in GitHub Actions from the tagged
  commit, then attaches them to the release. A release asset can be replaced
  afterwards. A pinned hash catches that.

Decision: keep the release tarball with a pinned SHA-256, and set the pin only
after comparing the asset with the tarball its own release run built from the
tagged commit. For v3.6.1 the two matched (`e00c99ae...`, run 33000128435, commit
`190ea5ce`). This shows the pin is what upstream CI built. It does not show the
source is trustworthy, and no option here does. `cargo install allium-cli --locked`
would check the crate against the crates.io index, but it adds a compile step to
every run for the same trust in upstream, so it was not chosen. The job needs no
secrets and only reads the repository. The workflow sets `permissions: contents: read`
for all jobs, which the repository default (`read`) already gives.

The pin covers the binary that CI runs, the x86_64 Linux tarball. A local run uses
whatever `allium` is installed. On 2026-09-25 that was the Homebrew arm64 build of
the same version (3.6.1), and it printed the same diagnostic counts as CI.

### Bumping allium

Do this within 90 days of the upstream release, while its build artifacts exist.
Set `V` to the new version. The commands assume a lightweight tag, as v3.6.1 has
(`.object.type` is `commit`). For an annotated tag, dereference it first.

```bash
V=3.6.1
tag=$(gh api repos/juxt/allium-tools/git/ref/tags/v$V --jq .object.sha)
run=$(gh run list -R juxt/allium-tools -w release-artifacts.yml -e push --status success \
  --json databaseId,headSha,headBranch \
  --jq "map(select(.headBranch==\"v$V\" and .headSha==\"$tag\"))[0].databaseId")
gh run download "$run" -R juxt/allium-tools -n allium-x86_64-unknown-linux-gnu -D ci
gh release download "v$V" -R juxt/allium-tools -p allium-x86_64-unknown-linux-gnu.tar.gz -D rel
shasum -a 256 ci/*.tar.gz rel/*.tar.gz   # the two hashes must match
```

Then set `ALLIUM_VERSION` and `ALLIUM_SHA256` in `.github/workflows/tests.yaml`,
upgrade the local `allium`, run `./scripts/check_specs.sh`, and read any new
diagnostics. If the hashes differ, do not bump. Nothing notices a new release, and
being behind does not affect the check. Look at
`gh release list -R juxt/allium-tools` when you change a spec.

The script fails on an `error` diagnostic or a non-empty `findings` list. It does
not use the exit code, because `allium check` exits 1 on warnings and infos too.
These diagnostics are accepted, and the script prints their counts:

- `layerforge.allium`: two `externalEntity.missingSourceHint` warnings for `Mesh`
  and `Operator`. The hint wants an import of the spec that governs the entity.
  trimesh and a person have no allium spec, so there is nothing to import.
- `layerforge.allium`: `status.unreachableValue` for `Slice.planned`. The value is
  set by `Slice.created(... status: planned)` inside a `for` loop. The checker
  does not see a creation inside a loop. A single creation outside the loop, as
  a test in a scratch copy showed, makes the warning go away.
- `alignment.allium`: unused and unreachable items that exist because the target
  spec has no code yet. Each goes away when its feature lands.

A new warning is not a failure, so read the counts in the log when a spec changes.

## Defaults

Each default has one source in code: `ReferenceMarkConfig` for the `marks.*` keys, and
`Settings` for `units` and `layer_height` (`settings.py` reads the mark defaults from
`ReferenceMarkConfig`). The `--help` text of `cli.py` is built from `Settings()`, so it
follows a change.

`tests/test_defaults_documented.py` compares three copies with `Settings()`: the keys table
of `docs/configuration.md`, the `config` block of `specs/layerforge.allium`, and the
`--help` text. Change a default and the test fails until the table and the spec agree.
A new setting must get a row in the table, because the test also compares the keys.

Two kinds of copy are not tested:

- The prose of `docs/requirements.md` (FR-2, FR-6, FR-31) and the tuning advice in
  `docs/reference_mark_algorithm.md`. Search for the old value when you change a default.
- The TR-16 table of `docs/alignment_requirements.md`. It holds target defaults, such as
  0.1 times the mark size for `marks.tolerance`, that differ from today's on purpose.

`ReferenceMarkConfig` keeps its own ranges (`ge=0`, `gt=0`), because Python callers build it
without `Settings`. `Settings` repeats them, because it checks a file or option value before a
`ReferenceMarkConfig` is built.

## Changelog and versions

The [changelog](https://github.com/ravenoak/layerforge/blob/main/CHANGELOG.md) states
the version policy. LayerForge is at 0.x, so a minor version may break users.
A pull request that changes options, defaults, exit codes, output files or public
functions adds a line under `Unreleased` and marks it **Breaking** when existing
use stops working or gives different output.

New pull requests open with a checklist from
`.github/pull_request_template.md`. It lists the checks and the changelog line.

## Working Notes

- Run the checks so that a failure is not hidden. Do not pipe them through
  `tail` in an `&&` chain, because the pipe returns the exit code of `tail`.
  Run `uv run ruff format` before `ruff check` and `pyright`.
- `Trimesh.section` takes `(plane_normal, plane_origin)` when called with
  positional arguments. Pass both by keyword.
- `Path3D.to_2D()` without a transform re-centres every cut. Slices must use the
  transform in `Model.calculate_slice_contours` to share one frame.
- Hypothesis draws floats such as 1e-200. A hull edge that short makes GEOS divide by
  zero in `boundary.distance`. Round generated coordinates (issue #77).
- `nan < 0` and `nan <= 0` are false, so a sign check lets `nan` through. Use
  `math.isfinite` too (issue #106).
- `allium check` exits 1 on warnings, even on `main`. Read its `findings` and any
  `error` diagnostics (issue #109).
- After `gh pr merge`, `mergeable` reads `UNKNOWN` for about 15 s. Fetch and check
  again in a separate command.
- `trimesh.creation.extrude_polygon` needs a triangulation engine that is not
  installed. Tests build shapes with `extrude_triangulation` or the primitives
  in `trimesh.creation` instead.
- To look at an SVG, render it with `rsvg-convert -w 500 -b white in.svg -o out.png`.
  Do not use `qlmanage`, which can hang.
- Slice positions are the middle of each layer. A cut exactly on a face of the
  mesh comes out empty.
- Write a pydantic default as `Field(default=10.0, allow_inf_nan=False)`. With the
  value first, pyright strict reads the field as required and reports every call
  that leaves it out.
- `click.FloatRange` accepts `nan` and `inf`. Check `math.isfinite` yourself, or
  let the strict pydantic model in `settings.py` do it.
- `gh pr create --body-file` skips `.github/pull_request_template.md`. Copy the
  checklist into the body by hand.
- Run the checks in the order `ruff format`, `ruff check`, `pyright`, `pytest`, and run `pyright` after the first edit to a model, not at the end. In #106 it reported 31 errors that pytest did not show.
- zsh does not split an unquoted `$var`. `for a in "--x 1"; do cmd $a; done` passes one
  argument, and every probe then says `No such option '--x 1'` and tests nothing. Write
  one explicit call per case. Write scratch files with an absolute path.
- click 8.5 asks for an option with `prompt=` while it parses the options, so any check the
  command makes later comes after the question. `--stl-file` therefore has no `prompt=`.
  `cli` runs `resolve_settings` and then calls `click.prompt` (#135). A parse error (an
  unknown option, a wrong type, a `--config` path that does not exist) still comes first,
  and `--help`, which is eager, wins over every check `cli` makes. `CliRunner` results
  have `.stderr` and `.stdout` apart, and `.output` holds both.
- When a fix names one kind of bad input, probe the others of the same kind before you
  close the issue. #119 moved a bad config file before the prompt, and bad option values
  and the option conflict still came after it (G-28, #135). Probing the class of #135 found
  two more late failures: an output folder that is a file (#144, fixed with it) and a bad
  `--mark-color` (#145).
- The editor's pyright once showed errors (`No parameter named "size"`, an unknown import
  symbol) that `uv run pyright` and the CI lint job did not. They came right after
  `git checkout` and scripted edits changed files outside the editor. Later the same
  server resolved the symbols correctly (`goToDefinition` on `find_config_file` gave
  `settings.py:120`). The project venv holds no second copy of layerforge: a `.pth` file
  points at `src`. I did not reproduce the errors, so "stale state after edits made
  outside the editor" is a guess. Trust `uv run pyright` and the CI lint job.
- `Path.exists()` is False for a dangling symlink, but `mkdir` still fails on it. Use
  `os.path.lexists` when a check must match what the writer does (#144, found by
  `/code-review`).
- svgwrite 1.4.3, tiny profile: a `size` given as floats is written rounded to 4 decimals
  (`33.1235` for `33.123456789`), and the `viewBox` in full. Pass the size as text built
  from the same floats, or `width` will not equal the `viewBox` width (#74).
- `gh pr checks N` right after `gh pr create` can say `no checks reported`. Wait a few
  seconds, then use `--watch`.
- A test that passes before the code exists proves nothing. Two CLI tests that
  asserted only "exit 2 and the option name" passed on click's own
  `No such option` message, so they now assert the real message.

## Common Error Messages

- `ModuleNotFoundError: No module named 'networkx'` or `'scipy'` – `trimesh`
  needs both for slicing. Both are declared dependencies, so this means the
  environment was not created with `uv sync`.
