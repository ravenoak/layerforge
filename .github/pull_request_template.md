What changes, and why, in one or two sentences.

Fixes #N (use `Refs #N` when part of the issue stays open)

- [ ] Tests written first; `uv run ruff format`, `ruff check`, `pyright` and `pytest -q` run without pipes
- [ ] The FR row updated, the fixed Known-gaps row removed, and `specs/layerforge.allium` updated
- [ ] `./scripts/check_specs.sh` passes (no `error` diagnostics, no `findings`)
- [ ] `uv run mkdocs build --strict` passes
- [ ] A line under `Unreleased` in `CHANGELOG.md` when a user can see the change, marked **Breaking** where it is

A box that does not apply stays unticked and says `not needed: <reason>`.
