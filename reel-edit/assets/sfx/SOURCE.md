# Sound effects

The default look plays a few soft sound effects, well under the voice: a **pop** when a white pill or a
card appears at the top, a **whoosh** as the face shrinks into a light screen, and on request a
**click** or a **ding** (a check mark, a result). No riser: it was removed on 10 Nov 2026.

The files are **not included** (most sound-effect licenses allow them in your videos but not sharing the
files). Put your own here, or in `local/sfx/` (checked first, never committed), named:

| File | Used for | Good choice |
|---|---|---|
| `pop.wav` | a pill or card arriving | a short, soft pop or bubble, under 0.6 s |
| `whoosh.wav` | the face shrinking into a light screen | a light air swish, about 0.5 s |
| `click.wav` | a click on a recording, on request | a mouse click |
| `ding.wav` | a check mark or a result, on request | a short bright ping |

Trim the silence at the start and peak-normalize each to -1 dBFS, for example:

    ffmpeg -i <file> -af "silenceremove=start_periods=1:start_threshold=-50dB" -ar 48000 -ac 2 pop.wav

build.py sets the level (pop -15 dB, whoosh -17, click -13, ding -15 under that peak). A missing file
is skipped with a note, nothing breaks. `AUTO_SFX = False` in a reel's `edit.py` turns the automatic
ones off; `SFX = [(time, "ding"), ...]` adds more.
