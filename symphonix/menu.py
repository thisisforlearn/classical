"""Arrow-key interactive menu (the main way to drive sx).

Navigation: ↑/↓ or j/k move, Enter selects, q/Qu/Esc cancels, digits jump,
typing letters filters the list live (Backspace erases). Falls back to a
numbered prompt when stdin is not a terminal.
"""
import sys

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .keys import read_key


def _render(title, options, cur, palette, hint, filt, view):
    pal = palette or ["#8a2be2", "#d946ef", "#06b6d4", "#e879f9"]
    head = Text()
    head.append(f" ♪ {title} ", style=f"bold {pal[1]}")
    if filt:
        head.append(f"  [filter: {filt}]", style="dim")
    rows = Table.grid(padding=(0, 2))
    shown = _window(options, cur)
    offset = max(0, cur - 8)
    for i, label in enumerate(shown):
        real_i = offset + i
        mark = "▶ " if real_i == cur else "  "
        txt = Text(mark + " " + label, style=None)
        if real_i == cur:
            txt.stylize_range(f"bold {pal[2]}", 0, len(txt))
        rows.add_row(txt)
    foot = Text(hint or "↑↓ select · enter go · type to filter · q back",
                style=f"dim {pal[6] if len(pal) > 6 else pal[3]}")
    return Group(head, rows, "", foot)


def _window(options, cur, size=14):
    if len(options) <= size:
        return list(options)
    offset = min(max(0, cur - size // 2), max(0, len(options) - size))
    return list(options)[offset:offset + size]


def pick(title, options, palette=None, hint=None, initial=0):
    """returns selected index or None. Never raises. Non-tty -> numbered prompt."""
    if not options:
        return None
    try:
        if not sys.stdin.isatty():
            pass  # fall through to numbered fallback
        else:
            return _live_pick(title, options, palette, hint, initial)
    except Exception:
        pass
    print(f"\n{title}")
    for i, o in enumerate(options, 1):
        print(f"  {i:2d}. {o}")
    try:
        raw = input("#> ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        idx = int(raw) - 1
        return idx if 0 <= idx < len(options) else None
    except ValueError:
        return None


def _live_pick(title, options, palette, hint, initial):
    cur, filt = min(initial, len(options) - 1), ""
    with Live(
        _render(title, options, cur, palette, hint, filt, "grid"),
        screen=False, refresh_per_second=4) as live:
        while True:
            key = read_key()
            if key is None:
                continue
            if key in ("up", "k"):
                cur = (cur - 1) % len(options)
            elif key in ("down", "j"):
                cur = (cur + 1) % len(options)
            elif key == "enter":
                live.update(_render(title, options, cur, palette, hint, filt, "grid"))
                return cur
            elif key in ("esc", "q"):
                return None
            elif key in ("backspace", "delete"):
                filt = filt[:-1]
            elif key == "space":
                cur = min(cur + 5, len(options) - 1)
            elif isinstance(key, str) and len(key) == 1 and key.isdigit():
                i = int(key) - 1
                if 0 <= i < len(options):
                    cur = i
            elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                filt += key
            vis = [o for o in options if filt.lower() in o.lower()] if filt else options
            if not vis:
                cur = 0
                vis = options
            cur = max(0, min(cur, len(vis) - 1))
            # keep cur pointing at filtered label
            actual = options.index(vis[cur]) if vis else 0
            live.update(_render(title, options, actual, palette, hint, filt, "grid"))
