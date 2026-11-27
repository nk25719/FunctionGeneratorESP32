"""Regression tests for official release verification."""

import hashlib
import json
import tempfile
import unittest
import warnings
import zipfile

from pathlib import Path
from unittest.mock import patch

from firmware.scripts import verify_release as verifier


class ReleaseVerificationTests(unittest.TestCase):

    VERSION = "0.0.10"
    COMMIT = "a" * 40
    RUN_ID = "123456789"
    ATTEMPT = 1
    ROOT = "FunctionGeneratorESP32-v0.0.10-rc.1"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(self.temp.name)
        self.archive = self.directory / "candidate.zip"
        self.approval_path = self.directory / "APPROVAL.json"

        self.files = {
            "VERSION": b"0.0.10\n",
            "LICENSE": b"Synthetic test license\n",
            "firmware/web-esp32dev/firmware.bin": b"test firmware",
        }

        self.manifest = {
            "schema_version": 1,
            "project": "FunctionGeneratorESP32",
            "release_type": "candidate",
            "firmware_version": self.VERSION,
            "run_attempt": self.ATTEMPT,
            "source_commit": self.COMMIT,
            "license_included": True,
        }

        self.approval = {
            "schema_version": 1,
            "firmware_version": self.VERSION,
            "source_commit": self.COMMIT,
            "candidate_run_id": self.RUN_ID,
            "candidate_run_attempt": self.ATTEMPT,
            "hardware_validation": "passed",
            "documentation_review": "passed",
            "license_review": "passed",
            "decision": "approved",
            "approved_by": "test-reviewer",
            "approved_at_utc": "2026-01-01T00:00:00Z",
            "validation_evidence": "Synthetic test evidence",
        }

        self.source_version = self.VERSION
        self.source_license = self.files["LICENSE"]

    @staticmethod
    def digest(data):
        return hashlib.sha256(data).hexdigest()

    def create_archive(self, mutate=None, extra_entries=None):
        payload = dict(self.files)

        manifest = dict(self.manifest)
        manifest["files"] = [
            {
                "path": name,
                "size_bytes": len(data),
                "sha256": self.digest(data),
            }
            for name, data in sorted(payload.items())
        ]

        payload["manifest.json"] = json.dumps(
            manifest, indent=2
        ).encode()

        payload["SHA256SUMS.txt"] = "".join(
            f"{self.digest(data)}  {name}\n"
            for name, data in sorted(payload.items())
        ).encode()

        if mutate:
            mutate(payload)

        with zipfile.ZipFile(
            self.archive, "w", zipfile.ZIP_DEFLATED
        ) as bundle:
            for name, data in payload.items():
                bundle.writestr(
                    f"{self.ROOT}/{name}", data
                )

            for name, data in extra_entries or []:
                bundle.writestr(name, data)

        self.approval["archive_sha256"] = self.digest(
            self.archive.read_bytes()
        )

        self.write_approval()

    def write_approval(self):
        self.approval_path.write_text(
            json.dumps(self.approval, indent=2)
        )

    def verify(self):
        with patch.object(
            verifier, "git",
            return_value=self.source_version
        ), patch.object(
            verifier.subprocess,
            "check_output",
            return_value=self.source_license
        ):
            return verifier.verify(
                self.archive,
                self.approval_path,
                self.VERSION,
                self.RUN_ID,
                self.ATTEMPT,
            )

    def assert_rejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            self.verify()

    def test_valid_approved_candidate(self):
        self.create_archive()
        result = self.verify()

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["version"], self.VERSION)
        self.assertEqual(result["source_commit"], self.COMMIT)
        self.assertEqual(
            result["archive_sha256"],
            self.approval["archive_sha256"],
        )

    def test_pending_approval(self):
        self.approval["decision"] = "pending"
        self.create_archive()
        self.assert_rejected("Release is not approved")

    def test_incomplete_reviews(self):
        for field in (
            "hardware_validation",
            "documentation_review",
            "license_review",
        ):
            with self.subTest(field=field):
                self.approval[field] = "pending"
                self.create_archive()
                self.assert_rejected(f"{field} has not passed")
                self.approval[field] = "passed"

    def test_missing_approval_details(self):
        for field in (
            "approved_by",
            "approved_at_utc",
            "validation_evidence",
        ):
            with self.subTest(field=field):
                original = self.approval[field]
                self.approval[field] = ""
                self.create_archive()
                self.assert_rejected(f"Missing {field}")
                self.approval[field] = original

    def test_incorrect_run_id(self):
        self.approval["candidate_run_id"] = "999"
        self.create_archive()
        self.assert_rejected("Candidate run ID mismatch")

    def test_incorrect_attempt(self):
        self.approval["candidate_run_attempt"] = 2
        self.create_archive()
        self.assert_rejected("Candidate attempt mismatch")

    def test_incorrect_approval_version(self):
        self.approval["firmware_version"] = "0.0.11"
        self.create_archive()
        self.assert_rejected("Approval version mismatch")

    def test_incorrect_archive_hash(self):
        self.create_archive()
        self.approval["archive_sha256"] = "0" * 64
        self.write_approval()
        self.assert_rejected("Approved archive checksum mismatch")

    def test_incorrect_manifest_version(self):
        self.manifest["firmware_version"] = "0.0.11"
        self.create_archive()
        self.assert_rejected("Manifest version mismatch")

    def test_incorrect_packaged_version(self):
        self.files["VERSION"] = b"0.0.11\n"
        self.create_archive()
        self.assert_rejected("Packaged VERSION mismatch")

    def test_incorrect_manifest_attempt(self):
        self.manifest["run_attempt"] = 2
        self.create_archive()
        self.assert_rejected("Manifest attempt mismatch")

    def test_incorrect_source_commit(self):
        self.manifest["source_commit"] = "b" * 40
        self.create_archive()
        self.assert_rejected("Approved source commit mismatch")

    def test_invalid_source_commit(self):
        self.manifest["source_commit"] = "invalid"
        self.create_archive()
        self.assert_rejected("Invalid source commit")

    def test_incorrect_source_version(self):
        self.source_version = "0.0.11"
        self.create_archive()
        self.assert_rejected("Source VERSION mismatch")

    def test_missing_license(self):
        self.manifest["license_included"] = False
        del self.files["LICENSE"]
        self.create_archive()
        self.assert_rejected("Candidate does not include a license")

    def test_empty_license(self):
        self.files["LICENSE"] = b""
        self.create_archive()
        self.assert_rejected("Empty license")

    def test_mismatched_license(self):
        self.source_license = b"Different source license"
        self.create_archive()
        self.assert_rejected("Packaged license differs from source")

    def test_modified_firmware(self):
        def mutate(payload):
            payload[
                "firmware/web-esp32dev/firmware.bin"
            ] = b"evil firmware"

        self.create_archive(mutate=mutate)
        self.assert_rejected("Manifest checksum mismatch")

    def test_modified_firmware_size(self):
        def mutate(payload):
            payload[
                "firmware/web-esp32dev/firmware.bin"
            ] = b"modified"

        self.create_archive(mutate=mutate)
        self.assert_rejected("Size mismatch")

    def test_unexpected_file(self):
        self.create_archive(
            extra_entries=[
                (f"{self.ROOT}/unexpected.bin", b"unexpected")
            ]
        )
        self.assert_rejected("Manifest file inventory mismatch")

    def test_missing_file(self):
        def mutate(payload):
            del payload["firmware/web-esp32dev/firmware.bin"]

        self.create_archive(mutate=mutate)

        self.assert_rejected("Missing archive file")

    def test_unsafe_archive_path(self):
        self.create_archive(
            extra_entries=[
                (f"{self.ROOT}/../unsafe.bin", b"unsafe")
            ]
        )
        self.assert_rejected("Unsafe archive path")

    def test_duplicate_archive_entry(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)

            self.create_archive(
                extra_entries=[
                    (f"{self.ROOT}/VERSION", b"0.0.10\n")
                ]
            )

        self.assert_rejected("Duplicate archive entries")

    def test_multiple_archive_roots(self):
        self.create_archive(
            extra_entries=[
                ("another-root/file.bin", b"unexpected")
            ]
        )
        self.assert_rejected("Invalid archive structure")

    def test_incomplete_checksum_inventory(self):
        def mutate(payload):
            lines = payload["SHA256SUMS.txt"].splitlines()
            payload["SHA256SUMS.txt"] = (
                b"\n".join(lines[:-1]) + b"\n"
            )

        self.create_archive(mutate=mutate)
        self.assert_rejected("Incomplete checksum inventory")

    def test_incorrect_internal_checksum(self):
        def mutate(payload):
            lines = payload["SHA256SUMS.txt"].splitlines()
            lines[0] = b"0" * 64 + lines[0][64:]
            payload["SHA256SUMS.txt"] = (
                b"\n".join(lines) + b"\n"
            )

        self.create_archive(mutate=mutate)
        self.assert_rejected("Checksum mismatch")



    def test_unsupported_approval_schema(self):
        self.approval["schema_version"] = 99
        self.create_archive()
        self.assert_rejected("Unsupported approval schema")

    def test_unsupported_manifest_schema(self):
        self.manifest["schema_version"] = 99
        self.create_archive()
        self.assert_rejected("Unsupported manifest schema")

    def test_invalid_approval_timestamp(self):
        self.approval["approved_at_utc"] = "invalid"
        self.create_archive()
        self.assert_rejected("Invalid approval timestamp")

    def test_timestamp_without_timezone(self):
        self.approval["approved_at_utc"] = "2026-01-01T00:00:00"
        self.create_archive()
        self.assert_rejected("Approval timestamp must use UTC")

    def test_future_approval_timestamp(self):
        self.approval["approved_at_utc"] = "2099-01-01T00:00:00Z"
        self.create_archive()
        self.assert_rejected("Approval timestamp is in the future")


if __name__ == "__main__":
    unittest.main()
