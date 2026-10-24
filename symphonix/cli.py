"""symphonix CLI - the `sx` command suite."""
import argparse
import json as _json
import os
import random
import sys
import time

from . import __version__
from .art import COMPOSERS, ORDER, art_lines, match_composer
from .masterpieces import MASTERPIECES
from .roulette import RandomNobody, compute_random_piece, fetch_tracks, list_masterpieces
from .config import cache_dir, get_palette, get_config, set_config, THEMES
from .track import Track
from .search import search as do_search

# ------------------------------------------------------------------ shared --
CONSOLE = None

def con():
    global CONSOLE
    if CONSOLE is None:
        from rich.console import Console
        CONSOLE = Console()
    return CONSOLE

def palette_for(key=None):
    cfg = get_config()
    if getattr(get_config(), "get", None):
        pass
    cfg_run_theme = get_config().get("run_theme")
    if cfg_run_theme:
        cfg = dict(get_config())
        pal = THEMES.get(cfg_run_theme) or cfg.get("custom_colors") or []
        if pal:
            return list(pal)
    return get_palette(key)

def _banner_key(key, palette=None):
    from .anim import banner
    name, era, blurb, art = (COMPOSERS.get(key) or ("", "", "", ""))
    banner(key, palette or palette_for(key), name=name, era=era, blurb=blurb)

def _search_rows(tracks):
    from rich.table import Table
    t = Table(show_header=True, header_style="dim", box=None, pad_edge=False)
    t.add_column("#", justify="right", style="bold")
    t.add_column("piece")
    t.add_column("by / notes", style="dim")
    t.add_column("src", justify="center")
    t.add_column("len", justify="right", style="dim")
    t.add_column("size", justify="right", style="dim")
    SRC_COLOR = {"archive": "#66ccff", "musopen": "#ffdd77", "imslp": "#99ff99"}
    for i, tr in enumerate(tracks, 1):
        cached = " *" if tr.is_cached() else ""
        t.add_row(f"{i}", (tr.title or tr.id)[:64] + cached,
                  (tr.composer or "")[:30] + ((" · " + tr.year) if tr.year else ""),
                  f"[{SRC_COLOR.get(tr.source, '#aaaaaa')}]{tr.source}[/]",
                  tr.duration[:8], (f"{tr.size // 1024}k" if tr.size else "-"))
    if tracks:
        con().print(t)
    else:
        con().print("[yellow]no results - try fewer words[/]")

def _pick_track(query: str, limit=8, which="all"):
    if query.startswith("http"):
        t = Track(id=query, url=query, title=query.rsplit("/", 1)[-1][:60],
                  source="direct")
        return t
    results = do_search(query, limit=limit, which=which)
    if not results:
        return None
    from .scoring import best_track
    return best_track(results, query)

def _player():
    from .player import Player
    return Player()

def _controller():
    from .keys import KeyController
    return KeyController().start()

# ------------------------------------------------------------------ commands

def cmd_default(args):
    if args.fast:
        pass
    else:
        pal = palette_for()
        try:
            from .anim import splash
            splash(pal, __version__, fast=getattr(args, "fast", False))
        except Exception:
            pass
    key = random.choice(ORDER)
    _banner_key(key)
    from rich.panel import Panel
    from rich.text import Text
    con().print(Panel(Text(
        " find & play public-domain classical music, right in your terminal.\n\n"
        "   sx search bethoven 5th       → colored results table\n"
        "   sx play   mozart requiem     → streams instantly w/ equalizer\n"
        "   sx download bach brandenburg → smart download to disc\n"
        "   sx random max beethoven      → 🎲 surprise masterpiece mode\n"
        "   sx work                      → 🧑‍💻 endless focus canon + staff art\n"
        "   sx quiz                      → guess-the-composer game mode\n"
        "   sx theme vaporwave --preview → swap ALL the colors\n"
        "   sx composers                 → 24 legendary artists, ASCII portraits\n"
        "   sx info chopin               → composer facts from Wikipedia\n"
        "   help: sx --help",
        justify="left"), border_style=pal_for_dash(palette_for(key)),
        title="quickstart", title_align="left"))

def pal_for_dash(pal):
    try:
        return pal[2 % len(pal)]
    except Exception:
        return "#8a2be2"

