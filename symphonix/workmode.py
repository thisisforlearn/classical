"""Work focus mode: endless classical playing pulled from the canon.

- Prefetches all recommended queries in parallel so the first track starts fast
- Loops forever (reshuffled each pass, no instant repeats)
- Ctrl+C once: skip · twice fast: quit (or 'q' during playback)
"""
import random
import threading
import time

from .masterpieces import RECOMMENDED


def canon_queries(items=None):
    out = []
    for key, work, squery in (items or RECOMMENDED):
        out.append({
            "key": key, "work": work, "query": squery or work,
        })
    return out


def prefetch(items=None, timeout_cap=25.0):
    """Search each cornerstone once, in parallel. Returns [Track] in canon order."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .search import search as do_search
    jobs = {}
    plan = canon_queries(items)
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for item in plan:
            jobs[ex.submit(do_search, item["query"], "", 6,
                           "archive", True)] = item
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

    def __init__(self, palette, items=None):
        self.palette = palette
        self.items = items
        self._queue = None

    def ensure_queue(self):
        if self._queue is None:
            self._queue = prefetch(items=self.items)
        return self._queue

    def play_forever(self):
        from .anim import SESSION
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
            if SESSION.get("quit"):
                SESSION["quit"] = False
                return                       # user pressed q: out of work mode
            time.sleep(0.4)


# ---------------------------------------------------------------- collections
COLLECTIONS = {
    "full canon": [("mozart", "Symphony No. 41 Jupiter", "Mozart Jupiter symphony 41"),
        ("beethoven", "Symphony No. 5", "Beethoven symphony 5"),
        ("vivaldi", "Four Seasons Spring", "Vivaldi Spring four seasons"),
        ("bach", "Toccata and Fugue in D minor BWV 565", "Bach toccata fugue"),
        ("handel", "Messiah Hallelujah Chorus", "Handel hallelujah chorus"),
        ("grieg", "In the Hall of the Mountain King", "Grieg mountain king")],
    "classical era": [
        ("mozart", "Symphony No. 41 Jupiter", "Mozart Jupiter symphony 41"),
        ("mozart", "Eine kleine Nachtmusik", "Mozart Eine kleine Nachtmusik"),
        ("haydn", "Surprise Symphony", "Haydn surprise symphony"),
        ("mozart", "Piano Concerto No. 21 Andante", "Mozart concerto 21 andante")],
    "romantic": [
        ("beethoven", "Symphony No. 9 Ode to Joy", "Beethoven symphony 9"),
        ("schubert", "Trout Quintet", "Schubert trout quintet"),
        ("chopin", "Nocturne Op. 9 No. 2", "Chopin nocturne 9 2"),
        ("tchaikovsky", "Swan Lake", "Tchaikovsky swan lake")],
    "piano recital": [
        ("chopin", "Nocturne Op. 9 No. 2", "Chopin nocturne 9 2"),
        ("satie", "Gymnopedie No. 1", "Satie Gymnopedie 1"),
        ("debussy", "Clair de Lune", "Debussy clair de lune"),
        ("liszt", "Hungarian Rhapsody No. 2", "Liszt Hungarian Rhapsody 2")],
}
