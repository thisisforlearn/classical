"""Shared HTTP plumbing for all music sources."""
import functools
import requests

UA = "symphonix/1.0 (+https://github.com/thisisforlearn/classical)"

HEADERS = {"User-Agent": UA, "Accept": "application/json,text/html;q=0.8,*/*;q=0.5"}

_SESSION = None

def get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        s.headers.update(HEADERS)
        _SESSION = s
    return _SESSION

def human_size(n) -> str:
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"

def human_dur(sec) -> str:
    try:
        sec = int(float(sec))
    except (TypeError, ValueError):
        return ""
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"
