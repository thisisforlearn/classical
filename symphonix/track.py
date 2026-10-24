from pathlib import Path
from typing import Optional

class Track:
    """A single playable/downloadable public-domain recording."""
    def __init__(self, id: str, url: str, title: str, composer: str = "",
                 performer: str = "", year: str = "", source: str = "archive",
                 ext: str = "mp3", duration: str = "", size: int = 0,
                 license: str = "", filename: str = ""):
        self.id = id                      # stable id (archive identifier, musopen id...)
        self.url = url                    # direct audio URL
        self.title = title
        self.composer = composer
        self.performer = performer
        self.year = year
        self.source = source              # archive | musopen | imslp | local
        self.ext = ext or "mp3"
        self.duration = duration
        self.size = size
        self.license = license
        self.filename = filename          # for local/cached tracks

    # -------------------------------------------------------------------
    @property
    def label(self) -> str:
        comp = f" - {self.composer}" if self.composer else ""
        perf = f" - {self.performer}" if self.performer and self.performer != self.composer else ""
        return f"{self.title}{comp}{perf}"

    def display(self) -> str:
        bits = [self.title or self.id]
        who = [self.composer or "", self.performer or ""] if self.performer != self.composer else [self.composer or ""]
        sub = ", ".join(x for x in who if x)
        if self.year:
            sub += (", " if sub else "") + self.year
        if sub:
            bits.append(sub)
        return " | ".join(bits)

    def guess_composer_key(self):
        from .art import match_composer
        text = f"{self.composer} {self.title}"
        return match_composer(text)

    def cache_path(self) -> Path:
        from .config import cache_dir
        safe = "".join(c if c not in '\\/:*?"<>|' else "_" for c in self.label)[:120].strip()
        return cache_dir() / f"{safe or self.id}.{self.ext}"

    def is_cached(self) -> bool:
        return self.cache_path().exists() and self.cache_path().stat().st_size > 0

    # -------------------------------------------------------------------
    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "Track":
        d = dict(d)
        known = {f for f in cls.__init__.__code__.co_varnames if f != "self"}
        return cls(**{k: v for k, v in d.items() if k in known})

def unique(tracks: list[Track]) -> list[Track]:
    seen, out = set(), []
    for t in tracks:
        key = (t.title or "").lower().strip(), (t.composer or "").lower().strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out