def cmd_composers(args):
    pal = palette_for()
    if getattr(args, "jsonf", None):
        print(_json.dumps([{"key": k, "name": v[0], "era": v[1], "blurb": v[2]}
                           for k, v in COMPOSERS.items()], indent=2))
        return
    if args.art:
        for k in ORDER:
            _banner_key(k)
            time.sleep(0.15)
        return
    from rich.table import Table
    t = Table(title="🎼 the symphonix composers — 24 legends",
              title_style="bold " + pal[0], box=None, pad_edge=False)
    t.add_column("key", style="dim")
    t.add_column("artist", style="bold " + pal[1])
    t.add_column("era", style="dim")
    t.add_column("mono", style="italic dim")
    col = 0
    half = (len(ORDER) + 1) // 2
    left, right = ORDER[:half], ORDER[half:]
    for a, b in zip(left, right + [(" ", " ", "", "")]):
        na, eraa, blurb_a = COMPOSERS[a][0], COMPOSERS[a][1], COMPOSERS[a][2]
        nb, erab, blurb_b = COMPOSERS.get(b, ("", "", "", ""))[:3] if b else ("", "", "")
        t.add_row(a, na, eraa, (blurb_a or "")[:52],
                  b, nb, erab, (blurb_b or "")[:52])
    con().print(t)

def cmd_banner(args):
    key = None
    if args.key:
        key = match_composer(args.key) or (args.key.lower() if args.key.lower() in COMPOSERS else None)
        if key is None:
            from rich.prompt import Confirm
            con().print(f"[red]unknown composer '{args.key}'[/]")
            return 1
    else:
        key = random.choice(ORDER)
    _banner_key(key)
    return 0

def cmd_search(args):
    tracks = do_search(args.query, composer=args.composer or "",
                       limit=args.limit, which=args.src or "all")
    if args.json:
        print(_json.dumps([t.to_dict() for t in tracks], indent=2, ensure_ascii=False))
        return
    _search_rows(tracks)
    SLC = {"archive": "♫", "musopen": "♪", "imslp": "♬", "direct": "·"}
    if tracks:
        con().print(f"[dim]  play/show with: sx play '{args.query[:40]}'  ·  "
                    f"download: sx download '{args.query[:40]}'  ·  "
                    f"raw urls: sx search '{args.query[:28]}' --json[/]")

def cmd_play(args):
    queue = []
    want = getattr(args, "playlist", None)
    if want:
        from .playlists import Playlists
        pl = Playlists().load(want)
        if not pl:
            con().print(f"[red]playlist '{want}' not found[/]")
            return 1
        queue.extend(pl)
    else:
        picks = do_search(args.query, limit=getattr(args, "limit", 5) or 5,
                          which=getattr(args, "src", None) or "all")
        if not picks and getattr(args, "limit", 1) == 1:
            con().print("[red]nothing found[/]")
            return 1
        if args.shuffle:
            random.shuffle(picks)
        queue.extend(picks)
    ret = run_queue(queue)
    # (shuffled the list above already)
    return ret

def run_queue(queue, note=""):
    from .config import cache_dir
    p = _player()
    ctl = _controller()
    palette = palette_for()
    try:
        for t in list(queue):
            if not t.url and not t.is_cached():
                continue
            p.play(t)
            key = t.guess_composer_key()
            action = None
            ui_action = None
            try:
                from .anim import playback_ui
                ui_action = playback_ui(p, t, key, palette, ctl, note=note)
            except KeyboardInterrupt:
                ui_action = None
            finally:
                try:
                    p.stop()
                except Exception:
                    pass
            # q/s pressed during playback: stop the WHOLE queue (the stop bug)
            if ui_action in ("stop", "back"):
                break
            # nothing to do for "next": fall through to the next track

    except KeyboardInterrupt:
        pass
    finally:
        p.stop()
    return 0

