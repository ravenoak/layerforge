"""checks.allow_unaligned and --allow-unaligned (TR-12, #92): default, flag, file."""

import trimesh
from click.testing import CliRunner

from layerforge.cli import cli
from layerforge.settings import Settings, merge_settings


def test_allow_unaligned_is_off_by_default():
    assert Settings().checks.allow_unaligned is False


def test_the_flag_turns_it_on():
    assert merge_settings(Settings(), {"allow_unaligned": True}).checks.allow_unaligned is True


def test_the_file_value_stands_when_the_flag_is_absent():
    file_settings = Settings.model_validate({"checks": {"allow_unaligned": True}})
    merged = merge_settings(file_settings, {"allow_unaligned": None})
    assert merged.checks.allow_unaligned is True


def test_the_negated_flag_overrides_a_file_that_allows_it():
    # A guard, not a driver: `merge_settings` already lets an explicit False through.
    file_settings = Settings.model_validate({"checks": {"allow_unaligned": True}})
    merged = merge_settings(file_settings, {"allow_unaligned": False})
    assert merged.checks.allow_unaligned is False


def test_help_lists_both_forms_of_the_flag():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--allow-unaligned" in result.output
    assert "--no-allow-unaligned" in result.output


def _run_cone(tmp_path, *extra):
    stl = tmp_path / "cone.stl"
    trimesh.creation.cone(radius=20, height=30).export(stl)
    out = tmp_path / "out"
    args = ["--stl-file", str(stl), "--output-folder", str(out), *extra]
    return CliRunner().invoke(cli, args), out


def test_no_allow_unaligned_beats_a_file_that_allows_it(tmp_path):
    config = tmp_path / "allow.toml"
    config.write_text("[checks]\nallow_unaligned = true\n")
    result, out = _run_cone(tmp_path, "--config", str(config), "--no-allow-unaligned")
    assert result.exit_code == 1, result.stderr
    assert not out.exists()
    assert "Nothing was written. Use --allow-unaligned" in result.stderr


def test_allow_unaligned_beats_a_file_that_forbids_it(tmp_path):
    config = tmp_path / "forbid.toml"
    config.write_text("[checks]\nallow_unaligned = false\n")
    result, out = _run_cone(tmp_path, "--config", str(config), "--allow-unaligned")
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10


def test_the_file_still_decides_when_neither_form_is_given(tmp_path):
    config = tmp_path / "allow.toml"
    config.write_text("[checks]\nallow_unaligned = true\n")
    result, out = _run_cone(tmp_path, "--config", str(config))
    assert result.exit_code == 0, result.stderr
    assert len(list(out.glob("slice_*.svg"))) == 10


def test_a_quoted_value_in_the_config_file_is_refused_with_exit_2(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[checks]\nallow_unaligned = "yes"\n')
    result = CliRunner().invoke(cli, ["--config", str(bad), "--stl-file", "unused.stl"])
    assert result.exit_code == 2
    assert "checks.allow_unaligned" in result.output
