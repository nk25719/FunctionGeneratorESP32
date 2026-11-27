"""Package verified firmware builds as release candidates."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGETS = {
    "web-esp32dev": "ESP32 DevKit",
    "standalone-esp32": "esp32:esp32:esp32",
    "standalone-esp32s2": "esp32:esp32:esp32s2",
    "examples/adc-esp32": "esp32:esp32:esp32",
    "examples/adc-esp32s2": "esp32:esp32:esp32s2",
}


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024), b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True
    ).strip()


def release_notes(changelog):
    match = re.search(
        r"(?ms)^## \[Unreleased\]\s*\n"
        r"(.*?)(?=^## |\Z)",
        changelog
    )

    if not match:
        raise ValueError("Missing Unreleased section")

    return match.group(1).strip()


def validate_builds(build_dir):
    firmware = build_dir / "firmware"

    for target in TARGETS:
        directory = firmware / target

        binaries = [
            p for p in directory.glob("*.bin")
            if p.is_file() and p.stat().st_size > 0
        ]

        if not binaries:
            raise ValueError(
                f"Missing binaries for {target}"
            )

    for name in (
        "firmware.bin",
        "bootloader.bin",
        "partitions.bin",
    ):
        path = firmware / "web-esp32dev" / name

        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Missing {path}")


def package(build_dir, output, candidate, attempt):
    if candidate < 1 or attempt < 1:
        raise ValueError("Invalid candidate or attempt")

    version = (ROOT / "VERSION").read_text().strip()

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid firmware version")

    if git("status", "--porcelain"):
        raise ValueError(
            "Working tree must be clean before packaging"
        )

    validate_builds(build_dir)

    name = (
        f"FunctionGeneratorESP32-v{version}"
        f"-rc.{candidate}"
    )

    if attempt > 1:
        name += f"-attempt.{attempt}"

    output.mkdir(parents=True, exist_ok=True)
    destination = output / name
    archive = output / f"{name}.zip"

    if destination.exists() or archive.exists():
        raise FileExistsError(
            "Candidate already exists; refusing overwrite"
        )

    destination.mkdir()

    shutil.copytree(
        build_dir / "firmware",
        destination / "firmware"
    )

    shutil.copytree(
        ROOT / "documentation",
        destination / "documentation",
        ignore=shutil.ignore_patterns(
            ".DS_Store", "__pycache__"
        )
    )

    shutil.copy2(
        ROOT / "VERSION",
        destination / "VERSION"
    )

    shutil.copy2(
        build_dir / "BUILD_REPORT.txt",
        destination / "BUILD_REPORT.txt"
    )

    shutil.copy2(
        ROOT / "documentation/Development/BUILD_ENVIRONMENT.md",
        destination / "BUILD_ENVIRONMENT.md"
    )

    shutil.copy2(
        ROOT / "documentation/Development/VALIDATION_CHECKLIST.md",
        destination / "VALIDATION_CHECKLIST.md"
    )

    license_path = ROOT / "LICENSE"

    if license_path.exists() and license_path.stat().st_size:
        shutil.copy2(
            license_path,
            destination / "LICENSE"
        )

    notes = release_notes(
        (ROOT / "CHANGELOG.md").read_text()
    )

    commit = git("rev-parse", "HEAD")

    (destination / "RELEASE_NOTES.md").write_text(
        f"# {name}\n\n"
        f"Firmware version: {version}\n\n"
        f"Source commit: {commit}\n\n"
        "Status: Release candidate, not approved.\n\n"
        "## Changes\n\n"
        f"{notes}\n\n"
        "## Validation\n\n"
        "Physical hardware validation and maintainer "
        "approval are required before publication.\n",
        encoding="utf-8"
    )

    files = []

    for path in sorted(destination.rglob("*")):
        if path.is_file():
            files.append({
                "path": path.relative_to(
                    destination
                ).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    manifest = {
        "schema_version": 1,
        "project": "FunctionGeneratorESP32",
        "firmware_version": version,
        "candidate": candidate,
        "run_attempt": attempt,
        "release_type": "candidate",
        "source_commit": commit,
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "hardware_validation": "pending",
        "maintainer_approval": "pending",
        "license_included": (
            destination / "LICENSE"
        ).exists(),
        "targets": TARGETS,
        "files": files,
    }

    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8"
    )

    checksums = []

    for path in sorted(destination.rglob("*")):
        if path.is_file():
            checksums.append(
                f"{sha256(path)}  "
                f"{path.relative_to(destination).as_posix()}"
            )

    (destination / "SHA256SUMS.txt").write_text(
        "\n".join(checksums) + "\n",
        encoding="utf-8"
    )

    with zipfile.ZipFile(
        archive, "w", zipfile.ZIP_DEFLATED
    ) as bundle:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                bundle.write(
                    path,
                    path.relative_to(output)
                )

    archive.with_suffix(".zip.sha256").write_text(
        f"{sha256(archive)}  {archive.name}\n"
    )

    print(f"Candidate created: {archive}")

    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--build-dir", type=Path, required=True
    )
    parser.add_argument(
        "--output", type=Path, required=True
    )
    parser.add_argument(
        "--candidate", type=int, required=True
    )
    parser.add_argument(
        "--attempt", type=int, default=1
    )

    args = parser.parse_args()

    package(
        args.build_dir.resolve(),
        args.output.resolve(),
        args.candidate,
        args.attempt,
    )
