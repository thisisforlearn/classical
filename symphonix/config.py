"""Configuration, themes and on-disk state for symphonix."""
import json
import os
from pathlib import Path

APP = "symphonix"

def app_dir() -> Path:
    d = Path(os.environ.get("SYMPHONIX_HOME", str(Path.home() / ("." + APP))))
    d.mkdir(parents=True, exist_ok=True)
    return d

def cache_dir() -> Path:
    d = app_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d

def playlists_dir() -> Path:
    d = app_dir() / "playlists"
    d.mkdir(parents=True, exist_ok=True)
    return d

def config_path() -> Path:
    return app_dir() / "config.json"

DEFAULT_CONFIG = {
    "theme": "dawn",
    "custom_colors": [],            # custom theme colors set via `sx theme custom`
    "composer_overrides": {},       # composer key -> custom palette
    "lines_per_search": 10,
    "last_quiz_score": 0,
    "best_quiz_score": 0,
}

def _read() -> dict:
    p = config_path()
    if not p.exists():
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
    return merged

def _write(cfg: dict) -> None:
    config_path().write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def get_config() -> dict:
    return _read()

def set_config(**kv: object) -> None:
    cfg = _read()
    cfg.update(kv)
    _write(cfg)

# ---------------------------------------------------------------- themes ---

THEMES = {
    "dawn":       ["#7c4dff", "#e2118d", "#ff7a18", "#ffd166"],
    "midnight":   ["#00e5ff", "#2979ff", "#7c4dff", "#00ffa3"],
    "vaporwave":  ["#ff71ce", "#01cdfe", "#05ffa1", "#b967ff"],
    "ember":      ["#ff4e00", "#d35400", "#c9a227", "#fff3b0"],
    "royal":      ["#c9a227", "#ffe08a", "#b388ff", "#e6e6fa"],
    "forest":     ["#1b998b", "#a3d977", "#2b303a", "#dbffb1"],
    "acid":       ["#39ff14", "#ffe600", "#ff007f", "#00fff7"],
    "mono":       ["#ffffff", "#c9c9c9", "#8a8a8a", "#565656"],
    "neon":       ["#ff0266", "#f806cc", "#0f58f6", "#19f9d8"],
    "autumn":     ["#d7263d", "#f46036", "#ff9b3d", "#ffb932"],
    "lagoon":     ["#00d1b6", "#2ec4b6", "#5bc0eb", "#fde74c"],
    "amethyst":   ["#9b5de5", "#c77dff", "#e0aaff", "#4ea8de"],
}

def get_palette(composer_key: str | None = None) -> list[str]:
    """Palette = composer override -> custom colors -> named theme default."""
    cfg = _read()
    if composer_key:
        ov = cfg.get("composer_overrides", {})
        pal = ov.get(composer_key)
        if pal:
            return list(pal)
    theme = cfg.get("theme", "dawn")
    if theme == "custom" and cfg.get("custom_colors"):
        return list(cfg["custom_colors"])
    return list(THEMES.get(theme, THEMES["dawn"]))

def COMPOSER_KEYS() -> list[str]:
    # avoid circular import: read the registry lazily
    from .art import COMPOSERS
    return [k for k, _ in zip(COMPOSERS.keys(), range(len(COMPOSERS)))]
