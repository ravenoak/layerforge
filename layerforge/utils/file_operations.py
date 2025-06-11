import pathlib


def ensure_directory_exists(directory: str) -> None:
    """Ensure the specified directory exists.

    Creates the directory if it does not exist.

    Parameters
    ----------
    directory : str
        The directory to ensure exists.

    Returns
    -------
    None

    Side effects
    -----------
    Creates the directory if it does not exist.
    """
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)


def generate_file_name(directory: str, index: int, extension: str) -> str:
    """Generate a standardized file name.

    Parameters
    ----------
    directory : str
        The directory where the file will be saved.
    index : int
        The index of the layer.
    extension : str
        The file extension.

    Returns
    -------
    str
        The generated file name
    """
    return f"{directory}/slice_{index:03d}.{extension}"