def cmd_download(args):
    tracks = []
    if args.query.startswith("http"):
        tracks = [Track(id=args.query, url=args.query,
                        title=args.query.rsplit("/", 1)[-1][:60], source="direct")]
    else:
        tracks = do_search(args.query, limit=args.limit or 10, which=args.src or "all")
    if not args.all and tracks:
        tracks = tracks[:1]
    from .downloader import content_size, stream_to_file
    key_palette = palette_for()
    for t in tracks:
        from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
        label = t.label
        with Progress(
            TextColumn("♪  downloading [bold]" + label + "[/]"),
            BarColumn(style=key_palette[0], complete_style=key_palette[1]),
            TextColumn("[progress.percentage]{task.percentage:>4.0f}%"),
            TimeRemainingColumn(), console=con(), transient=False) as prog:
            tid = prog.add_task(label, total=sum([max(t.size, 1)]))
            def cb(written, total_, speed):
                total_ = total_ or t.size or 1
                prog.update(tid, total=total_, completed=written)
            try:
                path = stream_to_file(t.url, str(t.cache_path()), on_progress=cb)
                con().print(f"[green]✓[/] {label} → {path}")
            except Exception as exc:
                con().print(f"[red]✗ {label}: {exc}[/]")
    return 0

def cmd_cache(args):
    d = cache_dir()
    if args.cache_cmd == "list":
        files = sorted(d.iterdir())
        tot = sum(f.stat().st_size for f in files if f.is_file())
        for f in files:
            con().print(f"  [cyan]{f.name}[/]  [dim]{f.stat().st_size // 1024} KB[/]")
        con().print(f"\n[bold]{len(files)} files · {tot // (1024 * 1024)} MB[/] in {d}")
    elif args.cache_cmd == "clear":
        for f in d.iterdir():
            try:
                f.unlink()
            except Exception:
                pass
        con().print("[green]cache cleared[/]")
    else:
        con().print(str(d))
    return 0

# ------------------------------------------------------------ work / ui -----
def cmd_work(args):
    """sx work — endless recommendation loop with animated staff art."""
    con().print("[bold]🧑‍💻 work mode[/] · cornerstones on repeat — "
                "space: pause · n: skip · q: stop")
    from .workmode import COLLECTIONS, WorkRunner
    items = COLLECTIONS.get(getattr(args, "collection", None) or "full canon") \
        or list(COLLECTIONS.values())[0]
    try:
        WorkRunner(palette_for(), items=items).play_forever()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        con().print(f"[red]work mode stopped:[/] {exc}")
    return 0


def cmd_ui(args):
    """sx ui [arrow|number|type] — choose control tier (stored)."""
    from .menu import MODES, get_ui_mode, set_ui_mode
    want = (args.mode or "").strip().lower()
    alias = {"arrow": "arrow", "arrows": "arrow", "q": "arrow",
             "num": "number", "numbered": "number", "numbers": "number",
             "n": "number", "type": "type", "typing": "type", "t": "type"}
    if want in alias:
        set_ui_mode(alias[want])
    cur = get_ui_mode()
    if not want or want not in alias:
        from .menu import _LABELS
        con().print(f"[bold]current UI tier:[/] {cur} " +
                    " · ".join(f"{k}={v[:14]}" for k, v in _LABELS.items()))
        con().print("[dim] sx ui arrow | sx ui num | sx ui type — "
                    "also switchable inside the menu[/]")
    else:
        con().print(f"[green]UI tier ≈ {cur}[/]")
    return 0


