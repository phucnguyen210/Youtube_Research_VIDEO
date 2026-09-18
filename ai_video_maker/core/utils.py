from __future__ import annotations
import json
import re
import subprocess
import wave
from pathlib import Path
from typing import Any
import imageio_ffmpeg


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start_candidates = [i for i in (text.find("{"), text.find("[")) if i >= 0]
        if not start_candidates:
            raise
        start = min(start_candidates)
        for end in range(len(text), start, -1):
            chunk = text[start:end]
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                continue
        raise


def media_duration(path: Path) -> float:
    """Get media duration robustly.

    OpenAI streaming WAV files can use RF64/placeholder size fields that Python's wave
    module may interpret as a huge number of frames. FFmpeg parses the real duration,
    so use it first and only fall back to wave for conventional WAV files.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr or "")
    if match:
        h, m, s = match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)
        if 0 < duration < 6 * 3600:
            return duration

    try:
        with wave.open(str(path), "rb") as wf:
            duration = wf.getnframes() / float(wf.getframerate())
            if 0 < duration < 6 * 3600:
                return duration
    except Exception:
        pass
    raise RuntimeError(f"Không đọc được thời lượng audio hợp lệ: {path}")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    return value[:80] or "project"
