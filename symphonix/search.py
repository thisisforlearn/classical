"""Unified search across all sources, with lazy file resolution."""
import concurrent.futures as cf
from importlib import import_module
from .track import Track, unique

def _mod(name):
    return import_module(f"symphonix.sources.{name}")

_CACHE = {}
_MAX_CACHED = 96


def search(query: str = "", composer: str = "", limit: int = 10,
           which: str = "all", hifi: bool = False) -> "list[Track]":
    """Search public-domain sources. which: all|archive|musopen|imslp

    hifi=True prefers lossless (flac/wav) file versions.
    Results are cached per process (menus feel instant)."""
    ckey = (query, composer, limit, which, bool(hifi))
    hit = _CACHE.get(ckey)
    if hit is not None:
        return list(hit)

    if which in ("archive", "archive_org"):
        out = _mod("archive_org").search(query, composer, limit, hifi=hifi)
    elif which == "musopen":
        out = _mod("musopen").search(query, limit)
    elif which == "imslp":
        out = _mod("imslp").search(query, limit)
    elif which == "all":
        jobs = {}
        with cf.ThreadPoolExecutor(max_workers=3) as ex:
            jobs[ex.submit(_mod("archive_org").search, query, composer,
                           limit, hifi)] = "archive"
            jobs[ex.submit(_mod("musopen").search, query, limit)] = "musopen"
            jobs[ex.submit(_mod("imslp").search, query, 5)] = "imslp"
            res = {"archive": [], "musopen": [], "imslp": []}
            for fut in cf.as_completed(jobs, timeout=18):
                src = jobs[fut]
                try:
                    res[src] = fut.result()
                except Exception:
                    res[src] = []
        out = unique(res["archive"] + res["musopen"] + res["imslp"])[: max(limit * 2, 12)]
    else:
        raise ValueError(f"unknown source: {which}")

    if len(_CACHE) > _MAX_CACHED:
        _CACHE.clear()
    _CACHE[ckey] = list(out)
    return list(out)
