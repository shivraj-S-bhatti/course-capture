from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

from course_capture.canvas import export_course
from course_capture.captions import mux_subtitles
from course_capture.description import write_description
from course_capture.indexer import write_index
from course_capture.inventory import write_manifest
from course_capture.transcribe import DEFAULT_MODEL, transcribe_video
from course_capture.workspace import initialize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="course-capture",
        description="Build a private, searchable, captioned course workspace.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a private course workspace")
    init_parser.add_argument("directory", type=Path)

    canvas_parser = subparsers.add_parser("canvas", help="Export authorized Canvas files, pages, and modules")
    canvas_parser.add_argument("--base-url", required=True)
    canvas_parser.add_argument("--course-id", required=True)
    canvas_parser.add_argument("--out", required=True, type=Path)
    canvas_parser.add_argument("--token-env", default="CANVAS_TOKEN")

    inventory_parser = subparsers.add_parser("inventory", help="Hash and classify course files")
    inventory_parser.add_argument("directory", type=Path)
    inventory_parser.add_argument("--output", type=Path)
    inventory_parser.add_argument("--exclude", action="append", default=[])

    index_parser = subparsers.add_parser("index", help="Create a Markdown study index")
    index_parser.add_argument("manifest", type=Path)
    index_parser.add_argument("--output", type=Path)

    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe one video with MLX Whisper")
    transcribe_parser.add_argument("video", type=Path)
    transcribe_parser.add_argument("--out-dir", required=True, type=Path)
    transcribe_parser.add_argument("--model", default=DEFAULT_MODEL)
    transcribe_parser.add_argument("--force", action="store_true")
    transcribe_parser.add_argument("--verbose", action="store_true")

    caption_parser = subparsers.add_parser("caption", help="Add a toggleable SRT track to an MP4")
    caption_parser.add_argument("video", type=Path)
    caption_parser.add_argument("subtitles", type=Path)
    caption_parser.add_argument("--output", required=True, type=Path)
    caption_parser.add_argument("--force", action="store_true")

    description_parser = subparsers.add_parser("description", help="Build a reviewed video description")
    description_parser.add_argument("spec", type=Path)
    description_parser.add_argument("--output", type=Path)

    subparsers.add_parser("doctor", help="Check local runtime tools")
    return parser


def doctor() -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "mlx_whisper": importlib.util.find_spec("mlx_whisper") is not None,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            created = initialize(args.directory)
            print(f"workspace: {args.directory.expanduser().resolve()}")
            print(f"created: {len(created)} paths")
        elif args.command == "canvas":
            counts = export_course(args.base_url, args.course_id, args.out, args.token_env)
            print(json.dumps(counts, indent=2))
        elif args.command == "inventory":
            output = write_manifest(args.directory, args.output, set(args.exclude))
            print(f"manifest: {output}")
        elif args.command == "index":
            output = write_index(args.manifest, args.output)
            print(f"study index: {output}")
        elif args.command == "transcribe":
            outputs = transcribe_video(
                args.video,
                args.out_dir,
                model=args.model,
                force=args.force,
                verbose=args.verbose,
            )
            for output in outputs:
                print(output)
        elif args.command == "caption":
            print(mux_subtitles(args.video, args.subtitles, args.output, args.force))
        elif args.command == "description":
            print(write_description(args.spec, args.output))
        elif args.command == "doctor":
            print(json.dumps(doctor(), indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
