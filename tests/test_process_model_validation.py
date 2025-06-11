import pytest
import click

from layerforge.cli import process_model


def test_process_model_invalid_layer_height(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=0,
            output_folder=str(tmp_path),
        )


def test_process_model_invalid_scale_factor(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(tmp_path),
            scale_factor=0,
        )


def test_process_model_invalid_target_height(cylinder_stl, tmp_path):
    with pytest.raises(click.BadParameter):
        process_model(
            stl_file=str(cylinder_stl),
            layer_height=1.0,
            output_folder=str(tmp_path),
            target_height=0,
        )

