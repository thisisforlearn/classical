"""Keyboard controls during playback (space=pause, n=next, s=stop)."""
import os
import sys
import threading

STOP, NEXT, PAUSE, BACK = "stop", "next", "pause", "back"

def _reader_unix(ctrl):
    import termios, tty
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == " ":
                queue.append(PAUSE)
            elif ch in ("n", "N", "s", "S", "d"):
                queue.append(NEXT if ch in ("n", "N") else STOP)
            elif ch in ("b", "p", "P"):
                queue.append(BACK)
            elif ch in ("q", "Q"):
                queue.append(STOP)
                break
            else:
                continue
    except Exception:
        pass
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass

class KeyController:
    """Async keyboard listener; only when stdin is a TTY."""
    def __init__(self):
        self.queue = []
        self.enabled = False
        self._thread = None

    def start(self):
        self.enabled = sys.stdin.isatty()
        if not self.enabled:
            return self
        try:
            self._thread = threading.Thread(target=_reader_unix, args=(self, None), daemon=True)
            self._thread.start()
            self._reader = _reader_unix
        except Exception:
            self.enabled = False
        return self

    def poll(self) -> "str | None":
        if self.queue:
            act = self.queue.pop(0)
            return act
        return None

    def stop(self):
        pass
