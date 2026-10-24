# 🎼 symphonix

> Find, play, download and **use** public-domain classical music — entirely from your terminal.
> 24 legendary composers. Animated ASCII portraits. A real-time equalizer driven by the actual audio.
> Works on **Linux, macOS, Windows — anything that runs Python.**

```
 pip install symphonix
```

---

## ⚡ quickstart

```bash
sx                       # splash screen + menu of ideas
sx search chopin nocturne        # colorful results table
sx play mozart requiem           # streams instantly + animated equalizer
sx download bach brandenburg     # download to a local cache
sx quiz                          # guess-the-composer game (music plays!)
sx theme vaporwave               # repaint the whole app
```

*Prefer not installing yet?* `python -m symphonix play bach air` works too.

## 🎨 the cool part — command tour

| command | what it does |
|---|---|
| `sx banner [bach]` | giant animated composer portrait (or a surprise one) |
| `sx composers --art` | the full gallery — 24 ASCII masterpieces, colored |
| `sx search <q> -n 10` | search archive.org + musopen + imslp at once |
| `sx search <q> --json` | JSON output → use in YOUR python projects |
| `sx play <q> --shuffle` | queue with real reactive equalizer + note animations |
| `keys during play` | `space` pause · `n` skip · `s` stop+next · `q` quit |
| `sx download <q> --all` | batch download withprogress bars |
| `sx cache list\|clear\|path` | manage the offline cache (~/.symphonix/cache) |
| `sx playlist add lofi <q>` `sx playlist play lofi` | save/replay lists; `.m3u` export for VLC |
| `sx info beethoven` | composer facts pulled from Wikipedia |
| `sx theme list\|set <t>\|custom <hex...>` | 🎨 full color control, even per-composer |
| `sx quiz --rounds 5` | music assassin: recording plays, you name the maestro |
| `sx doctor` | check audio engine, network, themes |

## 🌎 what "public domain" is used

Audio comes from three wonderful projects:

- **[archive.org](https://archive.org)** — 100k+ classical recordings, stable API, direct mp3/ogg/flac
- **[musopen.org](https://musopen.org)** — royalty-free recordings (their license icons still apply per track)
- **[imslp.org](https://imslp.org)** — the Petrucci Library: sheet music + community recordings

Composer facts via Wikipedia. All playback uses **miniaudio** (a pure pip wheel — no system
libraries needed). If the wheel is missing for your platform, symphonix automatically falls back
to `ffplay` / `mpv` / `mpg123` if installed.

## 🔌 use it inside your own python code

```python
from symphonix import search, Track

tracks = search("beethoven symphony 5", limit=3)
best: Track = tracks[0]

print(best.title, "|", best.composer, "|", best.url)
best.cache_path()       # stable local path after sx download
```

Also: `symphonix.player.Player` (play by track), `symphonix.art.COMPOSERS` (the portraits),
`symphonix.config.THEMES`. The CLI is just the tip.

## 🖥 platforms

| OS | status | notes |
|---|---|---|
| Linux | ✅ | pulseaudio/pipewire/alsa; falls back gracefully |
| macOS | ✅ | coreaudio via miniaudio wheel |
| Windows 10/11 | ✅ | WASAPI; rich does ANSI fine |

Requires just **Python 3.9+**.

## 🧪 development

```bash
git clone https://github.com/thisisforlearn/classical && cd classical
pip install -e .[dev]
pytest            # offline tests
pytest --live     # include home-tested network tests
```

## 🛟 licensing

`symphonix` is **GPL-3.0-or-later** (see LICENSE).

The recordings are public-domain *recordings* per their source, but every country's
implementation differs (especially on performance rights). Each track row shows the source;
`--json` includes the license URL when the upstream provides one. Do the polite thing and
respect whatever the source icon says.

## 🔴 the fun part

`cd classical && sx quiz` — the library plays a *real* recording, hides the composer, and
you guess. Highest score is saved on your machine forever. Beat it.
