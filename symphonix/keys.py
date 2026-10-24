"""Keyboard controls during playback (space=pause, n=next, s=stop, q=quit)
plus a cross-platform raw key reader used by the arrow-key menu.

Windows: msvcrt getch (arrow = 0xE0/0x00 prefix + scan code 72/80/75/77)
Unix:    termios cbreak mode (arrow = ESC + '[' + 'A'/'B'/'C'/'D')
"""
import os
import sys
import threading

STOP, NEXT, PAUSE, BACK = "stop", "next", "pause", "back"
ACTIONS = {"up", "down", "left", "right", "enter", "space", "esc",
           "q", "n", "s", "b", "p", "d", "j", "k", "quit"}


def _norm_char(ch):
    return {
        " ": "space", "\r": "enter", "\n": "enter", "\x1b": "esc",
        "n": "n", "N": "n", "j": "j", "k": "k",
        "s": "s", "S": "s", "d": "d", "q": "q", "Q": "q",
        "b": "b", "p": "p", "P": "p",
    }.get(ch, ch)


def _drain_csi():
    """Unix: swallow the 2 remaining chars of an ESC-queue like ESC[A."""
    import select
    r, _, _ = select.select([sys.stdin], [], [], 0.06)
    if not r:
        return None
    b2 = sys.stdin.read(1)
    b3 = sys.stdin.read(1) if select.select([sys.stdin], [], [], 0.0)[0] else ""
    key = (b2 or "") + (b3 or "")
    return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(key, "esc")


read_key = None

if sys.platform.startswith("win") and os.name == "nt":
    def read_key():
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            code = msvcrt.getch()
            return {b"H": "up", b"P": "down", b"K": "left",
                    b"M": "right"}.get(code, "esc")
        if ch == b"\r":
            return "enter"
        if ch == b" ":
            return "space"
        if ch == b"\x1b":
            return "esc"
        try:
            return _norm_char(ch.decode("ascii", "ignore"))
        except Exception:
            return "esc"
else:
    def read_key():
        import termios
        fd = sys.stdin.fileno()
        try:
            ch = sys.stdin.read(1)
        except Exception:
            return None
        if ch == "\x1b":
            sub = _drain_csi()
            if sub is None:
                return "esc"
            return sub
        return _norm_char(ch)


def _reader_unix(ctrl, *_):
    import termios, tty  # noqa: F403
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        tty.setcbreak(fd)
        while True:
            key = read_key()
            if key is None:
                break
            if key == "space":
                ctrl.queue.append(PAUSE)
            elif key in ("n",):
                ctrl.queue.append(NEXT)
            elif key in ("s", "d"):
                ctrl.queue.append(STOP)
            elif key in ("b", "p"):
                ctrl.queue.append(BACK)
            elif key == "q":
                ctrl.queue.append(STOP)
                break
            elif key in ("esc", ""):
                continue
    except Exception:
        pass
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass


def _reader_win(ctrl, *_):
    while True:
        try:
            key = read_key()
        except Exception:
            break
        if key is None:
            continue
        if key == "space":
            ctrl.queue.append(PAUSE)
        elif key == "n":
            ctrl.queue.append(NEXT)
        elif key in ("s", "d"):
            ctrl.queue.append(STOP)
        elif key in ("b", "p"):
            ctrl.queue.append(BACK)
        elif key in ("q", "esc"):
            ctrl.queue.append(STOP)
            break


class KeyController:
    """Async keyboard listener; only when stdin is a TTY."""

    def __init__(self):
        self.queue = []
        self.enabled = False
        self._thread = None

    def start(self):
        self.enabled = False
        try:
            tty_ok = sys.stdin.isatty()
        except Exception:
            tty_ok = False
        if not tty_ok:
            return self
        reader = _reader_win if sys.platform.startswith("win") else _reader_unix
        try:
            self._thread = threading.Thread(target=reader, args=(self,), daemon=True)
            self._thread.start()
            self.enabled = True
        except Exception:
            self.enabled = False
        return self

    def poll(self) -> "str | None":
        if self.queue:
            return self.queue.pop(0)
        return None

    def stop(self):
        self.queue.append(STOP)
