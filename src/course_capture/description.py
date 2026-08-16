from __future__ import annotations

import json
import re
from pathlib import Path


TIMESTAMP = re.compile(r"^(?:(\d{1,2}):)?([0-5]?\d):([0-5]\d)$")


def timestamp_seconds(value: str) -> int:
    match = TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid chapter timestamp: {value}")
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def render_description(spec: dict[str, object]) -> str:
    title = str(spec.get("title", "")).strip()
    summary = str(spec.get("summary", "")).strip()
    chapters = spec.get("chapters", [])
    notes = spec.get("notes", [])
    if not title:
        raise ValueError("Description spec needs a title")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Description spec needs at least one chapter")

    chapter_lines = []
    previous = -1
    for chapter in chapters:
        if not isinstance(chapter, dict):
            raise ValueError("Each chapter must be an object")
        start = str(chapter.get("start", "")).strip()
        chapter_title = str(chapter.get("title", "")).strip()
        current = timestamp_seconds(start)
        if current <= previous:
            raise ValueError("Chapter timestamps must increase")
        if not chapter_title:
            raise ValueError("Each chapter needs a title")
        chapter_lines.append(f"{start} {chapter_title}")
        previous = current
    if timestamp_seconds(str(chapters[0].get("start", ""))) != 0:
        raise ValueError("The first chapter must start at 00:00")

    lines = [title]
    if summary:
        lines.extend(("", summary))
    lines.extend(("", "Chapters", *chapter_lines))
    if isinstance(notes, list) and notes:
        lines.extend(("", "Study notes", *(f"- {str(note).strip()}" for note in notes)))
    return "\n".join(lines).rstrip() + "\n"


def write_description(spec_path: Path, output: Path | None = None) -> Path:
    spec_path = spec_path.expanduser().resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    rendered = render_description(spec)
    output = output or spec_path.with_name(f"{spec_path.stem}-description.txt")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return output
