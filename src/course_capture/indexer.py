from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


KIND_ORDER = ("video", "slides", "transcript", "notes", "page", "assessment", "audio", "file")


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def render_index(manifest: dict[str, object]) -> str:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("Manifest assets must be a list")
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("Each manifest asset must be an object")
        groups[str(asset.get("kind", "file"))].append(asset)

    total_bytes = sum(int(asset.get("bytes", 0)) for asset in assets)
    lines = [
        f"# {manifest.get('root_name', 'Course')} Study Index",
        "",
        f"- Assets: {len(assets)}",
        f"- Size: {human_bytes(total_bytes)}",
        f"- Manifest generated: {manifest.get('generated_at', 'unknown')}",
        "",
        "Use this file as the course map. Add semantic summaries in your private notes.",
        "",
    ]

    ordered_kinds = [kind for kind in KIND_ORDER if groups.get(kind)]
    ordered_kinds.extend(sorted(set(groups) - set(ordered_kinds)))
    for kind in ordered_kinds:
        lines.extend((f"## {kind.title()}", ""))
        for asset in sorted(groups[kind], key=lambda item: str(item.get("path", ""))):
            path = str(asset.get("path", ""))
            size = human_bytes(int(asset.get("bytes", 0)))
            fingerprint = str(asset.get("sha256", ""))[:12]
            duration = asset.get("duration_seconds")
            detail = f"{size}; sha256 `{fingerprint}`"
            if duration is not None:
                detail += f"; {float(duration) / 60:.1f} min"
            lines.append(f"- `{path}` ({detail})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_index(manifest_path: Path, output: Path | None = None) -> Path:
    manifest_path = manifest_path.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if output is None:
        if manifest_path.parent.name == ".course-capture":
            output = manifest_path.parent.parent / "STUDY_INDEX.md"
        else:
            output = manifest_path.with_name("STUDY_INDEX.md")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_index(manifest), encoding="utf-8")
    return output