# ----------------------------------------------------------------- menu ---
def cmd_menu(args=None):
    """Arrow-key concert hall - the main way. Typed commands stay as fallback."""
    from types import SimpleNamespace
    from .menu import pick
    from .scoring import best_track

    def _type(prompt):
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    menu_pal = palette_for()
    from .menu import ensure_ui_mode, get_ui_mode, set_ui_mode
    ensure_ui_mode()
    acts = ["🔎  Search & Play",
            "👑  Recommended cornerstones",
            "🧑‍💻  Work mode — endless focus canon",
            "🎲  Random — surprise me",
            "🏆  Composer pages",
            "📥  Download for offline",
            "📜  Playlists",
            "🎯  Quiz",
            "🎨  Themes",
            "🎛  UI mode: {mode}",
            "ℹ️   About",
            "🚪  Exit"]
    while True:
        acts[9] = f"🎛  UI mode: {get_ui_mode()}"
        i = pick("[ symphonix concert hall ]", acts, palette=menu_pal,
                 hint="↑↓ choose · enter go · type to filter · q leave")
        if i is None:
            return 0
        try:
            if i == 0:                                       # search & play
                q = _type("🔎 search: ")
                if q:
                    res = do_search(q, limit=12, which="all")
                    if not res:
                        con().print("[yellow]nothing found[/]")
                        continue
                    first = best_track(res, q)
                    k = pick("results — enter = play now",
                             [t.label for t in res], palette=menu_pal)
                    if k is not None:
                        queue = res[k:] + res[:k] if first is not res[k] else res
                        run_queue(queue[:3])
                continue
            elif i == 1:                                     # recommended
                from .masterpieces import RECOMMENDED
                lbls = [f"{COMPOSERS[k][0].split()[-1]} — {w}" for k, w, _ in RECOMMENDED]
                k = pick("cornerstones of the canon", lbls, palette=palette_for())
                if k is None:
                    continue
                ckey, work, squery = RECOMMENDED[k]
                res = do_search(squery or f"{work} "
                                f"{COMPOSERS[ckey][0].split()[-1]}",
                                limit=6, which="all")
                if res:
                    run_queue([best_track(res, work)] + res[:2])
                continue
            elif i == 2:                                     # work mode
                try:
                    from .workmode import COLLECTIONS, WorkRunner
                    coll_names = list(COLLECTIONS)
                    L = pick("work canon - choose an era/recital", coll_names,
                             palette=palette_for())
                    if L is None:
                        continue
                    items = COLLECTIONS[coll_names[L]]
                    con().print(f"[bold]🧑‍💻 work mode[/] · [dim]{coll_names[L]} — "
                                "space: pause · n: skip · q: stop[/]")
                    WorkRunner(palette_for(), items=items).play_forever()
                except KeyboardInterrupt:
                    pass
                except Exception as exc:
                    con().print(f"[red]work mode hiccup:[/] {exc}")
                continue
            elif i == 3:                                     # random
                cmd_random(SimpleNamespace(name=[], max=False, list=False,
                                           limit=4, no_play=False))
                continue
            elif i == 4:                                     # composer pages
                pretty = [f"{COMPOSERS[key][0]} ({key})" for key in ORDER]
                k = pick("the 24 maestros", pretty, palette=palette_for())
                if k is None:
                    continue
                ckey = ORDER[k]
                works = list_masterpieces(ckey)
                subvals = [
                    f"👑 signature: {works[0] if works else '?'}",
                    "🎲 random famous work",
                    "ℹ️  enrichment: info + full page",
                    "←  back",
                ]
                j = pick(pretty[k], subvals, palette=palette_for(ckey))
                if j == 0:
                    cmd_random(SimpleNamespace(name=[ckey], max=True, list=False,
                                               limit=4, no_play=False))
                elif j == 1:
                    cmd_random(SimpleNamespace(name=[ckey], max=False, list=False,
                                               limit=4, no_play=False))
                elif j == 2:
                    _banner_key(ckey)
                    cmd_info(SimpleNamespace(name=ckey))
                continue
            elif i == 5:                                     # download
                q = _type("📥 download what: ")
                if q:
                    cmd_download(SimpleNamespace(query=q, limit=1, all=False,
                                                 src=None))
                continue
            elif i == 6:                                     # playlists
                from .playlists import Playlists, seed_presets
                P = Playlists()
                try:
                    seed_presets(P)
                except Exception:
                    pass
                names = P.list()
                opts = list(names) + ["✚  add: search a piece"]
                opts.append("☰  play a playlist")
                k = pick("playlists", opts, palette=palette_for())
                if k is None:
                    continue
                entry = opts[k]
                if entry == "✚  add: search a piece":
                    q = _type("search a piece to save: ")
                    nm = _type("playlist name: ")
                    if q and nm:
                        cmd_playlist(SimpleNamespace(playlist_cmd="add", name=nm,
                                                     query=[q], pick=1,
                                                     play=False))
                elif entry == "☰  play a playlist":
                    if names:
                        k2 = pick("which", names, palette=palette_for())
                        if k2 is not None:
                            cmd_playlist(SimpleNamespace(playlist_cmd="play",
                                                         name=names[k2]))
                continue
            elif i == 7:                                     # quiz
                cmd_quiz(SimpleNamespace(quiz_cmd="start", rounds=5, limit=5,
                                         src=None, fast=True))
                continue
            elif i == 8:                                     # theme
                names = list(THEMES)
                k = pick("themes", names, palette=palette_for())
                if k is None:
                    continue
                set_config(theme=names[k])
                con().print(f"[green]theme → {names[k]}[/]")
                continue
            elif i == 9:                                     # UI mode
                cur = get_ui_mode()
                k3 = pick("interaction tiers — arrows > numbers > typing",
                          ["arrow keys (questionary, cross-platform)",
                           "numbered list",
                           "typing"],
                          palette=menu_pal)
                if k3 is not None:
                    set_ui_mode(("arrow", "number", "type")[k3])
                continue
            elif i == 10:
                cmd_about(SimpleNamespace())
                continue
            else:
                return 0
        except KeyboardInterrupt:
            continue
        except SystemExit:
            return 0


