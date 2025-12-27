import pathlib


def get_absolute_path(relative_path_from_root: str) -> str:
    """
    Returns the absolute path for a given path relative to the project root.
    """
    project_root = pathlib.Path(__file__).resolve().parent.parent

    return str(project_root / relative_path_from_root)


def ensure_path_exists(path_string: str) -> None:
    """
    Ensures that the directory structure for the given path string exists
     and creates the file itself if it does not exist.
    Assumes the leaf of the path_string is a file.
    """
    path = pathlib.Path(path_string)

    # Create the parent directories (e.g., /data/raw/)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create the file itself (e.g., moduleInfo.json) if it doesn't exist
    path.touch(exist_ok=True)
