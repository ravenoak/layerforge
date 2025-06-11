import os
from layerforge.utils.file_operations import ensure_directory_exists, generate_file_name


def test_ensure_directory_exists_creates_tmp_dir(tmp_path):
    dir_path = tmp_path / "created"
    assert not dir_path.exists()
    ensure_directory_exists(str(dir_path))
    assert dir_path.exists() and dir_path.is_dir()


def test_generate_file_name_formatting():
    result = generate_file_name("dir", 1, "svg")
    assert result == "dir/slice_001.svg"
