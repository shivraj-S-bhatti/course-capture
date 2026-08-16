import tempfile
import unittest
from pathlib import Path

from course_capture.inventory import build_manifest, classify, sha256_file


class InventoryTests(unittest.TestCase):
    def test_classifies_assets_from_path_and_extension(self):
        self.assertEqual(classify(Path("incoming/videos/lecture-01.mp4")), "video")
        self.assertEqual(classify(Path("derived/transcripts/lecture-01.txt")), "transcript")
        self.assertEqual(classify(Path("incoming/homework/hw-01.pdf")), "assessment")
        self.assertEqual(classify(Path("incoming/slides/week-01.pdf")), "slides")

    def test_builds_relative_manifest_and_ignores_internal_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            notes = root / "incoming" / "notes"
            notes.mkdir(parents=True)
            (notes / "lecture-01.md").write_text("hello\n", encoding="utf-8")
            internal = root / ".course-capture"
            internal.mkdir()
            (internal / "manifest.json").write_text("{}", encoding="utf-8")
            (root / ".gitignore").write_text("incoming/\n", encoding="utf-8")
            (root / "STUDY_INDEX.md").write_text("generated\n", encoding="utf-8")

            manifest = build_manifest(root)

            self.assertEqual(manifest["asset_count"], 1)
            asset = manifest["assets"][0]
            self.assertEqual(asset["path"], "incoming/notes/lecture-01.md")
            self.assertEqual(asset["sha256"], sha256_file(notes / "lecture-01.md"))
            self.assertNotIn(str(root), asset["path"])


if __name__ == "__main__":
    unittest.main()
