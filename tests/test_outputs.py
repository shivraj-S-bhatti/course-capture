import json
import tempfile
import unittest
from pathlib import Path

from course_capture.canvas import CanvasClient, parse_links, safe_name, same_origin
from course_capture.description import render_description, timestamp_seconds
from course_capture.indexer import render_index
from course_capture.transcribe import format_timestamp, write_transcript_outputs


class OutputTests(unittest.TestCase):
    def test_renders_study_index(self):
        manifest = {
            "root_name": "demo-course",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "assets": [
                {
                    "path": "incoming/slides/week-01.pdf",
                    "kind": "slides",
                    "bytes": 2048,
                    "sha256": "a" * 64,
                }
            ],
        }
        rendered = render_index(manifest)
        self.assertIn("# demo-course Study Index", rendered)
        self.assertIn("## Slides", rendered)
        self.assertIn("2.0 KB", rendered)

    def test_renders_reviewed_description(self):
        spec = {
            "title": "Lecture 1",
            "summary": "Synthetic summary.",
            "chapters": [
                {"start": "00:00", "title": "Start"},
                {"start": "02:30", "title": "Example"},
            ],
        }
        rendered = render_description(spec)
        self.assertIn("00:00 Start", rendered)
        self.assertEqual(timestamp_seconds("1:02:03"), 3723)

    def test_rejects_nonzero_first_chapter(self):
        with self.assertRaises(ValueError):
            render_description(
                {
                    "title": "Lecture 1",
                    "chapters": [{"start": "00:10", "title": "Late start"}],
                }
            )

    def test_writes_transcript_formats(self):
        segments = [{"start": 1.25, "end": 3.5, "text": "A & B"}]
        with tempfile.TemporaryDirectory() as directory:
            outputs = write_transcript_outputs(segments, Path(directory) / "lecture-01")
            self.assertEqual(format_timestamp(1.25), "00:00:01,250")
            self.assertIn("A & B", outputs[0].read_text(encoding="utf-8"))
            self.assertIn("00:00:01,250 --> 00:00:03,500", outputs[1].read_text(encoding="utf-8"))
            payload = json.loads(outputs[2].read_text(encoding="utf-8"))
            self.assertEqual(payload["segments"][0]["text"], "A & B")

    def test_canvas_helpers(self):
        links = parse_links('<https://example.test?page=2>; rel="next", <https://example.test?page=9>; rel="last"')
        self.assertEqual(links["next"], "https://example.test?page=2")
        self.assertEqual(safe_name("../Week 1 / Intro"), "Week-1---Intro")
        self.assertTrue(same_origin("https://canvas.test/a", "https://canvas.test/b"))
        self.assertFalse(same_origin("https://canvas.test/a", "https://storage.test/b"))
        client = CanvasClient("https://canvas.test", "secret")
        self.assertIn("Authorization", client.headers_for("https://canvas.test/api/v1/courses"))
        self.assertNotIn("Authorization", client.headers_for("https://storage.test/signed-file"))


if __name__ == "__main__":
    unittest.main()
