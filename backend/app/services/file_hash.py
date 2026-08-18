import hashlib
from pathlib import Path


def calculate_file_hash(
    path: Path,
) -> str:

    sha256 = hashlib.sha256()

    with path.open("rb") as file:

        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()