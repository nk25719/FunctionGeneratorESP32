import unittest

from firmware.scripts.version_impact import select_impact


class VersionImpactTests(unittest.TestCase):

    def test_major(self):
        self.assertEqual(
            select_impact(["version:major"]), "major"
        )

    def test_minor(self):
        self.assertEqual(
            select_impact(["version:minor"]), "minor"
        )

    def test_patch(self):
        self.assertEqual(
            select_impact(["version:patch"]), "patch"
        )

    def test_none(self):
        self.assertEqual(
            select_impact(["version:none"]), "none"
        )

    def test_missing_label(self):
        with self.assertRaises(ValueError):
            select_impact(["documentation"])

    def test_conflicting_labels(self):
        with self.assertRaises(ValueError):
            select_impact([
                "version:major",
                "version:patch"
            ])
