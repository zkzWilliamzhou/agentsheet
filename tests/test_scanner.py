import os
import tempfile
import unittest

from agentsheet.scanner import discover, hash_file, snapshot


class ScannerTests(unittest.TestCase):
    def test_discovers_known_agent_files(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, ".github"))
            os.makedirs(os.path.join(root, ".workbuddy"))
            os.makedirs(os.path.join(root, "src"))
            for rel in ("CLAUDE.md", "AGENTS.md", ".cursorrules",
                        ".github/copilot-instructions.md", ".workbuddy/config.json",
                        "README.md", "src/main.py"):
                with open(os.path.join(root, *rel.split("/")), "w", encoding="utf-8") as handle:
                    handle.write(rel)
            found = discover(root)
            self.assertIn("CLAUDE.md", found)
            self.assertIn("AGENTS.md", found)
            self.assertIn(".cursorrules", found)
            self.assertIn(".github/copilot-instructions.md", found)
            self.assertIn(".workbuddy/config.json", found)
            self.assertNotIn("README.md", found)
            self.assertNotIn("src/main.py", found)

    def test_skill_folder_files_are_discovered(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "skills", "demo", "scripts"))
            with open(os.path.join(root, "skills", "demo", "SKILL.md"), "w") as handle:
                handle.write("---\nname: demo\n---\n")
            with open(os.path.join(root, "skills", "demo", "scripts", "run.py"), "w") as handle:
                handle.write("print('hi')\n")
            found = discover(root)
            self.assertIn("skills/demo/SKILL.md", found)
            self.assertIn("skills/demo/scripts/run.py", found)

    def test_hash_file_is_sha256_and_size(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "f.txt")
            with open(path, "wb") as handle:
                handle.write(b"abc")
            digest, size = hash_file(path)
            self.assertEqual(
                digest,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            self.assertEqual(size, 3)

    def test_snapshot_is_sorted(self):
        with tempfile.TemporaryDirectory() as root:
            for rel in ("AGENTS.md", "CLAUDE.md", ".cursorrules"):
                with open(os.path.join(root, rel), "w") as handle:
                    handle.write(rel)
            snapshot_result = snapshot(root)
            self.assertEqual(list(snapshot_result), sorted(snapshot_result))


if __name__ == "__main__":
    unittest.main()
