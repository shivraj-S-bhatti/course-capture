from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def mux_subtitles(video: Path, subtitles: Path, output: Path, force: bool = False) -> Path:
    video = video.expanduser().resolve()
    subtitles = subtitles.expanduser().resolve()
    output = output.expanduser().resolve()
    if not video.is_file():
        raise ValueError(f"Video does not exist: {video}")
    if not subtitles.is_file():
        raise ValueError(f"Subtitle file does not exist: {subtitles}")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is not installed or is not on PATH")
    if output.exists() and not force:
        raise FileExistsError(f"Output exists; use --force to replace it: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y" if force else "-n",
        "-i",
        str(video),
        "-i",
        str(subtitles),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-map",
        "1:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-c:s",
        "mov_text",
        "-metadata:s:s:0",
        "language=eng",
        "-metadata:s:s:0",
        "handler_name=English subtitles",
        "-disposition:s:0",
        "default",
        str(output),
    ]
    subprocess.run(command, check=True)
    return output
