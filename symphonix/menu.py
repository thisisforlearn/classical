"""Interaction tier system:  1) arrow keys (questionary, cross-platform)
                            2) numbered picker (works anywhere)
                            3) typing interface (works anywhere)

The mode is chosen once (first run) and stored in the on-disk config.
If the current tier errors at runtime we silently demote to the next tier
and remember a one-line note, so menus NEVER crash the app.
"""
import sys

from .config import get_config, set_config

try:
    import questionary
    from questionary import Style
    HAS_Q = True
except Exception:                                   # pragma: no cover
    questionary, Style = None, None
    HAS_Q = False

MODES = ("arrow", "number", "type")
_LABELS = {
    "arrow":  "⌨  arrow keys — select with ↑ ↓ + Enter (recommended)",
    "number": "🔢  numbered list — type the number you want",
    "type":   "⌨  typing — type what you want, press Enter",
}


def get_ui_mode() -> str:
    cfg = get_config()
    mode = cfg.get("ui") or "arrow"
    if mode not in MODES:
        mode = "arrow"
    return mode


def set_ui_mode(mode: str) -> None:
    if mode in MODES:
        set_config(ui=mode)


class _Demote:
    """Session state: which tier failed, for a dim one-line note."""
    note = ""


def _style_for(palette):
    """questionary Style built from our theme palette (safe ANSI subset)."""
    try:
        pal = list(palette)
        hexes = [c.lstrip("#") for c in pal[:4]] or ["8a2be2", "e879f9",
                                                    "06b6d4", "ffffff"]
        return Style([
            ("qmark",      "fg:#" + hexes[1] + " bold"),
            ("question",   "fg:#" + hexes[0] + " bold"),
            ("highlighted", "fg:black bg:#" + hexes[1] + " bold"),
            ("pointer",    "fg:#" + hexes[1] + " bold"),
            ("answer",     "fg:#" + hexes[2] + " bold"),
        ])
    except Exception:
        return Style([("highlighted", "fg:black bg:white bold")])


def pick(title, options, palette=None, hint=None, initial=0):
    """returns selected index or None (back/quit). Never raises."""
    if not options:
        return None
    mode = get_ui_mode()
    tiers = [mode] + [m for m in MODES if m != mode]
    for tier in tiers:
        try:
            if tier == "arrow" and HAS_Q and sys.stdin.isatty() and sys.stdout.isatty():
                return _arrow_pick(title, options, palette, initial)
            if tier == "number":
                return _number_pick(title, options)
            if tier == "type":
                return _type_pick(title, options)
        except (KeyboardInterrupt, EOFError):
            return None
        except Exception as exc:                    # demote, keep going
            _Demote.note = f"{tier} menu unavailable ({exc.__class__.__name__})"
    return None


class _Qiary:
    pass


def _arrow_pick(title, options, palette, initial):
    cut = max(len(str(options[0]) + title) + 8, 96)
    entries = [o if len(o) <= cut else o[: cut - 1] + "…" for o in options]
    menu = questionary.select(
        title,
        choices=entries,
        style=_style_for(palette),
        pointer="▶",
        instruction="(↑ ↓ move · enter select · q back)",
    )
    answer = menu.ask()
    if answer is None or answer == "" or answer is False:
        return None
    cleaned = answer if len(answer) < 2 else answer.replace("…", "")
    if cleaned in options:
        cleaned = options[options.index(cleaned)]
    try:
        hooks = [i for i, o in enumerate(options) if o == cleaned or
                 (len(cleaned) > 4 and cleaned in o)]
        return hooks[0] if hooks else None
    except ValueError:
        return None


def _number_pick(title, options):
    print()
    print(title)
    for i, o in enumerate(options, 1):
        print(f"  {i:2d}. {o}")
    raw = input("#> ").strip()
    try:
        idx = int(raw) - 1
        return idx if 0 <= idx < len(options) else None
    except ValueError:
        return None


def _type_pick(title, options):
    print()
    print(title)
    query = input("type here ✏  ").strip().lower()
    if not query:
        return None
    hits = [i for i, o in enumerate(options) if query in o.lower()]
    if not hits:
        print("(nothing matched — exact index? e.g. 4)") 
        raw = input("#> ").strip()
        try:
            idx = int(raw) - 1
            return idx if 0 <= idx < len(options) else None
        except ValueError:
            return None
    if len(hits) == 1:
        return hits[0]
    # several matches: one more round of narrowing
    for j, i in enumerate(hits, 1):
        print(f"  {j:2d}. {options[i]}")
    raw = input("#> ").strip()
    try:
        j = int(raw) - 1
        return hits[j] if 0 <= j < len(hits) else None
    except ValueError:
        return None


def ensure_ui_mode(consol=None) -> str:
    """Ask once which interaction tier; stores in config. Returns the mode."""
    cfg = get_config()
    if cfg.get("ui") in MODES:
        return cfg["ui"]
    print()
    choice = pick("🎛  pick how you want to control symphonix (remembered):",
                  list(_LABELS.values()), palette=None)
    mode = {0: "arrow", 1: "number", 2: "type"}.get(choice, "arrow")
    set_ui_mode(mode)
    return mode