def cmd_recommend(args):
    """sx recommend [composer] — cornerstones of the canon, instantly."""
    from .masterpieces import RECOMMENDED
    from .scoring import best_track
    pool = RECOMMENDED
    if args.name:
        key = match_composer(args.name)
        if key:
            subset = [(k, w, q) for k, w, q in RECOMMENDED if k == key]
            pool = subset or RECOMMENDED
            if not subset:
                con().print(f"[dim]no canon cornerstones for {key} — "
                            "playing one from the grand list[/]")
    if not pool:
        pool = RECOMMENDED
    key, work, squery = random.choice(pool)
    scl = palette_for(key)
    _banner_key(key)
    con().print(f"  🌟 [bold #{scl[1]}]RECOMMENDED[/] · "
                f"{COMPOSERS[key][0].split()[-1]} — {work}")
    query = squery or f"{work} {COMPOSERS[key][0].split()[-1]}"
    res = do_search(query, limit=6, which="all")
    if not res:
        con().print("[yellow]no recordings found — try `sx search`[/]")
        return 1
    best_res = best_track(res, work)
    first = best_track(res, work)
    ordered = [first] + [t for t in res if t is not first][:2]
    return run_queue(ordered[:3])


# ------------------------------------------------------------- playlist ----
def cmd_playlist(args):
    from .playlists import Playlists
    if not args.playlist_cmd:
        con().print("[bold]usage:[/] sx playlist list|add|show|play|delete|export")
        return
    pl = Playlists()
    if args.playlist_cmd == "list":
        for name in pl.list():
            tracks = pl.load(name) or []
            con().print(f"  {name:22s} → {len(tracks)} tracks")
    elif args.playlist_cmd == "add":
        query = " ".join(getattr(args, "query", []) or []) or args.name
        tracks = do_search(query, limit=8, which="archive")
        if not tracks:
            con().print("[yellow]no match[/]")
            return 1
        pick = min(max(int(getattr(args, "pick", 1) or 1), 1), len(tracks))
        t = tracks[pick - 1]
        # append to existing
        existing = pl.load(args.name) or []
        existing.append(t)
        pl.save(args.name, existing)
        con().print(f"[green]+[/] added to '{args.name}': {t.label}")
    elif args.playlist_cmd == "show":
        tracks = pl.load(args.name)
        if tracks is None:
            con().print(f"[red]no playlist '{args.name}'[/]")
            return 1
        _search_rows(tracks)
    elif args.playlist_cmd == "play":
        tracks = pl.load(args.name) or []
        if not tracks:
            con().print("[red]empty or missing playlist[/]")
            return 1
        return run_queue(tracks)
    elif args.playlist_cmd == "export":
        if not pl.path(args.name).exists():
            con().print("[red]unknown playlist[/]")
            return 1
        path = pl.export_m3u(args.name)
        con().print(f"[green]✓[/] exported to {path}")
    elif args.playlist_cmd == "delete":
        ok = pl.delete(args.name)
        con().print("[green]removed[/]" if ok else "[yellow]no such playlist[/]")
    return 0

