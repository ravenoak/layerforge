from pathlib import Path


def test_tests_run_in_an_empty_directory():
    """A stray layerforge.toml in a checkout must not change a test (#120)."""
    assert not any(Path.cwd().iterdir())
