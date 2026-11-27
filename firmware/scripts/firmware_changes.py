"""Classify the paginated GitHub changed-file list for a merged PR."""

import json
from pathlib import PurePosixPath
import sys


SKETCH_EXTENSIONS = {".ino", ".h", ".hpp", ".c", ".cc", ".cpp", ".cxx", ".S", ".s"}


def is_firmware_path(path):
    # Normalize paths following repository restructuring.
    if path.startswith("firmware/"):
        path = path[len("firmware/"):]

    if path == "functiongenerator_web/platformio.ini" or path.startswith(
        ("functiongenerator_web/src/", "functiongenerator_web/include/")
    ):
        return True

    file = PurePosixPath(path)
    return (
        file.parts[0:1] == ("functiongenerator_esp32",)
        and (len(file.parts) == 2 or file.parts[1:2] == ("src",))
        and file.suffix in SKETCH_EXTENSIONS
    )


def has_firmware_changes(pages):
    files = [file for page in pages for file in page]
    for file in files:
        # Ignore unchanged relocations into firmware/.
        previous = file.get("previous_filename", "")
        current = file["filename"]

        if (
            file.get("status") == "renamed"
            and previous
            and current == "firmware/" + previous
            and file.get("additions") == 0
            and file.get("deletions") == 0
        ):
            continue

        if is_firmware_path(file["filename"]) or is_firmware_path(
            file.get("previous_filename", "")
        ):
            return True

    # GitHub returns at most 3,000 files. A truncated list cannot prove a skip.
    if len(files) >= 3000:
        raise ValueError("Cannot rule out firmware changes in GitHub's capped file list")
    return False


if __name__ == "__main__":
    print("true" if has_firmware_changes(json.load(sys.stdin)) else "false")