# ------------------------------------------------------------------ info ---
def cmd_info(args):
    import symphonix.info as W
    key = match_composer(args.query)
    pal = palette_for(key)
    _banner_key(key) if key else _banner_key(random.choice(ORDER))
    data = W.find(args.query)
    if not data:
        con().print("[yellow]Wikipedia could not be reached[/]")
        return 1
    con().print(f"[bold #{pal[1]}]{data['title']}[/]  [dim]— Wikipedia[/]")
    con().print()
    words = data["extract"].split(". ")
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) > 96:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    for line in lines[:14]:
        con().print(" ", line, style="dim")
    if data.get("url"):
        con().print(f"  ↪ [underline]{data['url']}[/]")
    return 0

# ------------------------------------------------------------------ quiz ---
def cmd_quiz(args):
    pal = palette_for()
    from .anim import notes_rain
    p = _player()
    try:
        from .quiz import QuizRunner
    except Exception:
        con().print("[red]quiz crashed[/]")
        return 1
    class Ui:
        palette = staticmethod(palette_for)
        player = None
        def warn(self, msg):
            con().print(msg)
        def quiz_question(self, i, tot, era, first_init, opts):
            con().print()
            con().print(f"[bold #{pal[0]}][ round {i}/{tot} ][/] — [dim]{era}[/] — ♪ listening...")
            con().print(f"    [bold #ffffff]Q: which maestro is this?[/] (first letter hint: {first_init})")
            for j, opt in enumerate(opts, 1):
                con().print(f"      {j}. {COMPOSERS[opt][0]}")
            con()
        def quiz_reveal(self, key, correct, name, era, blurb):
            con().print()
            _banner_key(key)
            if correct:
                con().print(f"[bold green]✓ correct![/] {name} — {blurb}")
                notes_rain(pal, secs=0.9)
            else:
                con().print(f"[bold red]✗ miss![/] It was [bold]{name}[/] — {blurb}")
    Ui.player = p
    q = QuizRunner(Ui())
    score, rounds, best = q.run(rounds=args.rounds)
    cfg = get_config()
    newbest = int(cfg.get("best_quiz_score", 0) or 0)
    con().print(f"\n[bold]{score}/{rounds}[/] correct · "
                f"[gold1]{score / max(rounds, 1) * 100:.0f}%[/] · "
                f"[dim]best: {newbest}[/]")
    return 0

# ------------------------------------------------------------------ theme --
def _theme_preview(name, pal):
    con().print(f" [bold u]{name}[/]   {'  '.join('█' for _ in range(4))}",
                style=" ".join(pal))
    key = random.choice(ORDER)
    name_, era, blurb, art = COMPOSERS[key]
    from .anim import banner
    banner(key, pal, name=name_, era="", blurb="")

def cmd_theme(args):
    cfg = get_config()
    from rich.panel import Panel
    if args.theme_cmd == "list":
        for name, pal in THEMES.items():
            sw = " ".join(f"[bold {c}]██[/]" for c in pal)
            cur = " (current)" if cfg.get("theme") == name else ""
            con().print(f"  {name:12s} {sw}{cur}")
        if cfg.get("custom_colors"):
            sw = " ".join(f"[bold {c}]██[/]" for c in cfg["custom_colors"])
            con().print(f"  custom:      {sw} (active" if cfg.get("theme") == "custom" else f"  custom:      {sw}")
    elif args.theme_cmd == "set":
        if args.name not in THEMES:
            con().print(f"[red]unknown theme '{args.name}'[/] — see sx theme list")
            return 1
        set_config(theme=args.name)
        con().print(f"[green]theme → {args.name}[/]")
        if args.preview:
            _theme_preview(args.name, THEMES[args.name])
    elif args.theme_cmd == "custom":
        cols = list(args.colors or [])
        if not cols:
            con().print("[red]give 1-4 hex colors, e.g.  sx theme custom #ff0055 #ffb300 #fff8b0 #7c4dff[/]")
            return 1
        set_config(custom_colors=[c.lower() for c in cols], theme="custom")
        con().print("[green]custom colors set[/]")
        if args.preview:
            _theme_preview("custom", [c.lower() for c in cols])
    elif args.theme_cmd == "per":
        if args.name and args.colors:
            key = match_composer(args.name) or args.name.lower()
            ov = cfg.get("composer_overrides", {})
            ov[key] = [c.lower() for c in args.colors]
            set_config(composer_overrides=ov)
            con().print(f"[green]{key}[/] now uses {args.colors}")
        else:
            con().print("[red]use:  sx theme per beethoven #ff0000 #ffa000 #ffff00 #ffffff [/]")
    elif args.theme_cmd == "reset":
        set_config(theme="dawn", custom_colors=[], composer_overrides={})
        con().print("[green]reset to default[/]")
    elif args.theme_cmd == "show":
        pal = palette_for()
        _theme_preview(cfg.get("theme", "dawn"), pal)
    elif args.theme_cmd == "preview":
        for name, pal in THEMES.items():
            _theme_preview(name, pal)
    return 0


