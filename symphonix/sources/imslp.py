"""IMSLP source - MediaWiki API search + recording mp3 extraction."""
import re
from urllib.parse import quote
from ..track import Track
from .base import get_session, UA

def search(query: str, limit: int = 8) -> "list[Track]":
    s = get_session()
    s.cookies.set("imslpdisclaimeraccepted", "yes", domain="imslp.org")
    s.cookies.set("imslp_wikiLanguageSelectorLanguage", "en", domain="imslp.org")
    out = []
    try:
        api = ("https://imslp.org/api.php?action=query&format=json&list=search"
               f"&srsearch={quote(query)}&srlimit={min(limit, 50)}")
        r = s.get(api, timeout=(6, 20), headers={"User-Agent": UA})
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        for hit in hits[:limit]:
            title = hit.get("title", "")
            page_url = f"https://imslp.org/wiki/{quote(title.replace(' ', '_'))}"
            r2 = s.get(page_url, timeout=(6, 20), headers={"User-Agent": UA})
            if r2.status_code != 200:
                continue
            html = r2.text
            mp3s = {m.group(1) for m in re.finditer(r'https?://[^\s\'"]+?\.mp3[^\'" ]*', html, flags=re.I)}
            for u in list(mp3s)[:2]:
                fname = u.rsplit("/", 1)[-1]
                out.append(Track(id=f"imslp:{u}", url=u, title=f"{fname[:70]} (IMSLP rec.)",
                                 composer=title.replace("Category:", "").split(":")[0] if title.startswith(("Category",)) else "",
                                 source="imslp", ext="mp3"))
    except Exception:
        pass
    return out
