"""checks.allow_unaligned and --allow-unaligned (TR-12, #92): default, flag, file."""

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


def test_help_lists_the_flag():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--allow-unaligned" in result.output


def test_a_quoted_value_in_the_config_file_is_refused_with_exit_2(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[checks]\nallow_unaligned = "yes"\n')
    result = CliRunner().invoke(cli, ["--config", str(bad), "--stl-file", "unused.stl"])
    assert result.exit_code == 2
    assert "checks.allow_unaligned" in result.output
