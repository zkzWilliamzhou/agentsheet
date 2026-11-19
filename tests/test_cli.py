import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agentsheet.cli import EXIT_DRIFT, EXIT_OK, EXIT_USAGE_ERROR, main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        with open(os.path.join(self.repo, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("v1\n")
        self.sheet_path = os.path.join(self.tmp.name, "sheet.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_help_loads(self):
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, EXIT_OK)
        self.assertIn("agentsheet", out.getvalue())

    def test_generate_to_file_then_verify_clean(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["generate", self.repo, "-o", self.sheet_path])
        self.assertEqual(code, EXIT_OK)
        self.assertTrue(os.path.isfile(self.sheet_path))

        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["verify", self.repo, self.sheet_path])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("ADDED (0)", out.getvalue())
        self.assertIn("MODIFIED (0)", out.getvalue())

    def test_verify_detects_drift_and_exit_1(self):
        with redirect_stdout(io.StringIO()):
            main(["generate", self.repo, "-o", self.sheet_path])
        with open(os.path.join(self.repo, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("v2 changed\n")

        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["verify", self.repo, self.sheet_path])
        self.assertEqual(code, EXIT_DRIFT)
        self.assertIn("MODIFIED", out.getvalue())

    def test_diff_command(self):
        with redirect_stdout(io.StringIO()):
            main(["generate", self.repo, "-o", self.sheet_path])
        sheet_b = self.sheet_path + ".b"
        with open(os.path.join(self.repo, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("new\n")
        with redirect_stdout(io.StringIO()):
            main(["generate", self.repo, "-o", sheet_b])

        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["diff", self.sheet_path, sheet_b])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("ADDED", out.getvalue())

    def test_bad_repo_is_usage_error(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["generate", "/nonexistent/agentsheet/repo"])
        self.assertEqual(code, EXIT_USAGE_ERROR)
        self.assertIn("error", err.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
