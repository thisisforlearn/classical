"""Streaming playback with a reactive level meter.

Primary engine: miniaudio (pure pip wheel, no OS dependencies) - decodes the
music file *while it is still downloading*, so `sx play` feels instant.
Fallback engine: ffplay / mpv / mpg123 when miniaudio is unavailable.
"""
import math
import os
import re
import shutil
import subprocess
import threading
import time
from collections import deque

from importlib import import_module

try:
    import miniaudio                     # noqa: F401
    HAS_MINIAUDIO = True
except Exception:
    HAS_MINIAUDIO = False


def _fmod(name):
    return import_module(f"symphonix.sources.{name}")


def find_system_player():
    for exe in ("ffplay", "mpv", "mpg123"):
        if shutil.which(exe):
            return exe
    return None


class Player:
    """One track at a time; the CLI polls state + `levels` for animations."""

    def __init__(self):
        self.track = None
        self.proc = None
        self.device = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._thread = None
        self._dl_thread = None
        self.levels = deque(maxlen=40)      # normalized 0..1, for equalizer
        self.elapsed = 0.0
        self.duration = 0.0
        self.status = "idle"                # idle|buffering|streaming|playing|paused
        self.finished = threading.Event()
        self.error = None
        self.engine = ("miniaudio" if HAS_MINIAUDIO
                       else (find_system_player() or "none"))
        self._duration_estimate = 0.0

    # ----------------------------------------------------------------- api
    def play(self, track, path=None):
        self.stop()
        self.track = track
        self._stop.clear()
        self._pause.clear()
        self.levels.clear()
        self.elapsed = 0.0
        self.status = "buffering"
        self.finished.clear()
        self.error = None
        self.track = track
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        self._pause.set()
        self.status = "paused"

    def resume(self):
        self._pause.clear()
        self.status = "playing"

    def toggle(self):
        if self._pause.is_set():
            self.resume()
        else:
            self.pause()

    def stop(self):
        self._stop.set()
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
        t, self._thread = self._thread, None
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=4.0)
        d, self.device = self.device, None
        if d is not None:
            try:
                d.close()
            except Exception:
                pass
        self.status = "idle"

    @property
    def is_busy(self):
        return bool(self._thread and self._thread.is_alive() and not self.finished.is_set())

    def level(self) -> float:
        if not self.levels:
            return 0.0
        return sum(self.levels) / len(self.levels)

    # ------------------------------------------------------------ internals
    def _run(self):
        track = self.track
        try:
            cached = track.cache_path()
            local = track.url if track.url else None
            if local and local.startswith("http"):
                if cached.exists() and cached.stat().st_size > 0:
                    self._play_file(track, str(cached))
                    return
                if self.engine == "miniaudio" or HAS_MINIAUDIO:
                    self._play_stream(track, cached)
                    return
                self._fallback(track, str(cached), stream=True)
                return
            # direct path / already downloaded
            self._play_file(track, local or track.filename or str(cached))
        except Exception as exc:
            self.error = str(exc) or repr(exc)
            self.status = "error"
            self.finished.set()

    # ---------------- miniaudio: file on disk (fully or partially there) ----
    def _play_file(self, track, path):
        if track.duration and ":" in track.duration:
            m, s = track.duration.split(":")[:2]
            self.duration = int(m) * 60 + float(s)
        if not self.duration:
            self.duration = self._guess_duration(path)
        chunks = miniaudio.stream_file(
            str(path), output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=2, sample_rate=44100, frames_to_read=1024)
        metered = self._metered(chunks)
        next(metered)
        self.device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=2, sample_rate=44100)
        self.device.start(metered)
        self.status = "playing"
        try:
            last_elapsed, idle_since = 0.0, time.time()
            while not self._stop.is_set():
                time.sleep(0.05)
                if self._pause.is_set():
                    idle_since = time.time()
                    continue
                if abs(self.elapsed - last_elapsed) > 0.02:
                    last_elapsed = self.elapsed
                    idle_since = time.time()
                    continue
                # decoder idle > 1.4s -> the file is fully played
                if time.time() - idle_since > 1.4:
                    break
        finally:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None
            self.finished.set()

    def _metered(self, chunks):
        """Audio device callback: pull PCM, measure RMS, ship to speaker."""
        import array
        out = b""
        while True:
            frames = yield out
            if self._pause.is_set():
                out = b"\x00\x00" * (max(frames or 0, 1) * 2)
                continue
            try:
                chunk = chunks.send(max(frames or 1, 1))
            except StopIteration:
                out = b""
                continue
            except Exception:
                out = b""
                continue
            if isinstance(chunk, array.array) and chunk.typecode == "h":
                data = chunk
            else:
                data = memoryview(chunk).cast("h")
            step = max(len(data) // 80, 1)
            s = data[::step]
            rms = math.sqrt(sum(float(v) * float(v) for v in s) / max(len(s), 1)) / 32768.0
            self.levels.append(min(rms, 1.0))
            self.elapsed += len(data) / 2 / 44100.0   # stereo int16 frames
            out = chunk

    # ---------------- miniaudio: progressive download-while-streaming ------
    def _play_stream(self, track, path, min_buffer=512 * 1024):
        dl_mod = import_module("symphonix.downloader")
        head = None
        try:
            head = dl_mod.content_size(track.url)
        except Exception:
            head = 0
        total = head or 0
        self._duration_estimate = (total / (128000 / 8)) if total else 0
        self._dl_thread = threading.Thread(
            target=self._download, args=(track, str(path)), daemon=True)
        self._dl_thread.start()
        target = min_buffer if not total else min(min_buffer, total * 0.95 or min_buffer)
        deadline = time.time() + 40
        while (not path.exists() or path.stat().st_size < target) and not self._stop.is_set():
            if time.time() > deadline:
                break
            if self._dl_thread and not self._dl_thread.is_alive():
                break
            time.sleep(0.08)
        wrapped = None
        played_frames = 0
        self.status = "playing"
        while not self._stop.is_set():
            if not path.exists():
                break
            try:
                chunks = miniaudio.stream_file(
                    str(path), output_format=miniaudio.SampleFormat.SIGNED16,
                    nchannels=2, sample_rate=44100, frames_to_read=1024,
                    seek_frame=played_frames)
            except Exception:
                time.sleep(0.2)
                continue
            metered = self._metered(chunks)
            next(metered)
            self.device = miniaudio.PlaybackDevice(
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=2, sample_rate=44100)
            self.device.start(metered)
            # watch for decoder starving (download slower than playback)
            stable_since = time.time()

            def size_now():
                try:
                    return path.stat().st_size
                except OSError:
                    return 0

            last_size, idle_since = size_now(), time.time()
            while not self._stop.is_set():
                time.sleep(0.05)
                growth = size_now()
                if growth != last_size:
                    last_size, idle_since = growth, time.time()
                    continue
                if time.time() - idle_since > 1.0:
                    break          # 1s of no new bytes: decoder starving
            if self.device:
                try:
                    self.device.close()
                except Exception:
                    pass
            self.device = None
            played_frames = int(self.elapsed * 44100)
            dl_alive = self._dl_thread and self._dl_thread.is_alive()
            if not dl_alive and not self._download.is_written_complete:
                break
            if not dl_alive:
                break
            # anti-glitch: before re-opening the decoder, let the file gain a
            # little head-room so we don't thrash open/close on slow links
            played_bytes = played_frames * 4
            waited = 0.0
            while not self._stop.is_set() and waited < 4.0:
                have = size_now() - played_bytes
                if have >= 384 * 1024 or not dl_alive:
                    break
                time.sleep(0.06)
                waited += 0.06
            time.sleep(0.04)      # wait for a bit to ensure download
        self._stop.set()
        if self._dl_thread and self._dl_thread.is_alive():
            self._dl_thread.join(timeout=3)
        self.status = "finished"
        self.finished.set()

    # ------------------------------------------------------------- download
    class _Download:
        def __init__(self):
            self.written = 0
            self.total = 0
            self.is_written_complete = False

    def _download(self, track, path):
        self._download_obj = self._DownloadObj = self._Download()
        obj = self._download_obj
        dl_mod = import_module("symphonix.downloader")
        # keep at most this many bytes ahead of what the listener has heard
        # (128 kbps => 16000 bytes per second of audio); polite to bandwidth.
        ahead_bytes = max(512 * 1024, 30 * 16000)
        rate = 16000.0
        try:
            def on_progress(written, total, speed):
                obj.written, obj.total = written, total
                # throttle: wait until the playhead catches up
                while not self._stop.is_set():
                    playhead = int(getattr(self, "elapsed", 0.0) * rate)
                    if written - playhead <= ahead_bytes:
                        break
                    time.sleep(0.06)

            dl_mod.stream_to_file(track.url, path, on_progress=on_progress)
            obj.is_written_complete = True
        except Exception as exc:
            self.error = str(exc)

    # ------------------------------------------------------------- fallback
    def _fallback(self, track, src, stream=False):
        exe = find_system_player()
        path = src if os.path.exists(src) or stream else None
        target = src if stream else (track.url or src)
        cmd_map = {
            "ffplay": ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", target],
            "mpv":    ["mpv", "--no-video", "--no-terminal", "--really-quiet", target],
            "mpg123": ["mpg123", "-q", target],
        }
        cmd = cmd_map.get(exe)
        if not cmd:
            self.error = ("no audio engine: install ffmpeg (ffplay/mpv), or reinstall "
                          "symphonix so the miniaudio wheel matches your python")
            self.status = "error"
            self.finished.set()
            return
        self.duration = self._guess_duration(target if not stream else None)
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,
                                         stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            self.error = f"`{exe}` not found"
            self.status = "error"
            self.finished.set()
            return
        self.status = "playing"
        t0 = time.time()
        while self.proc and self.proc.poll() is None:
            if self._stop.is_set():
                try:
                    self.proc.terminate()
                except Exception:
                    pass
                break
            # synthesized level visual for fallback engines
            lvl = abs(math.sin(time.time() * 2.3)) * 0.8 + 0.1
            self.levels.append(min(lvl, 1.0))
            self.elapsed = time.time() - t0
            time.sleep(0.07)
        self.status = "finished"
        self.finished.set()

    # ------------------------------------------------------------ utilities
    @staticmethod
    def _guess_duration(path) -> float:
        try:
            info = miniaudio.get_file_info(str(path))
            if getattr(info, "duration", 0):
                return float(info.duration)
        except Exception:
            pass
        try:
            size = os.path.getsize(str(path))
        except OSError:
            return 240.0
        return max(size / (128000 / 8), 1.0)
