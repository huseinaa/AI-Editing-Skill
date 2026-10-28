---
name: reel-edit
description: Edit filmed talking-head takes into a finished vertical reel (Instagram Reels, YouTube Shorts, TikTok). Joins the takes, cuts the dead air, cleans and levels the voice, writes captions from the real audio synced to each word, picks an edit style (CLEAN, PUNCH, EXPLAINER, DEMO, OFFER), adds a text hook, branded graphics, B-roll, zooms and a cover, all inside the safe zone, and exports a 1080x1920 file. Use when the user gives a recorded video or a folder of takes and asks to edit it, caption it, add a hook, graphics or B-roll, make a cover, or types /reel-edit.
---

# /reel-edit

Takes in, finished reel out. The words are yours: this skill owns everything on screen.

## How to call it

The only required input is the video or the reel's folder. Everything else has a default.

```
/reel-edit "Reels/My first reel"
/reel-edit "talk.mp4" style=explainer hook="Your app is not ready"
```

**A reel folder** holds the camera takes, in any number, joined in the order they were filmed. Takes
are the `.mov` files (iPhone); in a folder with no `.mov` (Android `.mp4`), every video is a take. A
video whose name starts with `broll` is B-roll, and the rest of its name says what it shows. Images in
the folder can be used as pop-in visuals.

| Input | Values | Default |
|---|---|---|
| `style=` | `clean` · `punch` · `explainer` · `demo` · `offer` (or a combo) | picked from the transcript, stated in one line |
| `hook=` | the on-screen hook text | 3 written, best one used |
| script | paste the script | none. Only a spelling guide and a source for the hook |
| `broll=` | files or a folder, one line on what each shows | the non-take videos in the folder |
| `captions=` | `en` · `ar` (Arabic letters, English terms kept Latin) · other | `caption_language` in brand.json |
| `cta=` | `follow` · `send` · a keyword | follow |
| `cover=` | the cover title, or `off` | a cover is always made |

**Never stall on a missing input.** Pick the default, say which one in one line, deliver the video.
The user iterates on the result ("make the list slower", "change the hook"), which is cheap.

---

## Step 0: Brand and context (every run)

1. **`brand.json`** at the skill root holds the user's brand: colors, fonts, logo, follow line,
   caption language, browser. Every graphic and cover reads it. If it still has the default values
   and the user has a brand, ask once for their colors, fonts and logo and fill it in.
2. Read `STYLES.md` (the five styles and the visual idea bank) and `deltas.md` if it exists (what the
   user corrected in past edits).
3. If the user keeps a script or notes for this reel (a doc, a note, a pasted script), read it: it
   gives the order of the takes, the spelling of their words, the text hook and where B-roll goes.

First run on a machine: `python scripts/doctor.py`. It lists anything missing with the fix.

`S` below = this skill's `scripts/` folder. Work dir: `<reel folder>/.reel-edit/` (or any temp folder).

## Step 1: Assemble the takes and cut

```
python S/assemble.py "<reel folder>" <workdir>          # joins every take in filming order
python S/transcribe.py <workdir>/master.mp4 <workdir>   # --lang en|ar|...
```

Read `words.txt` against the script, write `<workdir>/cuts.txt`, and run assemble again with it:

```
drop CGAK5759                      # a line said again in a later take: keep the last complete one
trim VVTY3909 from=0.52 to=10.74   # 0.04s before the first word, 0.06s after the last
order VVTY3909 EGHA4017            # only when the takes were filmed out of script order
keep ORME2737 0.27-7.16 9.47-11.62 # one long take: only these stretches stay
tail 0.15                          # only if a hand moves inside the default 0.3s end tail
python S/assemble.py "<reel folder>" <workdir> --cuts <workdir>/cuts.txt
```

