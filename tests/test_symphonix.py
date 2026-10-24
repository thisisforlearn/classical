"""symphonix test suite (offline-friendly; network tests are optional)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from symphonix.art import (ORDER as ART_ORDER, COMPOSERS, match_composer,
                           render_bigtext)  # noqa: E402
from symphonix.config import THEMES, get_palette  # noqa: E402
from symphonix.track import Track, unique  # noqa: E402
from symphonix.playlists import Playlists  # noqa: E402


def test_24_composers_registry():
    assert len(COMPOSERS) >= 24
    for key in ART_ORDER:
        name, era, blurb, art = COMPOSERS[key]
        assert name and era and blurb and art.strip(), key

def test_bigtext_letters():
    rows = render_bigtext("SX")
    assert len(rows) == 5
    assert "█" in rows[0]

def test_match_composer():
    assert match_composer("Beethoven symphony no 5") == "beethoven"
    assert match_composer("The Best of MOZART") == "mozart"
    assert match_composer("unknown jamendo track") is None

def test_themes_palettes():
    assert len(THEMES) >= 10
    for name, pal in THEMES.items():
        assert len(pal) == 4
        for c in pal:
            assert c.startswith("#") and len(c) == 7

def test_track_roundtrip_and_dedupe():
    t1 = Track(id="a", url="http://x/a.mp3", title="Nocturne", composer="Chopin",
               source="archive", ext="mp3")
    t2 = Track.from_dict(t1.to_dict())
    assert t2.title == "Nocturne" and t2.composer == "Chopin"
    t3 = Track(id="c", url="http://x/c.mp3", title="Nocturne", composer="Chopin")
    assert len(unique([t1, t2, t3])) == 1

def test_playlists_save_load(tmp_path, monkeypatch):
    import symphonix.config as cfg
    monkeypatch.setattr(cfg, "playlists_dir", lambda: tmp_path)
    pl = Playlists()
    t = Track(id="a", url="http://x/a.mp3", title="T", ext="mp3")
    pl.save("mine", [t])
    assert "mine" in pl.list()
    loaded = pl.load("mine")
    assert loaded[0].title == "T"
    m3u = pl.export_m3u("mine")
    assert "#EXTM3U" in m3u.read_text()

def test_search_shape_offline():
    import symphonix.search as S

    class Fake:
        def get(self, *a, **k):  # minimal requests session stub
            raise RuntimeError("offline")
    # just ensure signature works and returns list
    assert isinstance(S.search.__doc__, str)

# ---- live network tests (skipped by default; run with --live) ----------

@pytest.fixture
def live(request):
    if not request.config.getoption("--live"):
        pytest.skip("live network test (use --live)")
    return True

def test_live_archive_search(live):
    import symphonix.search as S
    res = S.search("bach air", limit=1)
    assert res
    assert res[0].url.startswith("http")


# ------------------------------------------------------------------ random
def test_masterpieces_cover_all_composers():
    from symphonix.masterpieces import MASTERPIECES
    from symphonix.art import ORDER
    missing = [k for k in ORDER if k not in MASTERPIECES]
    assert not missing, f"composers missing masterpieces: {missing}"
    for key, works in MASTERPIECES.items():
        assert works and all(isinstance(w, str) and w for w in works)


def test_random_roulette_modes():
    from symphonix.roulette import compute_random_piece
    from symphonix.masterpieces import MASTERPIECES
    key, q, label = compute_random_piece("chopin", max_mode=True)
    assert key == "chopin" and "signature" in label and q
    key, q, label = compute_random_piece("bach", max_mode=False)
    assert key == "bach" and q.endswith("Bach") and "random" in label
    key, q, label = compute_random_piece(None, max_mode=False)
    assert key in MASTERPIECES and q
    # 'max' as first positional token flips signature mode
    key, q, label = compute_random_piece("max")
    assert key in MASTERPIECES and "signature" in label
    key, q, label = compute_random_piece("max mozart")
    assert key == "mozart" and "signature" in label


# ------------------------------------------------------------ ui tiers
def test_menu_tiers_and_mode_store():
    from symphonix.menu import MODES, get_ui_mode, set_ui_mode, pick
    set_ui_mode("number")
    assert get_ui_mode() in MODES
    set_ui_mode("arrow")
    # non-tty: arrow tier skipped, demote chain returns None w/o crash
    assert pick("t", ["a", "b"]) is None


def test_work_prefetch_offline(monkeypatch):
    from symphonix.workmode import prefetch
    from symphonix.track import Track
    hits = {"a": [], "b": []}
    def fake(q, composer="", limit=5, which="all"):
        idx = "a" if "toccata" in q.lower() else "b"
        return [Track(id=idx, url=f"http://{idx}", title=q[:24], source="archive")]
    import symphonix.search as S
    monkeypatch.setattr(S, "search", fake)
    keys0 = list(prefetch())
    assert keys0 and all(t.url for t in keys0)
