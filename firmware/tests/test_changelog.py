import tempfile
import unittest
from pathlib import Path

from firmware.scripts.update_changelog import update


class ChangelogTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.path = self.root / "CHANGELOG.md"

        self.path.write_text(
            "# Changelog\n\n"
            "## [Unreleased]\n\n"
            "### Added\n\n"
            "### Changed\n\n"
            "### Fixed\n\n"
            "## [0.0.9]\n\n"
            "### Fixed\n"
            "- Previous change\n"
        )

    def record(self, pr, title, impact):
        return update(
            self.root,
            pr,
            title,
            impact,
            "test-user",
            "example/FunctionGeneratorESP32",
        )

    def test_feature(self):
        self.assertTrue(
            self.record(1, "feat: new waveform", "minor")
        )

        self.assertIn(
            "### Added\n- feat: new waveform",
            self.path.read_text()
        )

    def test_fix(self):
        self.record(2, "fix: DAC output", "patch")

        self.assertIn(
            "### Fixed\n- fix: DAC output",
            self.path.read_text()
        )

    def test_documentation(self):
        self.record(3, "docs: update manual", "none")

        self.assertIn(
            "### Changed\n- docs: update manual",
            self.path.read_text()
        )

    def test_duplicate_pr(self):
        self.record(4, "fix: output", "patch")
        before = self.path.read_text()

        self.assertFalse(
            self.record(4, "fix: output", "patch")
        )

        self.assertEqual(
            self.path.read_text(), before
        )

    def test_previous_release_preserved(self):
        self.record(5, "fix: output", "patch")

        self.assertIn(
            "## [0.0.9]\n\n"
            "### Fixed\n"
            "- Previous change\n",
            self.path.read_text()
        )

    def test_invalid_impact(self):
        before = self.path.read_text()

        with self.assertRaises(ValueError):
            self.record(6, "test", "invalid")

        self.assertEqual(
            self.path.read_text(), before
        )