**Cut a take at its start and end only.** Cut 0.04 s before the first word and 0.06 s after the
last, measured by loudness (20 ms windows, loud = within 24 dB of the take's peak), not by the
transcript. A short pause inside a take stays, especially the small breaths between the items of a
spoken list: they are the rhythm. Only cut inside a take for a retake (a sentence said twice: keep
the last complete one), a false start, or a long pause of a second or more (a single-take list reel
with 1 to 3 s between points). Then look at the frames around every join in 0.1 s steps and move a
cut in if a hand reaches for the phone.

**The very end keeps 0.3 s after the last word**, so the word finishes. assemble.py does this by
itself and prints `end tail:`.

**The voice is cleaned and leveled on every take, automatically:** highpass, RNNoise, a gentle
expander for room echo, a fixed gain to **-14 LUFS**, a limiter at -1.5 dBFS. No compressor (it can
make Whisper translate Arabic speech to English; transcribe.py warns if that happens). A take the chain
hurts: `voice raw <take>` in cuts.txt.

Then transcribe the final master again. **Every caption and visual is timed on that transcript.**

To change a cut after captions and cards are written: save `takes.json` and `edit.py`, re-run
assemble, then `python S/retime.py <workdir> <old takes.json>` moves every time in edit.py.

## Step 2: Captions from the audio, never from the script

People change wording on camera. **The transcript is the truth, the script is a spelling guide.**

- 4 to 5 words per chunk, **one line**. Every chunk starts on a word's start time.
- Arabic: Arabic letters, English terms stay Latin (app, AI, UI...).
- Where a word is unclear, re-decode that stretch, pick the most likely, and **list it** in the
  report with its timestamp. Never silently guess.

## Step 3: Style, hook, beat plan, zooms

1. **Style** in one line, using the tree in `STYLES.md`.
2. **Hook.** 7 words max, one highlighted word, complementing (not repeating) the first spoken line.
   Write 3, use the best, list the other two.
3. **Beat plan.** Walk the transcript line by line and pick a visual from the idea bank. Every visual
   starts on the word that triggers it. Lists build item by item. Face on punchlines. Density check.
4. **Zooms** (talking heads): a `"hook"` zoom over the spoken hook with the riser, at most one
   `"in"`/`"out"` pair on a reflective line and its realization, and `PUNCH` hard zooms on emphasis
   lines (no closer than ~4 s, never two in a row). Never zoom a stretch covered by a full screen or
   split panel.

## Step 4: Write edit.py

Copy `examples/ui-ux-explanation/edit.py` as the template. Set `VIDEO` to `<workdir>/master.mp4` and
`OUTPUT` to `<reel folder>/<folder name> - edited.mp4`. The contract is at the top of
`scripts/reel_edit/project.py`, the components are in `scripts/reel_edit/components.py`. Use the
components before writing new HTML, and build anything new from the same tokens.

- **A list reel** ("7 signs...", "5 rules..."): `examples/list-reel/edit.py`. The number in the title
  is the number of points actually said.
- **A clip you react to:** `broll(path, mode="bottom")`, whole and uncropped, under the face. Talking
  over it: muted. Watching it then speaking: `audio=True`.
- **Images that pop in** (examples you describe but didn't film): `broll("<image>.png", mode="bottom")`,
  or an `overlay()` with an `<img>` for a transparent sticker.
- **Full screens with your face in a small circle:** `FACE_PIP` as a list of windows, each
  `{"crop": square, "box": (x, y, 300, 300), "window": (s, e), "shape": "circle"}`, and the captions
  in those windows styled `{"y": 1830}` so they sit under the circle.
- **Moving captions** (an optional style): `(start, "text", {"y": .., "x": .., "scale": ..})` per
  caption, `{word}` in the text draws that word big.
- **Private details on screen** (emails, keys): `BLUR = [(start, end, (x, y, w, h))]`.

Hard layout rules the renderer does not enforce:
- Everything inside the safe box: x 90 to 1350, y 360 to 1920 on the 1440x2560 master.
- No card covers the eyes. Cards sit from y 260, above the head; a tall card moves up or shrinks.
- Split panel content ends by ~560 px (the caption sits in the panel at y 1845).
- One highlight-color element per visual. The error color only for broken or wrong states.
- Consecutive states of one graphic keep shared elements in the same place, or the crossfade ghosts.
- A visual that starts at 0 is there on frame one (no fade in).

## Step 5: Render, build, check

```
python S/render.py <workdir>    # every visual and caption to PNG (re-render some: ... id1 id2 caps)
python S/build.py  <workdir>    # the video; prints loudness (target -14 LUFS, true peak <= -1 dBTP)
python S/check.py  <workdir>    # contact sheets with the safe box drawn, and the first-frame check
```

**Open the check sheets and look at every one before reporting.** Fix and rebuild until nothing
crosses the safe box, no caption overlaps a graphic, nothing jumps between states, and every caption
is one line. **Frame one must be the real picture** (face, hook, first caption): a `WARNING` from
check.py means fix and rebuild.

## Step 6: Cover

```
python S/cover.py <workdir> --title "Two Lines Max|*One Highlighted Line*" --frame <seconds> --out "<folder>/<name> - cover.jpg"
```

A frame of you (smiling, eyes on the lens, not mid-word: pull frames every 0.4 s and pick by eye),
your logo top centre, a fade in your primary color, the title on boxes. Open
`<workdir>/cover/cover-check.jpg`: the whole title must sit inside the 4:5 grid view and under the chin.

## Step 7: YouTube copy (only when the reel ends on a comment-a-keyword ask)

A keyword ask only works where your comment automation runs. Set `YOUTUBE_END` in edit.py to 0.3 s
after the last word before the ask (or the quietest point of a shorter gap), then
`python S/build.py <workdir> --youtube`. Follow, save and send asks stay; no second copy needed.

## Optional: three hook versions

Film three openings and one body, edit version A in full, then
`python S/variants.py <workdir-A> B <opening take> --from .. --to ..` builds B and C with the same
body, for testing which hook wins.

## Step 8: Report

Lead with the file. Then: path and size, loudness, cover path and title (+2 alternates), style and
why, hook (+2 alternates), the beat plan as a short table, words to check with timestamps, anything
skipped or assumed, the takes used and any dropped.

## Learning from feedback

When the user corrects an edit: fix it, then add the lesson to `deltas.md` in this folder (date,
reel, what they said, the rule it implies). The second time the same lesson comes up, write it into
this file as a rule. One correction is a preference, two is a rule.

## Setup notes

- Needs ffmpeg, Python with `faster-whisper playwright pillow numpy`, Microsoft Edge or Google Chrome
  (set `"browser"` in brand.json), and the Whisper **small** model in `~/.cache/faster-whisper-small`.
- Rendering pulls fonts from Google Fonts, so it needs internet.
