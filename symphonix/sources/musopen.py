"""Musopen source - best-effort scrape of royalty-free recordings."""
import re
from ..track import Track
from .base import get_session, UA

def search(query: str, limit: int = 10) -> "list[Track]":
    """Try Musopen's search pages; degrade gracefully if the site changes."""
    out = []
    url = "https://musopen.org/music/search/"
    try:
        r = get_session().get(
            url,
            params={"q": query, "type": "track", "page": 1},
            timeout=(6, 20),
            headers={"User-Agent": UA, "Referer": "https://musopen.org/"},
        )
        r.raise_for_status()
        html = r.text
        # recordings look like: <a href=".../music/track-name/nextpage"?> ... <audio src="...mp3">
        rows = re.findall(
            r'href="(/music/[^"#]{8,120})"[^>]{0,300}?class="?[^"]*"?>\s*([^<]{4,90})\s*(?:</a>)?',
            html, flags=re.I | re.S)
        for href, label in rows[:limit]:
            title = re.sub(r"\s+", " ", label).strip("&;").strip()
            if len(title) < 4:
                continue
            out.append(Track(
                id=f"musopen:{href}",
                url="https://musopen.org" + href,
                title=title[:95],
                source="musopen",
                ext="mp3",
            ))
        # direct mp3s embedded in the page
        for m in re.finditer(r'(https?://[^"\']+\.mp3)', html, flags=re.I):
            u = m.group(1)
            if any(x in u for x in ("javascript", "template")):
                continue
            name = u.rsplit("/", 1)[-1]
            out.append(Track(id=f"musopen:{u}", url=u, title=name[:95],
                             source="musopen", ext="mp3"))
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out
