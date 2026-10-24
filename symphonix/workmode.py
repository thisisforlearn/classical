"""Work focus mode: endless classical playing pulled from the canon.

- Prefetches all recommended queries in parallel so the first track starts fast
- Loops forever (reshuffled each pass, no instant repeats)
- Ctrl+C once: skip · twice fast: quit (or 'q' during playback)
"""
import random
import threading
import time

from .masterpieces import RECOMMENDED


def canon_queries():
    out = []
    for key, work, squery in RECOMMENDED:
        out.append({
            "key": key, "work": work, "query": squery or work,
        })
    return out


def prefetch(timeout_cap=25.0):
    """Search each cornerstone once, in parallel. Returns [Track] in canon order."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .search import search as do_search
    jobs = {}
    plan = canon_queries()
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for item in plan:
            jobs[ex.submit(do_search, item["query"], "", 5,
                           "archive")] = item
        for fut in as_completed(jobs, timeout=timeout_cap):
            item = jobs[fut]
            try:
                results.append((plan.index(item), item, fut.result()))
            except Exception:
                results.append((plan.index(item), item, []))
    tsorted = []
    for _, plan_item, tracks in sorted(results,
                                       key=lambda r: r[0]):
        good = None
        try:
            from .scoring import best_track
            good = best_track(tracks, plan_item["work"])
        except Exception:
            good = None
        # skip empty results silently
        if good is not None:
            tsorted.append(good)
    return tsorted


class WorkRunner:
    """Fetches/keeps the canon seats; plays forever with reshuffle."""

    def __init__(self, palette):
        self.palette = palette
        self._queue = None

    def ensure_queue(self):
        if self._queue is None:
            self._queue = prefetch()
        return self._queue

    def play_forever(self):
        from .cli import run_queue
        last_key = None
        guard = 0
        while True:
            q = self.ensure_queue()
            if not q:
                guard += 1
                if guard > 2:  # network dead, don't spin
                    raise RuntimeError(
                        "no recordings fetched; check the network and retry")
                time.sleep(1.5)
                continue
            q = q[:]
            if q and q[0].cache_path().exists() and last_key is not None:
                random.shuffle(q)
            try:
                run_queue(q, note="work")
                last_key = 1
            except KeyboardInterrupt:
                raise
            time.sleep(0.6)
