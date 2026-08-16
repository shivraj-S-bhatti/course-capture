import tempfile
import unittest
from pathlib import Path

from course_capture.workspace import initialize


class WorkspaceTests(unittest.TestCase):
    def test_initialize_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "course"
            first = initialize(root)
            second = initialize(root)
            self.assertTrue(first)
            self.assertEqual(second, [])
            self.assertTrue((root / "incoming" / "videos").is_dir())
            self.assertTrue((root / ".course-capture" / "config.json").is_file())
            self.assertIn("incoming/", (root / ".gitignore").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
