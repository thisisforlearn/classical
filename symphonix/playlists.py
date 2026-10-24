"""Playlists: save/load as JSON (+ .m3u export)."""
import json
from pathlib import Path
from .config import playlists_dir
from .track import Track

class Playlists:
    def list(self) -> "list[str]":
        return sorted(p.stem for p in playlists_dir().glob("*.json"))

    def path(self, name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name) or "playlist"
        return playlists_dir() / f"{safe}.json"

    def load(self, name: str) -> "list[Track] | None":
        p = self.path(name)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            fields = [Track.from_dict(d) for d in data.get("tracks", [])]
            return fields
        except Exception:
            return None

    def save(self, name: str, tracks: "list[Track]") -> Path:
        p = self.path(name)
        p.write_text(json.dumps({"name": name, "tracks": [t.to_dict() for t in tracks]},
                                indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def delete(self, name: str) -> bool:
        p = self.path(name)
        if p.exists():
            p.unlink()
            return True
        return False

    def export_m3u(self, name: str) -> Path:
        tracks = self.load(name) or []
        out = self.path(name).with_suffix(".m3u")
        lines = ["#EXTM3U"]
        for t in tracks:
            src = str(t.cache_path()) if t.is_cached() else t.url
            dur = t.duration if ":" in (t.duration or "") else "-1"
            lines += [f"#EXTINF:{-1},{t.label}", src]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out


# ------------------------------------------------------------------ presets
PRESET_PLAYLISTS = {
    "piano recital": [
        "Satie Gymnopedie 1", "Debussy clair de lune",
        "Chopin nocturne 9 2", "Liszt Liebestraum 3",
        "Schumann Traumerei", "Beethoven Fur Elise"],
    "symphonies": [
        "Beethoven symphony 5", "Beethoven symphony 9",
        "Mozart Jupiter symphony 41", "Schubert unfinished symphony"],
    "baroque glow": [
        "Bach toccata fugue", "Vivaldi Winter four seasons",
        "Handel water music", "Pachelbel canon"],
    "opera arias": [
        "Verdi La Donna e Mobile", "Puccini Nessun Dorma",
        "Mozart Figaro overture", "Bizet habanera Carmen"],
}


def seed_presets(P=None, log=None):
    """Fill curated playlists with the best-quality PD recordings once."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .scoring import best_track
    from .track import Track

    P = P or Playlists()
    todo = {name: queries for name, queries in PRESET_PLAYLISTS.items()
            if P.path(name).exists() is False}
    if not todo:
        return 0
    if log:
        log(f"curating {len(todo)} hi-fi preset playlist(s)...")
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        jobs = {}
        for name, queries in todo.items():
            for i, query in enumerate(queries):
                jobs[ex.submit(_best_ok, query)] = (name, i)
        for fut in as_completed(jobs, timeout=110):
            try:
                name, i = jobs[fut]
                results[(name, i)] = fut.result()
            except Exception:
                continue
    for name, queries in todo.items():
        picked = []
        for i in range(len(queries)):
            t = results.get((name, i))
            if t is not None:
                picked.append(t)
        if picked:
            P.save(name, picked)
            if log:
                log(f"  ✓ created '{name}' — {len(picked)} lossless-first tracks")
    return len(todo)


def _best_ok(query):
    """One seed round: search (hifi first), then score, half a second guard."""
    from .search import search as do_search
    from .scoring import best_track
    for attempt in (True, False):
        try:
            tracks = do_search(query, limit=4, hifi=attempt)
            t = best_track(tracks, query)
            if t is not None and t.url:
                return t
        except Exception:
            continue
    return None
