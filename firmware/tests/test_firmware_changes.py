"""Verify which merged changes get an automatic firmware bump."""

import unittest

from firmware.scripts.firmware_changes import has_firmware_changes


class FirmwareChangeTests(unittest.TestCase):
    def test_firmware_build_inputs_count(self):
        for path in (
            "firmware/functiongenerator_web/src/main.cpp",
            "firmware/functiongenerator_web/include/wavegen_page.h",
            "firmware/functiongenerator_web/platformio.ini",
            "firmware/functiongenerator_esp32/functiongenerator_esp32.ino",
            "firmware/functiongenerator_esp32/AmplitudeControl.h",
            "firmware/functiongenerator_esp32/src/driver.cpp",
        ):
            with self.subTest(path=path):
                self.assertTrue(has_firmware_changes([[{"filename": path}]]))

    def test_docs_tests_automation_and_examples_do_not_count(self):
        paths = (
            "README.md",
            "documentation/Manuals/guide.docx",
            "firmware/functiongenerator_web/docs/bench_verification.md",
            "firmware/functiongenerator_web/tests/web_regression.cjs",
            "firmware/functiongenerator_esp32/README.md",
            "firmware/functiongenerator_esp32/examples/demo.ino",
            "firmware/ADCtomid_ESP32/ADCtomid_ESP32.ino",
            "hardware/functiongenerator.kicad_sch",
            ".github/workflows/bump-version.yml",
            "firmware/scripts/bump_version.py",
            "VERSION",
        )
        self.assertFalse(has_firmware_changes([[{"filename": path} for path in paths]]))

    def test_renamed_firmware_file_on_later_page_counts(self):
        self.assertTrue(has_firmware_changes([
            [{"filename": "README.md"}],
            [{
                "filename": "archive/old-driver.cpp",
                "previous_filename": "firmware/functiongenerator_web/src/old-driver.cpp",
            }],
        ]))

    def test_does_not_skip_when_github_caps_file_list(self):
        files = [{"filename": f"docs/page-{i}.md"} for i in range(3000)]
        with self.assertRaisesRegex(ValueError, "capped file list"):
            has_firmware_changes([files])
