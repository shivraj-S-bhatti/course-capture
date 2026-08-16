from __future__ import annotations

import html
import json
from pathlib import Path


DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def format_timestamp(seconds: float, decimal: str = ",") -> str:
    total_ms = max(0, round(float(seconds) * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02}{decimal}{milliseconds:03}"


def normalize_segments(result: dict[str, object]) -> list[dict[str, object]]:
    normalized = []
    for segment in result.get("segments", []) or []:
        text = html.unescape(str(segment.get("text", "")).strip())
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", 0.0))
        if text and end > start:
            normalized.append({"start": start, "end": end, "text": text})
    return normalized


def write_transcript_outputs(segments: list[dict[str, object]], base: Path) -> list[Path]:
    base.parent.mkdir(parents=True, exist_ok=True)
    plain_text = " ".join(str(segment["text"]) for segment in segments)

    txt_path = base.with_suffix(".txt")
    txt_path.write_text(plain_text + "\n", encoding="utf-8")

    srt_path = base.with_suffix(".srt")
    with srt_path.open("w", encoding="utf-8") as handle:
        for number, segment in enumerate(segments, 1):
            handle.write(
                f"{number}\n"
                f"{format_timestamp(float(segment['start']))} --> "
                f"{format_timestamp(float(segment['end']))}\n"
                f"{segment['text']}\n\n"
            )

    json_path = base.with_suffix(".json")
    json_path.write_text(json.dumps({"segments": segments}, indent=2) + "\n", encoding="utf-8")
    return [txt_path, srt_path, json_path]


def transcribe_video(
    video: Path,
    out_dir: Path,
    model: str = DEFAULT_MODEL,
    force: bool = False,
    verbose: bool = False,
) -> list[Path]:
    video = video.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if not video.is_file():
        raise ValueError(f"Video does not exist: {video}")
    base = out_dir / video.stem
    outputs = [base.with_suffix(suffix) for suffix in (".txt", ".srt", ".json")]
    if any(path.exists() for path in outputs) and not force:
        raise FileExistsError(f"Transcript output exists for {video.name}; use --force to replace it")

    try:
        import mlx_whisper
    except ImportError as error:
        raise RuntimeError("MLX Whisper is not installed. Run: python -m pip install -e '.[mlx]'") from error

    result = mlx_whisper.transcribe(
        str(video),
        path_or_hf_repo=model,
        verbose=verbose,
        word_timestamps=False,
        condition_on_previous_text=True,
    )
    return write_transcript_outputs(normalize_segments(result), base)
