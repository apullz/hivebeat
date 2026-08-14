# hivebeat (◕‿◕✿)

a live-coding music synth that runs in a terminal. type a pattern, it loops forever, you tweak it live. square/saw/fm/pad melodies, euclidean drum grooves, chiptune or ambient — all from a tiny language of our own.

```
  _  _ _   ___  ___  _    ___  _____ ___     _  _
 | || | | | __|/ __|| |_ | __||_   _| __|   | |/ /
 | __ | |_| _| \__ \| ' \| _|   | | | _|    |   <
 |_||_|___|___||___/|_||_|___|  |_| |___|   |_|\_\   ...the hive is humming
```

## quickstart

**for sound, run this from a real termux shell (not inside proot):**

```
bash setup_termux.sh     # pkg install python python-numpy pulseaudio; starts the daemon
./hivebeat               # the live repl
```

**no sound device handy? render to wav instead (works anywhere):**

```
python3 render.py out.wav 8 \
  "drums >> kick(euclid(3,8), dur=0.25)" \
  "p1 >> square(\"c4 e4 g4 a4\", dur=0.25)"
```

then `./play.sh out.wav 8 "p1 >> saw(\"c2 e2\", dur=1)"` tries to auto-open it on android.

## the language

```
p1 >> square("c4 e4 g4 a4", dur=0.25)      melodic pattern (rests: . rest r)
p1 >> saw("c2 g2 [c3 e3 g3]", dur=1)       chords with [ ]
bass >> saw("c2 g2 a1 e2", dur=0.5)        reassign any player live
drums >> kick("x . x . x x . .", dur=0.5)  drum hits: x hit, . rest
hat >> hat(euclid(5, 8), dur=0.25)         euclidean rhythm: 5 hits over 8 steps

bpm(128)      change tempo
stop / hush   silence
?             help
exit / ctrl-c leave
```

params (comma-separated): `dur`, `step`, `delay`, `amp`, plus per-instrument ones — `fm(ratio, index)`, `square(saw)(detune, duty, tau)`, `kick(f0, f1)`, `pad(detune)`.

instruments: `square  saw  fm  pad  kick  snare  hat`

## architecture

| module | job |
|---|---|
| `audio.py` | sinks: `PacatSink` (live → termux pulseaudio), `WavSink` (offline render), `NullSink` (realtime clock, silent) |
| `live.py` | `Engine`: sample-accurate cycle scheduler + tanh limiter. players swap at cycle boundaries — no glitches |
| `dsl.py` | tiny parser → `PlayerDef` (note/chord/drum/euclid tokens, cycling dur/step) |
| `instruments.py` | stateless numpy synths: square, saw, fm, pad, kick, snare, hat |
| `pattern.py` | note→freq + bjorklund euclidean rhythms |

## why no supercollider/tidal/sonic-pi?

they all need scsynth, which doesn't run on termux/android. so hivebeat is its own engine: pure python + numpy, sample-accurate scheduler (sorensen & gardner's temporal-recursion style), stateless instruments.

## notes

- inside proot, termux pulseaudio can't start (android tagged-pointer + proot self-exec check). the repl auto-detects and falls back to a silent clock — do live audio from a **real termux shell**.
- v0.1: no envelopes-as-params yet, no midi, mono (stereo at the sink).
