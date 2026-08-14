import os
import subprocess
import threading
import time

import numpy as np

TERMUX_PREFIX = '/data/data/com.termux/files/usr'


def termux_pacat():
    p = os.path.join(TERMUX_PREFIX, 'bin/pacat')
    return p if os.path.exists(p) else 'pacat'


def _to_stereo_bytes(mono):
    data = np.clip(np.repeat(mono, 2), -1.0, 1.0)
    return (data * 32767.0).astype(np.int16).tobytes()


class PacatSink:
    """live audio: stream s16le straight into pacat (termux pulseaudio)."""

    def __init__(self, engine, block=512):
        self.engine = engine
        self.block = block
        self.proc = None
        self.thread = None
        self.running = False

    def start(self):
        cmd = [termux_pacat(), '--playback', '--raw', '--format=s16le',
               f'--rate={self.engine.sr}', '--channels=2', '--latency-msec=120']
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise RuntimeError('pacat not found — run `pkg install pulseaudio` in termux')
        time.sleep(0.4)
        if self.proc.poll() is not None:
            raise RuntimeError('pulseaudio not reachable — in a real termux shell run: pulseaudio --start --exit-idle-time=-1')
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        interval = self.block / self.engine.sr
        nxt = time.monotonic()
        while self.running:
            mono = self.engine.tick(self.block)
            try:
                self.proc.stdin.write(_to_stereo_bytes(mono))
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError):
                break
            nxt += interval
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.proc:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.terminate()
            except Exception:
                pass


class NullSink:
    """silent sink: advances the clock at realtime pace, no audio (drift tests)."""

    def __init__(self, engine, block=512):
        self.engine = engine
        self.block = block
        self.thread = None
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        interval = self.block / self.engine.sr
        nxt = time.monotonic()
        while self.running:
            self.engine.tick(self.block)
            nxt += interval
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


class WavSink:
    """offline render: engine -> wav file. no audio device needed."""

    def __init__(self, engine, path, seconds):
        self.engine = engine
        self.path = path
        self.seconds = seconds

    def run(self):
        import wave
        total = int(self.engine.sr * self.seconds)
        chunks = []
        done = 0
        block = 4096
        while done < total:
            n = min(block, total - done)
            chunks.append(self.engine.tick(n))
            done += n
        audio = np.concatenate(chunks)
        data = np.clip(audio, -1.0, 1.0)
        with wave.open(self.path, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.engine.sr)
            w.writeframes((data * 32767.0).astype(np.int16).tobytes())
        return len(audio) / self.engine.sr


def make_live_sink(engine, block=512):
    return PacatSink(engine, block)
