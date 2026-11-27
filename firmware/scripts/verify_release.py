"""Verify an approved release candidate before publication."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import zipfile

from pathlib import Path, PurePosixPath


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True
    ).strip()


def verify(archive, approval_path, expected_version,
           run_id, attempt):

    approval = json.loads(
        approval_path.read_text()
    )

    require(
        re.fullmatch(
            r"(0|[1-9]\d*)\."
            r"(0|[1-9]\d*)\."
            r"(0|[1-9]\d*)",
            expected_version
        ),
        "Invalid release version"
    )

    require(
        approval.get("schema_version") == 1,
        "Unsupported approval schema"
    )

    require(
        approval["decision"] == "approved",
        "Release is not approved"
    )

    for field in (
        "hardware_validation",
        "documentation_review",
        "license_review"
    ):
        require(
            approval[field] == "passed",
            f"{field} has not passed"
        )

    for field in (
        "approved_by",
        "approved_at_utc",
        "validation_evidence"
    ):
        require(
            isinstance(approval[field], str)
            and approval[field].strip(),
            f"Missing {field}"
        )

    require(
        str(approval["candidate_run_id"]) == str(run_id),
        "Candidate run ID mismatch"
    )

    require(
        approval["candidate_run_attempt"] == attempt,
        "Candidate attempt mismatch"
    )

    require(
        approval["firmware_version"] == expected_version,
        "Approval version mismatch"
    )

    try:
        approved_at = datetime.fromisoformat(
            approval["approved_at_utc"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("Invalid approval timestamp") from exc

    require(
        approved_at.tzinfo is not None
        and approved_at.utcoffset() == timezone.utc.utcoffset(None),
        "Approval timestamp must use UTC"
    )

    require(
        approved_at <= datetime.now(timezone.utc),
        "Approval timestamp is in the future"
    )

    archive_hash = sha256(archive.read_bytes())

    require(
        archive_hash == approval["archive_sha256"],
        "Approved archive checksum mismatch"
    )

    with zipfile.ZipFile(archive) as bundle:

        require(
            bundle.testzip() is None,
            "Corrupt ZIP archive"
        )

        names = [
            n for n in bundle.namelist()
            if not n.endswith("/")
        ]

        require(
            len(names) == len(set(names)),
            "Duplicate archive entries"
        )

        for name in names:
            path = PurePosixPath(name)

            require(
                not path.is_absolute()
                and ".." not in path.parts
                and "\\" not in name,
                "Unsafe archive path"
            )

        roots = {
            PurePosixPath(n).parts[0]
            for n in names
        }

        require(
            len(roots) == 1,
            "Invalid archive structure"
        )

        root = roots.pop()

        def read(name):
            try:
                return bundle.read(f"{root}/{name}")
            except KeyError as exc:
                raise ValueError(
                    f"Missing archive file: {name}"
                ) from exc

        manifest = json.loads(
            read("manifest.json")
        )

        require(
            manifest.get("schema_version") == 1,
            "Unsupported manifest schema"
        )

        require(
            manifest["project"] ==
            "FunctionGeneratorESP32",
            "Unexpected project"
        )

        require(
            manifest["release_type"] == "candidate",
            "Expected a release candidate"
        )

        require(
            manifest["firmware_version"] ==
            expected_version,
            "Manifest version mismatch"
        )

        require(
            read("VERSION").decode().strip() ==
            expected_version,
            "Packaged VERSION mismatch"
        )

        require(
            manifest["run_attempt"] == attempt,
            "Manifest attempt mismatch"
        )

        commit = manifest["source_commit"]

        require(
            re.fullmatch(r"[0-9a-f]{40}", commit),
            "Invalid source commit"
        )

        require(
            commit == approval["source_commit"],
            "Approved source commit mismatch"
        )

        require(
            git("show", f"{commit}:VERSION") ==
            expected_version,
            "Source VERSION mismatch"
        )

        require(
            manifest["license_included"] is True,
            "Candidate does not include a license"
        )

        require(
            read("LICENSE").strip(),
            "Empty license"
        )

        require(
            read("LICENSE") ==
            subprocess.check_output(
                ["git", "show", f"{commit}:LICENSE"]
            ),
            "Packaged license differs from source"
        )

        listed = set()

        for entry in manifest["files"]:
            name = entry["path"]

            require(
                name not in listed,
                f"Duplicate manifest entry: {name}"
            )

            listed.add(name)
            data = read(name)

            require(
                len(data) == entry["size_bytes"],
                f"Size mismatch: {name}"
            )

            require(
                sha256(data) == entry["sha256"],
                f"Manifest checksum mismatch: {name}"
            )

        actual = {
            n[len(root) + 1:]
            for n in names
        }

        require(
            listed == actual - {
                "manifest.json",
                "SHA256SUMS.txt"
            },
            "Manifest file inventory mismatch"
        )

        checked = set()

        for line in read(
            "SHA256SUMS.txt"
        ).decode().splitlines():

            digest, name = line.split("  ", 1)

            require(
                name not in checked,
                "Duplicate checksum entry"
            )

            checked.add(name)

            require(
                sha256(read(name)) == digest,
                f"Checksum mismatch: {name}"
            )

        require(
            checked == actual - {"SHA256SUMS.txt"},
            "Incomplete checksum inventory"
        )

    return {
        "version": expected_version,
        "source_commit": commit,
        "archive_sha256": archive_hash,
        "approved_by": approval["approved_by"],
        "status": "verified"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--archive", type=Path,
                        required=True)
    parser.add_argument("--approval", type=Path,
                        required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt", type=int,
                        required=True)

    args = parser.parse_args()

    result = verify(
        args.archive,
        args.approval,
        args.version,
        args.run_id,
        args.attempt
    )

    print(json.dumps(result, indent=2))