# ---------------------------------------------------------------- random ---
def cmd_random(args):
    name_tokens = list(getattr(args, "name", []) or [])
    max_mode = bool(getattr(args, "max", False))
    if name_tokens and name_tokens[0].lower() == "max":
        max_mode = True
        name_tokens = name_tokens[1:]
    name = " ".join(name_tokens).strip() or None
    try:
        key, query, label = compute_random_piece(name, max_mode=max_mode)
    except RandomNobody:
        from rich.table import Table
        con().print(f"[red]'{name}' is not one of the 24 maestros[/] — try one of:")
        con().print("[dim]" + " · ".join(MASTERPIECES) + "[/]")
        return 1
    scl = palette_for(key)
    _banner_key(key)
    icon = "👑" if max_mode else "🎲"
    con().print(f"  {icon} [bold #{scl[1]}]{label.upper()}[/]  ·  search: [dim]{query}[/]")
    if args.list:
        con().print("  [dim]masterpiece pool:[/]")
        for i, mw in enumerate(list_masterpieces(key), 1):
            con().print(f"    {i:2d}. {mw}".replace("1.", "★."))
        return 0
    tracks = fetch_tracks(key, query, limit=max(getattr(args, "limit", 4), 2))
    if not tracks:
        con().print("[yellow]...the world did not have that recording. Rolling again helps ;)[/]")
        return 1
    _search_rows(tracks)
    if getattr(args, "no_play", False):
        return 0
    return run_queue(tracks)


# ----------------------------------------------------------------- about ---
def cmd_about(args):
    from rich.panel import Panel
    from . import __repo__
    txt = (
        "  symphonix · terminal classical music finder & player\n"
        "  sources:  archive.org · musopen.org · imslp.org  (public-domain audio)\n"
        f"  repo:     {__repo__}\n"
        "  license:  GPL-3.0-or-later\n"
        "  engines:  miniaudio wheel → ffplay / mpv / mpg123\n"
        "  credits:  the librarians of three great PD music projects"
    )
    con().print(Panel(txt, border_style=palette_for()[0]))
    return 0

def cmd_doctor(args):
    import shutil
    con().print("[bold]environment checks[/]")
    try:
        import miniaudio
        con().print("  [green]✓[/] miniaudio audio wheel:", miniaudio.__version__)
    except Exception as x:
        con().print("  [red]✗ miniaudio missing:[/] install symphonix with pip")
    for exe in ("ffplay", "mpv", "mpg123"):
        if shutil.which(exe):
            con().print(f"  [green]✓[/] system fallback: {exe}")
    pal = palette_for()
    con().print(f"  ✓ theme: {get_config().get('theme')}")
    try:
        import requests
        r = requests.head("https://archive.org", timeout=(3, 8))
        con().print(f"  [green]{'✓' if r.status_code else '!'}[/]  archive.org reachable: HTTP {r.status_code}")
    except Exception as x:
        con().print("  [red]✗ network[/]", x)
    return 0

