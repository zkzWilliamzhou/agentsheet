import os
import tempfile
import unittest

from agentsheet.sheet import (
    SheetError,
    build_sheet,
    compare,
    has_drift,
    parse_sheet,
    render_json,
    verify,
)


class SheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        with open(os.path.join(self.repo, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("agent instructions v1\n")
        with open(os.path.join(self.repo, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("shared instructions\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_sheet_deterministic_no_timestamp(self):
        a = render_json(build_sheet(self.repo))
        b = render_json(build_sheet(self.repo))
        self.assertEqual(a, b)
        self.assertNotIn("generated_at", a)

    def test_with_timestamp_adds_field(self):
        sheet = build_sheet(self.repo, with_timestamp=True)
        self.assertIn("generated_at", sheet)

    def test_json_is_sorted(self):
        text = render_json(build_sheet(self.repo))
        self.assertEqual(text.strip(), __import__("json").dumps(__import__("json").loads(text), indent=2, sort_keys=True, ensure_ascii=False).strip())

    def test_verify_clean(self):
        sheet = build_sheet(self.repo)
        self.assertFalse(has_drift(verify(self.repo, sheet)))

    def test_verify_detects_modified_added_removed(self):
        sheet = build_sheet(self.repo)

        # modify one file, add one, remove one
        with open(os.path.join(self.repo, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("agent instructions v2 - changed\n")
        with open(os.path.join(self.repo, ".cursorrules"), "w", encoding="utf-8") as handle:
            handle.write("rule\n")
        os.remove(os.path.join(self.repo, "AGENTS.md"))

        delta = verify(self.repo, sheet)
        self.assertEqual(delta["modified"], ["CLAUDE.md"])
        self.assertEqual(delta["added"], [".cursorrules"])
        self.assertEqual(delta["removed"], ["AGENTS.md"])
        self.assertTrue(has_drift(delta))

    def test_parse_sheet_rejects_bad_input(self):
        with self.assertRaises(SheetError):
            parse_sheet("not json")
        with self.assertRaises(SheetError):
            parse_sheet('{"schema_version": 1}')  # no files object

    def test_compare_two_sheets(self):
        sheet_a = build_sheet(self.repo)
        with open(os.path.join(self.repo, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("changed\n")
        sheet_b = build_sheet(self.repo)
        delta = compare(sheet_a, sheet_b)
        self.assertEqual(delta["modified"], ["CLAUDE.md"])
        self.assertFalse(delta["added"])
        self.assertFalse(delta["removed"])


if __name__ == "__main__":
    unittest.main()
