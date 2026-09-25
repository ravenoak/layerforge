What changes, and why, in one or two sentences.

Fixes #N (use `Refs #N` when part of the issue stays open)

- [ ] Tests written first; `uv run ruff format`, `ruff check`, `pyright` and `pytest -q` run without pipes
- [ ] The FR row updated, the fixed Known-gaps row removed, and `specs/layerforge.allium` updated
- [ ] `allium check` shows no `error` diagnostics and no `findings` (read the JSON, not the exit code)
- [ ] `uv run mkdocs build --strict` passes
- [ ] A line under `Unreleased` in `CHANGELOG.md` when a user can see the change, marked **Breaking** where it is
