"""Robust download manager with progress, speed and resume."""
import os
import time
from importlib import import_module

import requests

from .config import cache_dir
from .track import Track
from .sources.base import get_session, human_size

def _dmod():
    return import_module("symphonix.downloader" if False else "symphonix.downloader")

def content_size(url: str) -> int:
    r = get_session().head(url, timeout=(6, 20), allow_redirects=True)
    try:
        r.raise_for_status()
    except Exception:
        return 0
    try:
        return int(r.headers.get("content-length") or 0)
    except (TypeError, ValueError):
        return 0

def stream_to_file(url: str, dest: str, on_progress=None,
                   chunk_size: int = 64 * 1024) -> str:
    """Download url to dest with resume support. Returns final path.
    on_progress(written_bytes, total_bytes_or_0, speed_Bps) called per chunk."""
    dest = os.path.expanduser(dest)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    resume_at = 0
    headers = {}
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        resume_at = os.path.getsize(dest)
        headers["Range"] = f"bytes={resume_at}-"
    total = content_size(url)
    if resume_at:
        total += resume_at
    s = get_session()
    with s.get(url, headers=headers, stream=True, timeout=(6, 60)) as r:
        r.raise_for_status()
        mode = "ab" if (resume_at and r.status_code == 206) else "wb"
        if mode == "wb" and total:
            total = int(r.headers.get("content-length") or total)
        speed_hist = []
        written = resume_at if mode == "ab" else 0
        with open(dest, mode) as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    t0 = time.time()
                    f.write(chunk)
                    dt = max(time.time() - t0, 0.0005)
                    written += len(chunk)
                    speed_hist.append(len(chunk) / dt)
                    if on_progress:
                        speed = sum(speed_hist[-12:]) / min(len(speed_hist), 12)
                        try:
                            on_progress(written, total or 0, speed)
                        except Exception:
                            pass
    return dest

def download_track(track: Track, dest_dir=None, on_progress=None) -> "str":
    """Download a Track (by url) into the symphonix cache (or given dir)."""
    if (track.url or "").startswith("http"):
        dest_dir = str(dest_dir or cache_dir())
        name = track.cache_path().name
        dest = os.path.join(dest_dir, name)
        return stream_to_file(track.url, dest, on_progress=None)
    if track.is_cached():
        return str(track.cache_path())
    return ""
