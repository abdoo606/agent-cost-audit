import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from costaudit.cli import main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "steps.json"


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(argv)
        return code, out.getvalue()

    def test_markdown_report(self):
        code, out = self.run_cli(["audit", "--logs", str(SAMPLE)])
        self.assertEqual(code, 0)
        self.assertIn("Agent cost audit", out)
        self.assertIn("Failures by tool", out)
        self.assertIn("Where the money went", out)

    def test_json_report(self):
        code, out = self.run_cli(["audit", "--logs", str(SAMPLE), "--json"])
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["total_steps"], 10)
        self.assertEqual(len(payload["tasks"]), 3)
        self.assertEqual(payload["failures_by_tool"]["bash"], 2)

    def test_over_budget_exits_one(self):
        code, out = self.run_cli(["audit", "--logs", str(SAMPLE), "--budget", "0.001"])
        self.assertEqual(code, 1)
        self.assertIn("OVER BUDGET", out)

    def test_bad_logs_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text('[{"task_id": "t", "model": "nope"}]', encoding="utf-8")
            code, _ = self.run_cli(["audit", "--logs", str(bad)])
            self.assertEqual(code, 2)
