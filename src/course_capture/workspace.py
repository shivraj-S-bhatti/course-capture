from __future__ import annotations

import json
from pathlib import Path


WORKSPACE_DIRS = (
    "incoming/files",
    "incoming/pages",
    "incoming/slides",
    "incoming/videos",
    "derived/captions",
    "derived/descriptions",
    "derived/transcripts",
    "notes",
    ".course-capture",
)


def initialize(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    created: list[Path] = []
    for relative in WORKSPACE_DIRS:
        path = root / relative
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)

    config = root / ".course-capture" / "config.json"
    if not config.exists():
        config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "course": root.name,
                    "private_workspace": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        created.append(config)

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# Private course material\n"
            "incoming/\n"
            "derived/\n"
            "notes/\n"
            ".course-capture/\n"
            "STUDY_INDEX.md\n",
            encoding="utf-8",
        )
        created.append(gitignore)

    return created
