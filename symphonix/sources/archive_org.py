"""Archive.org source: the backbone - stable API, real public-domain audio files."""
import sys
import re
from urllib.parse import quote, urlparse
from urllib.request import urlopen

from ..track import Track
from .base import get_session, human_size

AUDIO_EXTS = (".mp3", ".ogg", ".oga", ".flac", ".m4a", ".wav", ".aac")

def search(query: str, composer: str = "", limit: int = 10, hifi: bool = False):
    q = []
    if query:
        q.append(f'(title:({query}) OR description:({query}))')
    if composer:
        q.append(f'creator:"{composer}"')
    q.append('mediatype:audio')
    if hifi:
        q.append('format:(FLAC OR "Lossless Audio")')
    qa = quote(" AND ".join(q))
    fields = ["identifier", "title", "creator", "year", "date", "downloads", "licenseurl"]
    fl = "&".join(f"fl[]={f}" for f in fields)
    url = (f"https://archive.org/advancedsearch.php?q={qa}&{fl}"
           f"&rows={min(max(limit, 1), 100)}&sort[]=downloads+desc&output=json")
    r = get_session().get(url, timeout=(6, 25))
    r.raise_for_status()
    data = r.json()
    tracks = []
    fallback_docs = []
    for doc in data.get("response", {}).get("docs", []):
        ident = doc.get("identifier", "")
        if not ident:
            continue
        title = doc.get("title") or ident
        creator = doc.get("creator") or ""
        if isinstance(creator, list):
            creator = "; ".join(creator)
        license_ = doc.get("licenseurl", "") or ""
        year = str(doc.get("year", "") or (doc.get("date", "") or "").split("-")[0])
        # resolve an actual audio file lazily-on-demand; but resolve one now
        files = list_audio_files(ident, hifi=hifi)
        if files:
            f = files[0]
            name = f["name"]
            ext = name.rsplit(".", 1)[-1].lower()
            if hifi and ext not in ("flac", "wav", "aiff"):
                fallback_docs.append(doc)     # keep as backup only
                continue
            dur = f.get("length", "")
            try:
                m, s2 = divmod(int(float(dur)), 60)
                dur = f"{m:02d}:{s2:02d}"
            except (TypeError, ValueError):
                dur = str(dur or "")
            tracks.append(Track(
                id=f"{ident}/{name}",
                url=f"https://archive.org/download/{quote(ident)}/{quote(name)}",
                title=f.get("nice_title", _strip_track_title(title, name)) or (title or ident),
                composer=(creator or ""),
                year=year, source="archive",
                ext=name.rsplit(".", 1)[-1].lower(),
                duration=str(dur),
                size=int(f.get("size", 0) or 0),
                license="Public Domain / CC" if not license_ else license_.replace("http://", "").replace("https://", ""),
                filename=name,
            ))
        if not files:
            tracks.append(Track(id=ident,
                                url=f"https://archive.org/details/{ident}",
                                title=title, composer="", performer=creator,
                                year=year, source="archive"))
    if hifi and not tracks:
        # no identifiers with lossless: retry same docs without the skip
        for doc in fallback_docs[: limit]:
            pass  # reuse the same loop by recursion-lite: fall through below
        for doc in fallback_docs[: limit]:
            ident = doc.get("identifier", "")
            if not ident:
                continue
            title = doc.get("title") or ident
            creator = doc.get("creator") or ""
            if isinstance(creator, list):
                creator = "; ".join(creator)
            year = str(doc.get("year", "") or (doc.get("date", "") or "").split("-")[0])
            files = list_audio_files(ident, hifi=False)
            if not files:
                continue
            f = files[0]
            name, ext = f["name"], f["name"].rsplit(".", 1)[-1].lower()
            dur = f.get("length", "")
            try:
                m, s2 = divmod(int(float(dur)), 60)
                dur = f"{m:02d}:{s2:02d}"
            except (TypeError, ValueError):
                dur = str(dur or "")
            tracks.append(Track(
                id=f"{ident}/{name}",
                url=f"https://archive.org/download/{quote(ident)}/{quote(name)}",
                title=f.get("nice_title", _strip_track_title(title, name)) or (title or ident),
                composer="", performer=creator,
                year=year, source="archive", ext=ext,
                duration=str(dur), size=int(f.get("size", 0) or 0),
                license="Public Domain / CC", filename=name,
            ))
    return tracks

def _strip_track_title(title, filename):
    """Show a nicer single-track title derived from file name when possible."""
    base = (filename or "").rsplit(".", 1)[0]
    if "-" in base and len(base) - len(title) > 4:
        parts = base.split("-", 2)
        base = parts[-1].strip()
    base = (base or title or "").replace("_", " ")
    base = re.sub(r"[\(\[]?full album[\)\]]?", "", base, flags=re.I)
    base = re.sub(r"onclassical.*", "", base, flags=re.I)
    base = re.sub(r"^\d{1,3}[\-\s\.]*(mp3)?[ \.]*", "", base)
    base = re.sub(r"[ \.]{2,}", " ", base).strip()
    if len(base) >= 6 and base.lower() != (title or "").lower():
        return base[:95].title()
    return (title or "").strip()[:95]

def list_audio_files(identifier: str, hifi: bool = False) -> "list[dict]":
    url = f"https://archive.org/metadata/{quote(identifier)}"
    r = get_session().get(url, timeout=(6, 25))
    r.raise_for_status()
    data = r.json()
    out = []
    for f in data.get("files", []):
        name = f.get("name", "")
        if not name.lower().endswith(AUDIO_EXTS):
            continue
        if any(bad in name.lower() for bad in ("sample", "conversationwith", "copyrightnotice")):
            continue
        f = dict(f)
        f["nice_title"] = _strip_track_title(f.get("title", "") or "", name)
        out.append(f)
    # special key to track total for ui
    if hifi:
        pref = {"flac": 0, "wav": 1, "aiff": 2, "m4a": 3, "aac": 3,
                "ogg": 4, "oga": 4, "mp3": 5}
    else:
        pref = {"mp3": 0, "flac": 1, "m4a": 2, "aac": 2, "ogg": 3, "oga": 3, "wav": 4}
    out.sort(key=lambda x: (pref.get(x.get("name", "").rsplit(".", 1)[-1].lower(), 9),
                            -int(x.get("size", 0) or 0)))
    return out

def probe_file(identifier: str) -> "list[dict]":
    return list_audio_files(identifier)

def normalize_url(u: str) -> "tuple[str, str] | None":
    """archive.org/details/XYZ -> identifier XYZ"""
    try:
        p = urlparse(u)
    except Exception:
        return None
    if "archive.org" in (p.netloc or ""):
        parts = [x for x in p.path.split("/") if x]
        if len(parts) >= 2:
            return parts[0], "/".join(parts[1:]) or ""  # (identifier/file-part)
    return None
