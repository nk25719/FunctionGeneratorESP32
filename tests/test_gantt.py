"""Regression checks for the issue-field Gantt renderer."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_gantt.py"
spec = importlib.util.spec_from_file_location("generate_gantt", SCRIPT)
gantt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gantt)


class GanttTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_output = gantt.OUTPUT
        gantt.OUTPUT = Path(self.tmp.name) / "GANTT.md"

    def tearDown(self):
        gantt.OUTPUT = self.old_output
        self.tmp.cleanup()

    def test_issue_field_schedule_inclusive_dates(self):
        issues = [{
            "number": 19,
            "title": "Oscilloscope Vertical Axis should be in Volts",
            "state": "open",
            "body": "",
        }]
        with patch.object(gantt, "fetch_issue_field_dates", return_value={
            "start date": "2026-11-22",
            "target date": "2026-11-25",
        }):
            gantt.create_chart(issues)
        output = gantt.OUTPUT.read_text()
        self.assertIn("issue19, 2026-11-22, 4d", output)
        self.assertIn("tickInterval 1day", output)
        self.assertIn("| 2026-11-22 | 2026-11-25 | open |", output)

    def test_missing_dates_are_unscheduled(self):
        issues = [{"number": 5, "title": "No dates", "state": "open", "body": ""}]
        with patch.object(gantt, "fetch_issue_field_dates", return_value={}):
            gantt.create_chart(issues)
        output = gantt.OUTPUT.read_text()
        self.assertIn("## Issues without valid scheduled dates", output)
        self.assertIn("[#5", output)
        self.assertNotIn("issue5,", output)


if __name__ == "__main__":
    unittest.main()