# ------------------------------------------------------------------- main --
def build_parser():
    ap = argparse.ArgumentParser(prog="sx", description=(
        "🎼 symphonix - find, play, download and use public-domain classical music"))
    ap.add_argument("--theme", help="override theme for this run", default=None)
    ap.add_argument("--fast", action="store_true", help="skip start screens")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("search", help="find recordings")
    p.add_argument("query")
    p.add_argument("--limit", "-n", type=int, default=10)
    p.add_argument("--src", choices=["all", "archive", "musopen", "imslp"], default="all")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--composer", default="")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("play", help="stream immediately (with animated equalizer)")
    p.add_argument("query", nargs="?", default=None, help="text query, url, or file")
    p.add_argument("--limit", "-n", type=int, default=5)
    p.add_argument("--src", choices=["all", "archive", "musopen", "imslp"], default="all")
    p.add_argument("--shuffle", action="store_true")
    p.add_argument("--playlist", "-P", default=None, help="play a saved playlist by name")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("download", help="download to local cache with progress")
    p.add_argument("query", help="query or direct url")
    p.add_argument("--limit", "-n", type=int, default=10)
    p.add_argument("--src", choices=["all", "archive", "musopen", "imslp"], default="all")
    p.add_argument("--all", action="store_true", help="grab multiple matches")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("cache", help="local download cache")
    p.add_argument("cache_cmd", nargs="?", choices=["list", "clear", "path"], default="list")
    p.set_defaults(func=cmd_cache)

    p = sub.add_parser("playlist", help="save / play playlists")
    p.add_argument("playlist_cmd", choices=["list", "add", "show", "play", "export", "delete"],
                   nargs="?", default="list")
    p.add_argument("name", nargs="?", help="playlist name")
    p.add_argument("query", nargs="*", help="search text for `add`")
    p.add_argument("--pick", "-k", type=int, default=1)
    p.set_defaults(func=cmd_playlist)

    p = sub.add_parser("quiz", help="guess-the-composer game")
    p.add_argument("--rounds", type=int, default=5)
    p.set_defaults(func=cmd_quiz)

    p = sub.add_parser("info", help="composer / program facts from Wikipedia")
    p.add_argument("query")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("theme", help="change all the app colors")
    p.add_argument("theme_cmd", choices=["list", "set", "custom", "show", "preview", "reset", "per"],
                   nargs="?", default="show")
    p.add_argument("name", nargs="?", help="theme name / composer for `per`")
    p.add_argument("colors", nargs="*", help="hex colors for custom/per")
    p.add_argument("--preview", "-p", action="store_true")
    p.set_defaults(func=cmd_theme)

    p = sub.add_parser("composers", help="the 24 composer portraits & infos")
    p.add_argument("--art", action="store_true", help="show portraits too")
    p.add_argument("--json", dest="jsonf", action="store_true")
    p.set_defaults(func=cmd_composers)

    p = sub.add_parser("banner", help="show composer art")
    p.add_argument("key", nargs="?", default=None, help="composer name/key")
    p.set_defaults(func=cmd_banner)

    p = sub.add_parser("work", help="🧑‍💻 endless focus loop of canon cornerstones")
    p.add_argument("collection", nargs="?", default="full canon")
    p.set_defaults(func=cmd_work)

    p = sub.add_parser("ui", help="🎛 control tier: arrow | num | type")
    p.add_argument("mode", nargs="?", default="")
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("menu", aliases=["m"],
                       help="🎛  the arrow-key concert hall (main UI)")
    p.set_defaults(func=cmd_menu)

    p = sub.add_parser("recommend", aliases=["rec"],
                       help="🌟 play a canon cornerstone (pass composer to filter)")
    p.add_argument("name", nargs="?", default="")
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("random", aliases=["randome", "rnd"],
                       help="♪ roulette: a random masterpiece by a random maestro")
    p.add_argument("name", nargs="*", help="composer name; prefix with `max` for the signature piece")
    p.add_argument("--max", action="store_true", help="the single signature masterpiece")
    p.add_argument("--list", "-l", action="store_true", help="show the composer's masterpiece pool")
    p.add_argument("--limit", "-n", type=int, default=4)
    p.add_argument("--no-play", action="store_true", help="show only, don't play")
    p.set_defaults(func=cmd_random)

    p = sub.add_parser("about", help="about symphonix / sources / license")
    p.set_defaults(func=cmd_about)

    p = sub.add_parser("doctor", help="check audio engine + network + theme")
    p.set_defaults(func=cmd_doctor)

    return ap

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        os.environ.setdefault("SYMPHONIX_THEME", getattr(args, "theme", "") or "")
        argsfunc = getattr(args, "func", cmd_default)
        if not hasattr(args, "func") or args.cmd == "default":
            cmd_default(args)
            return cmd_menu(args)
        ret = argsfunc(args)
    except KeyboardInterrupt:
        print()
        return 130
    return ret or 0

if __name__ == "__main__":
    sys.exit(main())
