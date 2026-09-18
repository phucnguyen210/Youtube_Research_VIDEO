"""Content-addressed cache for AI background images."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from threading import Lock

_CACHE_LOCK = Lock()


def cache_key(prompt: str, model: str, quality: str, size: str, style_id: str) -> str:
    normalized=" ".join(prompt.split()).lower()
    payload=json.dumps([normalized,model,quality,size,style_id],ensure_ascii=False,separators=(",",":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_or_generate(cache_dir: Path, output_path: Path, prompt: str, model: str,
                    quality: str, size: str, style_id: str, generator) -> bool:
    """Return True only when the provider was called; cache hits copy existing art."""
    cache_dir.mkdir(parents=True,exist_ok=True)
    cached=cache_dir/f"{cache_key(prompt,model,quality,size,style_id)}.png"
    with _CACHE_LOCK:
        if cached.is_file() and cached.stat().st_size>0:
            shutil.copy2(cached,output_path)
            return False
        temporary=cached.with_suffix(".tmp.png")
        try:
            generator(temporary)
            if not temporary.is_file() or temporary.stat().st_size==0:
                raise RuntimeError("Image provider wrote an empty image")
            temporary.replace(cached)
            shutil.copy2(cached,output_path)
        finally:
            temporary.unlink(missing_ok=True)
        return True
