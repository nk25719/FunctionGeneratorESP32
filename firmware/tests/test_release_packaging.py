import hashlib
import tempfile
import unittest

from pathlib import Path

from firmware.scripts.package_release import (
    TARGETS,
    sha256,
    release_notes,
    validate_builds,
)


class ReleasePackagingTests(unittest.TestCase):

    def test_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "firmware.bin"
            path.write_bytes(b"test firmware")

            self.assertEqual(
                sha256(path),
                hashlib.sha256(
                    b"test firmware"
                ).hexdigest()
            )

    def test_release_notes(self):
        changelog = (
            "# Changelog\n\n"
            "## [Unreleased]\n\n"
            "### Added\n"
            "- New waveform\n\n"
            "## [0.0.9]\n"
            "- Old change\n"
        )

        notes = release_notes(changelog)

        self.assertIn("New waveform", notes)
        self.assertNotIn("Old change", notes)

    def test_missing_unreleased(self):
        with self.assertRaises(ValueError):
            release_notes("# Changelog\n")

    def test_missing_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                validate_builds(Path(tmp))

    def test_complete_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            for target in TARGETS:
                directory = root / "firmware" / target
                directory.mkdir(parents=True)

                (directory / "firmware.bin").write_bytes(
                    b"test"
                )

            web = root / "firmware/web-esp32dev"

            for name in (
                "bootloader.bin",
                "partitions.bin"
            ):
                (web / name).write_bytes(b"test")

            validate_builds(root)

            (web / "bootloader.bin").unlink()

            with self.assertRaises(ValueError):
                validate_builds(root)
