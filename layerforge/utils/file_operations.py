import pathlib


def ensure_directory_exists(directory):
    """Ensure the specified directory exists."""
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)


def generate_file_name(directory, index, extension):
    """Generate a standardized file name."""
    return f"{directory}/slice_{index:03d}.{extension}"
