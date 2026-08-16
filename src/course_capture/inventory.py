from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


IGNORED_DIRS = {".course-capture", ".git", ".venv", "__pycache__"}
IGNORED_FILES = {".DS_Store", ".gitignore", "STUDY_INDEX.md", "Thumbs.db"}

VIDEO_EXTENSIONS = {".mkv", ".mov", ".mp4", ".webm"}
AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}
TRANSCRIPT_EXTENSIONS = {".srt", ".vtt"}
SLIDE_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".key"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    suffix = path.suffix.lower()

    if parts & {"transcript", "transcripts", "caption", "captions"}:
        return "transcript"
    if parts & {"video", "videos"} or suffix in VIDEO_EXTENSIONS:
        return "video"
    if parts & {"audio"} or suffix in AUDIO_EXTENSIONS:
        return "audio"
    if parts & {"assignment", "assignments", "homework", "quiz", "quizzes", "exam", "exams"}:
        return "assessment"
    if parts & {"slide", "slides"} or suffix in SLIDE_EXTENSIONS:
        return "slides"
    if suffix in TRANSCRIPT_EXTENSIONS:
        return "transcript"
    if parts & {"note", "notes"} or suffix == ".md":
        return "notes"
    if parts & {"page", "pages"} or suffix in {".htm", ".html"}:
        return "page"
    return "file"


def probe_media(path: Path) -> dict[str, object]:
    if not shutil.which("ffprobe"):
        return {}
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        raw = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}

    details: dict[str, object] = {}
    duration = raw.get("format", {}).get("duration")
    if duration is not None:
        details["duration_seconds"] = round(float(duration), 3)
    streams = [
        {"type": stream.get("codec_type"), "codec": stream.get("codec_name")}
        for stream in raw.get("streams", [])
    ]
    if streams:
        details["streams"] = streams
    return details


def iter_files(root: Path, excludes: set[str] | None = None):
    excluded = IGNORED_DIRS | (excludes or set())
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if path.name in IGNORED_FILES:
            continue
        if path.is_file() and not path.is_symlink():
            yield path, relative


def build_manifest(root: Path, excludes: set[str] | None = None) -> dict[str, object]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Course directory does not exist: {root}")

    assets = []
    for path, relative in iter_files(root, excludes):
        kind = classify(relative)
        asset: dict[str, object] = {
            "path": relative.as_posix(),
            "kind": kind,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        }
        if kind in {"audio", "video"}:
            asset.update(probe_media(path))
        assets.append(asset)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_name": root.name,
        "asset_count": len(assets),
        "assets": assets,
    }


def write_manifest(
    root: Path,
    output: Path | None = None,
    excludes: set[str] | None = None,
) -> Path:
    root = root.expanduser().resolve()
    output = output or root / ".course-capture" / "manifest.json"
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(root, excludes)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output
