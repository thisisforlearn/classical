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
