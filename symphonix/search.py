"""Unified search across all sources, with lazy file resolution."""
import concurrent.futures as cf
from importlib import import_module
from .track import Track, unique

def _mod(name):
    return import_module(f"symphonix.sources.{name}")

def search(query: str = "", composer: str = "", limit: int = 10,
           which: str = "all") -> "list[Track]":
    """Search public-domain sources. which: all|archive|musopen|imslp"""
    if which in ("archive", "archive_org"):
        return _mod("archive_org").search(query, composer, limit)
    if which == "musopen":
        return _mod("musopen").search(query, limit)
    if which == "imslp":
        return _mod("imslp").search(query, limit)

    jobs = {}
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        jobs[ex.submit(_mod("archive_org").search, query, composer, limit)] = "archive"
        jobs[ex.submit(_mod("musopen").search, query, limit)] = "musopen"
        jobs[ex.submit(_mod("imslp").search, query, 5)] = "imslp"
        res = {"archive": [], "musopen": [], "imslp": []}
        for fut in cf.as_completed(jobs, timeout=45):
            src = jobs[fut]
            try:
                res[src] = fut.result()
            except Exception:
                res[src] = []
    return unique(res["archive"] + res["musopen"] + res["imslp"])[: max(limit * 2, 12)]
