"""Terminal visuals: gradients, splash, banners, melt-in reveals and the
reactive playback UI (equalizer driven by REAL audio RMS from symphonix.player)."""
import math
import random
import time

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from .art import GENERIC_ART, art_lines, render_bigtext

console = Console()

# --------------------------------------------------------------- palette ---
def _tint(hex_color: str, t: float):
    """t=0 -> plain, t=-1 darker, t=+1 toward white"""
    r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
    if t > 0:
        r += int((255 - r) * t); g += int((255 - g) * t); b += int((255 - b) * t)
    else:
        r = int(r * (1 + t)); g = int(g * (1 + t)); b = int(b * (1 + t))
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

def gradient(text: str, palette, width: int = None) -> Text:
    pal = list(palette or ["#ff00a0", "#8a2be2", "#ffd166"])
    n = len(pal)
    out = Text()
    lines = text.split("\n")
    width = width or (max((len(l) for l in lines), default=1) or 1)
    for row, line in enumerate(lines):
        t = row / max(len(lines) - 1, 1)
        idx = min(int(t * (n - 1) * 2), (n - 1) * 2) / 2
        i = int(idx); frac = idx - i
        c1 = pal[min(i, n - 1)]
        c2 = pal[min(i + 1, n - 1)]
        # simple two-tier gradient per line
        left = Text(line.ljust(width if False else 0))
        # split line: color 1st half, 2nd half second color (float blend skipped)
        half = max(len(line) // 2 + 1, 1)
        out.append(line[:half], style=f"bold {c1}")
        out.append(line[half:], style=f"{c2}")
        out.append("\n")
    return out

def paint(art, palette, rows=None) -> Text:
    """Vertical gradient paint of multi-line art (str or list of lines)."""
    pal = list(palette or ["#ff00a0", "#ffd166"])
    lines = [str(l) for l in (art if isinstance(art, (list, tuple))
              else str(art or "").rstrip("\n").split("\n"))]
    n = len(lines)
    t = Text()
    for i, line in enumerate(lines):
        pos = i / max(n - 1, 1)
        f = pos * (len(pal) - 1)
        a = int(f); b = min(a + 1, len(pal) - 1); frac = f - a
        col_a = pal[a]; col_b = pal[b]
        col = col_a if frac < 0.5 else col_b
        t.append(line + "\n", style=f"bold {col}")
    return t

# ------------------------------------------------------------------ notes ---
def _marquee(msg: str, width: int = 54, tick: int = 0) -> str:
    if not msg:
        return ""
    msg = f"  ♪  {msg}  ♫  "
    n = max(len(msg), width + 1)
    off = (tick * 3) % n
    shifted = msg[off:] + msg[:off]
    return (shifted * 3)[:width]

def _notes_line(width: int = 52, dens: int = 9) -> str:
    notes = "♪♫♬♩♭♮♯"
    return " ".join(random.choice(notes) if random.random() < 0.55 else "·"
                    for _ in range(dens)).center(width)

def title_lines(msg="SYMPHONIX", palette=(["#7c4dff", "#e2118d", "#ff7a18"])) -> Text:
    big = render_bigtext(msg)
    big = [l.rstrip() for l in big]
    painted = Text()
    pal = list(palette)
    n = len(big)
    for i, line in enumerate(big):
        f = i / max(n - 1, 1)
        j = min(int(f * (len(pal) - 1) * 2), 2 * (len(pal) - 1)) / 2
        ci = int(j); frac = j - ci
        c = pal[min(ci, len(pal) - 1)] if frac < 0.7 else pal[min(ci + 1, len(pal) - 1)]
        painted.append(line + "\n", style=f"bold {c}")
    return painted

# ------------------------------------------------------------------ command-level visuals

def splash(palette, version: str = "1.0.0", fast=False):
    big = title_lines("SYMPHONIX", palette)
    for tick in range(6 if fast else 3):
        vibe = Text()
        vibe.append(_notes_line(64 if not fast else 40, dens=11), style="dim " + pal0(palette, 3))
        vibe.append("\n")
        vibe.append(big)
        vibe.append("\n")
        vibe.append(_notes_line(64 if not fast else 40, dens=11), style="dim " + pal0(palette, 1))
        vibe.append(Text(f"public-domain classical music, in your terminal  ·  v{version}",
                         style="italic #8a8a8a").center(66))
        with Live(vibe, console=console, refresh_per_second=12, transient=True):
            time.sleep(0.25)

def pal0(palette, i):
    try:
        return palette[i % len(palette)]
    except Exception:
        return "#ff00a0"

def banner(composer_key: str, palette, name: str = "", era: str = "", blurb: str = ""):
    art = "\n".join(art_lines(composer_key))
    panel = Panel(
        Align.center(paint(art, palette)),
        title=Text(name or (composer_key or "?").title(), style="bold " + pal0(palette, 0)),
        subtitle=Text(era, style="dim " + pal0(palette, 1)),
        border_style=pal0(palette, 2),
        padding=(1, 3),
    )
    console.print(panel)
    if blurb:
        console.print(" " * 4 + f"{blurb}", style=f"italic {pal0(palette, 1)}")
    console.print()

def notes_rain(palette, secs=1.2, rows=5):
    frame = []
    colors = [pal0(palette, i) for i in range(4)] or ["#ff00a0"]
    live = Live(Text(), console=console, refresh_per_second=14, transient=False)
    with live:
        t0 = time.time()
        rng_rows = rows
        while time.time() - t0 < secs:
            frame = []
            for r in range(rng_rows):
                notes = "".join(random.choice("♪♫♬♩") if random.random() < .2 else " "
                                for _ in range(56))
                frame.append(Text(notes, style=random.choice(colors)))
            live.update(Align.center(Group(*frame)))
            time.sleep(0.06)

# ------------------------------------------------------------- playback UI --
TOKEN_BLOCKS = "▁▂▃▄▅▆▇█"

def _eq_grid(levels_deq, width=12, height=6, palette=("#8a2be2",)) -> Text:
    t = Text()
    sm = list(levels_deq)[-width * 4:]
    if not sm:
        cols = [0.0] * width
    else:
        chunks = max(len(sm) // width, 1)
        cols = []
        for i in range(width):
            vals = sm[i * chunks:(i + 1) * chunks]
            cols.append(sum(vals) / max(len(vals), 1))
        # smooth: cols[-1]=newest
        cols = cols[::-1]
    # stable gradient per ROW (no random color churn -> no flicker)
    for y in range(height - 1, -1, -1):
        rowc = max((y + 1) / height, 0.12)
        line = []
        for lvl in cols:
            filled = lvl >= rowc
            line.append("█" if filled else "·")
        t.append("".join(line) + "\n", style=pal0(palette, min(y, len(palette) - 1)))
    return t


def work_frame(tick, palette, width=46, height=7):
    """Animated classical staff with sliding notes (work mode art)."""
    pal = list(palette) or ["#8a2be2"]
    rows = [Text()] * height
    rows = [Text() for _ in range(height)]
    staff = 3                                     # center row of the pentagram
    for y in range(height):
        line = Text()
        for x in range(width):
            if y in range(1, 6) and (x % 6 == 0):
                line.append("─" if x % 6 == 0 else " ")
            else:
                line.append(" ")
        rows[y] = line
    # sliding notes across the staff
    for i in range(4):
        x = (tick * 2 + i * 11) % (width + 8) - 4
        if 0 <= x < width:
            phase = math.sin(tick * 0.22 + i * 1.3)
            y = staff + (1 if phase > 0.5 else -1 if phase < -0.5 else 0)
            rows[y].append("")                    # keep row object
            # insert note char at position x by rebuilding the row
            base = rows[y].plain
            if x < len(base):
                rows[y] = Text(base[:x]) + Text(
                    random.choice(("♪", "♫", "♩", "♬")),
                    style="bold " + pal0(pal, i)) + Text(base[x + 1:])
    t = Text()
    for row in rows:
        t.append(row)
        t.append("\n")
    return t


def work_ui(player, palette, controller=None):
    """Endless work-mode display: staff art + eq + progress, until stopped."""
    label = "work ♪ canon of cornerstones"
    keep = True
    tick = 0
    from .anim import Live
    live = Live(Align.center(Text()), console=console,
                refresh_per_second=7, transient=False)
    with live:
        while keep:
            if controller:
                action = controller.poll()
                if action in ("next", "stop", "back"):
                    keep = False
                    break
                if action == "pause":
                    player.toggle()
            tick += 1
            est = getattr(player, "_duration_estimate", 0.0) or player.duration
            elapsed = getattr(player, "elapsed", 0.0)
            frac = min(elapsed / est, 1.0) if est else 0.0
            bar = "█" * int(frac * 30) + "░" * (30 - int(frac * 30))
            icon = "▶" if player.status == "playing" else "⏸"
            art = paint(work_frame(tick, palette).plain.split("\n")[:7], palette)
            body = Group(
                Align.center(Panel(
                    Group(art, Text(), _eq_grid(player.levels,
                                                width=20, height=6,
                                                palette=palette)),
                    title=Text(" 🎼 work mode ", style="bold " + pal0(palette, 1)),
                    subtitle=Text("q/n: stop · space: pause",
                                  style=f"dim {pal0(palette, 3)}"),
                    border_style=pal0(palette, 0), padding=(1, 2))),
                Text(f"\n{icon}  {int(elapsed)/60:02.0f}:{int(elapsed)%60:02d}"
                     f"  ·  {frac*100:02.0f}%  ·  {bar}",
                     style=f"dim {pal0(palette, 2)}"),
            )
            live.update(Align.center(body))
            time.sleep(0.14)


def playback_ui(player, track, composer_key: str, palette, controller=None,
                note: str = ""):
    """Run a Live loop until the player finishes / is stopped."""
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    tick = 0
    dots = "◀◀"
    name, era, blurb, art = "", "", "", ""
    if composer_key:
        from .art import COMPOSERS
        name, era, blurb, art = COMPOSERS.get(composer_key, ("", "", "", ""))
    mini_art = "\n".join(art_lines(composer_key)) if composer_key else "\n".join(GENERIC_ART)
    label = (track.label if track else "—")[:66]
    duration = getattr(player, "duration", 0.0) or 0.0
    if note == "work":
        return work_ui(player, palette, controller=controller)
    stop_requested = False
    from .anim import Live as _Live
    live = _Live(Align.center(Text()), console=console,
                 refresh_per_second=7, transient=False)
    with live:
        while not player.finished.is_set() and not stop_requested:
            if controller:
                action = controller.poll()
                if action == "pause":
                    player.toggle()
                elif action in ("next", "stop"):
                    stop_requested = True
                    player.stop()
                    break
                elif action == "back":
                    stop_requested = True
                    player.stop()
                    break
            tick += 1
            speed = getattr(player, "speed_note", "")
            lvl_height = 6
            eq = _eq_grid(player.levels, width=14, height=lvl_height, palette=palette)
            est = duration or getattr(player, "_duration_estimate", 0.0)
            elapsed = getattr(player, "elapsed", 0.0)
            if est:
                frac = min(elapsed / est, 1.0)
                bar = "█" * max(int(frac * 34), 1) + "░" * (34 - int(frac * 34))
            else:
                bar = "░" * 34
            status = player.status
            icon = "▶" if status == "playing" else ("⏸" if status == "paused" else "♪")
            head = Text()
            head.append(_marquee(label, tick=tick) + "\n", style="bold " + pal0(palette, 0))
            head.append(f"{icon} {status}  ·  {int(elapsed)}s{(' /' + f'{int(est)}s') if est else ''}"
                        f"  ·  {speed or ''}".rstrip() + "\n", style="dim")
            head.append(bar + "\n", style=pal0(palette, 2))
            head.append(_notes_line(50, dens=8), style="dim " + pal0(palette, 3))
            group = Group(
                Align.center(Panel(
                    Align.center(Group(
                        paint("\n".join(mini_art.split("\n")[3:11]), palette),
                        eq,
                    )),
                    title=Text(f" {name or 'Composer'} ".strip(), style="bold " + pal0(palette, 1))
                          if name else Text(" resident ♫ ", style="dim"),
                    subtitle=Text("keys: [space] pause · [n] skip · [s] save + next · [q] stop",
                                  style="dim"),
                    border_style=pal0(palette, 0), padding=(0, 2)),
                ),
                head,
            )
            live.update(Align.center(group))
            time.sleep(0.12)
    return "next" if stop_requested else "done"
