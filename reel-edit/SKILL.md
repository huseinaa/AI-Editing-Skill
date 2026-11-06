---
name: reel-edit
description: Edit filmed talking-head takes into a finished vertical reel (Instagram Reels, YouTube Shorts, TikTok). Joins the takes, cuts the dead air, cleans and levels the voice, writes captions from the real audio synced to each word, picks an edit style (CLEAN, PUNCH, EXPLAINER, DEMO, OFFER), adds a text hook, branded graphics, real screen recordings, B-roll, zooms and a cover, all inside the safe zone, and exports a 1080x1920 file. Can also study reels the user likes and learn their style without copying them. Use when the user gives a recorded video or a folder of takes and asks to edit it, caption it, add a hook, graphics or B-roll, make a cover, learn a style from reference reels, or types /reel-edit.
---

# /reel-edit

Takes in, finished reel out. The words are yours: this skill owns everything on screen.

## How to call it

The only required input is the video or the reel's folder. Everything else has a default.

```
/reel-edit "Reels/My first reel"
/reel-edit "talk.mp4" style=explainer hook="Your app is not ready"
/reel-edit references https://www.instagram.com/reel/... https://www.instagram.com/reel/...
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
| `captions=` | `en` · `ar` (Arabic letters, English terms kept Latin) · other | `caption_language` in the brand |
| `cta=` | `follow` · `send` · a keyword | follow |
| `cover=` | the cover title, or `off` | a cover is always made |

**Never stall on a missing input.** Pick the default, say which one in one line, deliver the video.
The user iterates on the result ("make the list slower", "change the hook"), which is cheap.

---

## Step 0: Brand, workflow and context (every run)

1. **`local/WORKFLOW.md`**, if it exists, is the user's own process (where their scripts live, where
   finished reels are filed, which CTAs they use, extra steps). **Read it first. Its rules extend and
   override this file.** `local/` is never committed, so a pull never touches it.
2. **The brand.** `brand.json` at the skill root holds the defaults, and `local/brand.json` is laid on
   top of it: colors, fonts, logo, follow line, caption language, browser. Every graphic and cover
   reads it. If neither has the user's values and the user has a brand, ask once for their colors,
   fonts and logo and write them into `local/brand.json`.
3. Read `STYLES.md` (the five styles and the visual idea bank), `deltas.md` if it exists (what the
   user corrected in past edits), `local/style.md` if it exists (what was learned from their
   reference reels, see "Learn a style from reference reels"), and the
   [reference lessons](references/natural-editing.md), including the complete 15-rule coverage table.
   Order of authority when they disagree: the user's explicit request now, then `local/WORKFLOW.md`
   and `deltas.md`, then this file, then `local/style.md`.
4. If the user keeps a script or notes for this reel (a doc, a note, a pasted script), read it: it
   gives the order of the takes, the spelling of their words, the text hook and where B-roll goes.
5. Before cutting the next reel, read any unlearned exported `history/*.json` from cut review.
   Follow [cut-review.md](references/cut-review.md) to record observed lessons without guessing intent.

First run on a machine: `python scripts/doctor.py`. It lists anything missing with the fix.

`S` below = this skill's `scripts/` folder. Work dir: `<reel folder>/.reel-edit/` (or any temp folder,
or where `local/WORKFLOW.md` says).

## Step 1: Assemble the takes and cut

```
python S/assemble.py "<reel folder>" <workdir>          # joins every take in filming order
python S/transcribe.py <workdir>/master.mp4 <workdir>   # --lang en|ar|...
```

Read `words.txt` against the script, write `<workdir>/cuts.txt`, and run assemble again with it:

```
drop CGAK5759                      # a line said again in a later take: keep the last complete one
trim VVTY3909 from=0.52 to=10.74   # 0.04s before the first word, 0.06s after the last
trim "Sitemap (2)" from=0.4 to=6.1 # quote a take name that has spaces
order VVTY3909 EGHA4017            # only when the takes were filmed out of script order
keep ORME2737 0.27-7.16 9.47-11.62 # one long take: only these stretches stay
tail 0.15                          # only if a hand moves inside the default 0.3s end tail
python S/assemble.py "<reel folder>" <workdir> --cuts <workdir>/cuts.txt
```

**Cut a take at its start and end only.** Write a `trim`, not a `keep`, unless the take holds a retake
(a sentence said twice: keep the last complete one, or the first when it cuts cleanly on a silence), a
false start or stumble, or a long pause of a second or more (a single-take list reel with 1 to 3 s
between points). A short pause inside a take stays, especially the small breaths between the items of
a spoken list: they are the rhythm. Tone decides whether a gap carries thought or emotion; do not
remove it to hit a timing target.

**Never cut inside a sentence.** People slow down on purpose to be clear, and a cut there clips
words. A pause under a second is never dead space and a slow word is never a stumble. Before any
inside cut, listen to both seams: if a word is clipped or the sentence does not read whole, the cut
is wrong.

**Cut tight: 0.04 s before the first word, 0.06 s after the last.** No padding at the head or tail of
a take: right after the last word the speaker reaches for the phone, and right before the first word
they are settling after pressing record. Measure the speech bounds by loudness (20 ms windows, loud =
within 24 dB of the take's peak), not by the transcript. A soft last sound (s, sh, f, a released p
or t) sits under that threshold: also measure the high-frequency energy (the first difference of the
samples) and end 0.06 s after it stops. Then look at the frames around every join in 0.1 s steps and
move a cut in if a hand or body moves toward the camera.

**The very end keeps 0.3 s after the last word**, so the word finishes. Still write that last end at
+0.06: assemble.py pushes only the video's final end out and fades it, and prints `end tail:`. If a
hand already moves toward the phone in that 0.3 s, add `tail <shorter>` and say so in the report.

**When the reach starts before the last word ends**, a cut would lose the word. Keep the audio and
cover the picture: a full-screen graphic on what is being said, fully opaque past the join and fading
out over the next take.

**The voice is cleaned and leveled on every take, automatically:** highpass, RNNoise, a gentle
expander for room echo, a fixed gain to **-14 LUFS** (each take measured on its own, so takes from
different days match), a limiter at -1.5 dBFS. Never `loudnorm` (it pads the audio and drifts out of
sync), and no compressor (it can make Whisper translate Arabic speech to English; transcribe.py warns
if that happens). A take the chain hurts: `voice raw <take>` in cuts.txt.

**A take recorded on the phone mic** (thinner, roomier, its quiet moments 5 to 10 dB above the mic
takes) gets a tone match toward the mic takes:

```
clean UDKI8679 26.30-30.05    # in cuts.txt, the same span as its keep/trim
python S/clean_eq.py <workdir> --phone "<take>:<speech span>" --mic "<mic take>:<speech span>"
```

**Outside clips play at the voice's level.** build.py sets a `broll(audio=True)` clip to -14 LUFS too
and prints `loudness <x> LUFS, true peak <y> dBTP` after every build. Outside -15 to -13 LUFS or above
-1 dBTP goes in the report.

**Private details on a filmed screen** (emails, API keys, customer names): blur them with
`BLUR = [(start, end, (x, y, w, h))]` for as long as they are on screen, including while the camera
pans. Look for them on every screen shot; the user will not always say.

Then transcribe the final master again. **Every caption and visual is timed on that transcript.**

To change a cut after captions and cards are written: save `takes.json` and `edit.py`, re-run
assemble, then `python S/retime.py <workdir> <old takes.json>` moves every time in edit.py.

## Step 2: Captions from the audio, never from the script

People change wording on camera. **The transcript is the truth, the script is a spelling guide.**

- 3 to 4 words per natural phrase, **one line**; shorter at phrase endings. Every chunk starts on a word's start time. Stationary white text, weight 700, 3px dark outline on the 1440 master and a subtle shadow. Direct replacement, no fades, bouncing, or colored words by default.
- Arabic: Arabic letters, English terms stay Latin (app, AI, UI...). **Numbers read left to right**
  inside Arabic captions: write them with their separators ("5,000", "$53,000", "100%") and render.py
  keeps each one as an LTR run. Look at every caption with a number on the check sheet. Show monetary
  amounts in full (`$5,000`, not `$5K`) when the spoken amount is known; never invent precision.
- Use the configured fonts from the brand (defaults: Tajawal for Arabic and Inter for Latin).
- Where a word is unclear, re-decode that stretch on its own (a few seconds, with one of the speaker's
  own sentences as the prompt), pick the most likely, and **list it** in the report with its
  timestamp. Never silently guess.

## Step 3: Style, hook, beat plan, zooms

1. **Style** in one line, using the tree in `STYLES.md`.
2. **Hook.** 7 words max, at most two lines, plain white outlined text without a box or highlight block, complementing (not repeating) the first spoken line.
   Write 3, use the best, list the other two.
3. **Beat plan.** Walk the transcript line by line and pick a visual from the idea bank. Every visual
   starts on the word that triggers it. Prefer an actual example for each named item. Face on punchlines. Check each visual has a purpose; no density quota.
4. **Optional zooms:** keep the baseline calm. A script may mark `[zoom in + riser]` (the hook),
   `[zoom in]` / `[zoom out]` (a reflective line and the realization after it) and `[hard zoom]` (an
   emphasis line): place each on its line, matched by meaning; a mark whose line was cut is dropped
   and named in the report. With no marks, add a zoom only when the delivery benefits. No scheduled
   punch-ins or automatic hook effects. `RISER` defaults to False. Zooms stay on the face, never under
   a full screen, split, or B-roll window.

## Step 4: Write edit.py

**Start from `examples/sitemap-tutorial/edit.py`. It is the default look** (confirmed on a real reel).
Copy its structure, not its content: hook, small cards under the chin, a full screen with the face
circle for the one thing worth seeing big, captions moved below while a card is up, plain follow CTA.
`examples/ui-ux-explanation/edit.py` shows the full project contract, but its dense graphics and
caption lengths are historical. The contract is at the top of `scripts/reel_edit/project.py`, the
components are in `scripts/reel_edit/components.py`. Use the components before writing new HTML, and
build anything new from the same tokens.

### The default look

A plain talking head with captions, plus **a real visual for every thing the speaker names**: a site,
a file, an app, a step, a prompt. The face alone the rest of the time. Not a graphic every few seconds.

1. **The hook:** `hook_card`, plain white outlined text at the top, on frame one.
2. **Show the real thing, small.** The user's own site, page or file, never a mock-up. **An app or a
   site is a screen recording of it being used, not a still:** record it headlessly with Playwright
   (`record_video_dir`, the configured browser, 1280x800, never a visible window: the user may be
   recording their desktop) and do the real thing in it (upload a file, type, play, scroll a site to
   the bottom and back). Trim the clip from the moment the page is ready. A local JS build runs from a
   scratch copy over `python -m http.server` (ES modules do not load from file://). A still screenshot
   only for a file's text or when nothing moves. An app or brand gets its real logo: the simple-icons
   SVG from `cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/<name>.svg`, saved into the reel folder,
   in the brand's color. Never an emoji, never invented proof. If the thing named does not exist, say
   so and ask; do not draw a fake.
3. **Titles above the head, the explanation under the chin.** A step, day or section title is
   `hook_card(text, size=76)` at the top for as long as that step lasts, changing directly to the next
   title. Under the chin goes only what explains it: a screen recording in a rounded window
   (`broll(clip, mode="bottom", top=CARD_TOP, height=420)`), or a white `card` (radius 36, centred, up
   to 1000 px wide) holding the speaker's exact words (a prompt, a path) in a grey box at 40 px, chips,
   or a logo. No title inside the card. `CARD_TOP` is the chin + ~40 px on that framing.
   **States of one card change with a quick fade:** the first state `motion="in"`, middle ones
   `"quick"` (0.15 s, fading in on top of the one before), the last `"quick-out"`. Never a full fade out
   and in on every state, it flickers. Chips that appear one per spoken item keep their slots reserved
   so the card never jumps.
4. **Captions drop below while anything is up.** Every caption that starts while a card, the circle
   or a bottom window is on screen gets `{"y": 1855}`. Otherwise y 1700.
5. **One full screen, for the thing worth seeing big** (the file, the page, the product), with the face
   in the circle under it (`FACE_PIP`) and the content ending above y ~1320. Its title sits at the top
   in the hook style; a recording goes in a `broll(mode="bottom", top=520, height=760, motion="cut")`
   window over a `full()` background.
6. **A file is shown as itself.** In a `browser()` window with its real URL, its real text in monospace
   33 px / 46 px lines, browser colors (tags `#881280`, attribute names `#994500`, values `#1A1AA6`),
   long lines running off the edge. When the speaker says what matters, a second state makes those
   lines bold on the highlight color. Headless Edge hangs on its own XML viewer, so lay the text out in
   HTML yourself.
7. **The CTA:** `follow_card` (or the user's ask), plain text at the top.

### Full screens with the face in a circle

`FACE_PIP` as a list of windows, each
`{"crop": square, "box": (500, 1360, 440, 440), "window": (s, e), "shape": "circle"}`, and the
captions in those windows styled `{"y": 1855}`.

- 440 px, and the crop is a square around the whole head, hair to chin with air around it (about
  `(245, 370, 1100, 1100)` on a usual framing). Check a frame: nothing touches the edge. No ring unless
  `"ring": True`.
- **The circle and the full screen cut in and out together, on the word that names the thing**, like
  a cut between clips. No fade: a fade shows the face through the graphic. `full()`, `split()` and
  `FACE_PIP` are hard cuts by default (`motion="ease"` brings the fade back). When that word is at a
  take join, start on the join. If the frames before it show a reach, tighten that take's end instead
  of starting the screen early.

### Other layouts

- **A list reel:** one real example per spoken item, timed to that item, with the face between
  examples. A minimal progressive list only for abstract steps. `examples/list-reel/edit.py` is an
  optional historical layout. Count the points actually said for the title.
- **A clip you react to:** `broll(path, mode="bottom")`, whole and uncropped, in a rounded window under
  the mouth (`top=` just under the lower lip). Talking over it: muted, and it leaves on the verdict
  line. Watching it in silence and then speaking: `audio=True` (its sound plays, the voice fades back
  in at its end). To make it big: `height=1380, lift=250, top=<chin after the lift + 60>`, with the
  hook on one line (`size=64`).
- **A clip with captions burned in:** no captions of ours over it; two caption layers cannot be read.
- **Cutting a clip at a spoken line:** transcribe the clip (`transcribe.py "<clip>" <workdir>/clip`)
  and take `start=` and the end from its word times. Never guess a cut point by ear.
- **Lining a clip up with a silent reaction take:** the phone usually hears the clip. Cross-correlate
  the two waveforms at 8 kHz; the peak is the offset. If the match is weak, end the clip where the
  first word starts.
- **Illustrations of hypothetical examples** (only when real footage cannot show the concept):
  `broll("<image>.png", mode="bottom")`, generated into the reel's folder. Never a fake screenshot,
  article, receipt or result.
- **Moving captions** (legacy opt-in, only when explicitly requested): `(start, "text", {"y": .., "x": .., "scale": ..})` per
  caption, `{word}` in the text draws that word big.

Hard layout rules the renderer does not enforce:
- Everything inside the safe box: x 90 to 1350, y 360 to 1920 on the 1440x2560 master.
- Text helpers begin at y 372, inside the safe box, above the face. Shorten or reduce text that approaches the eyes or mouth; never move it above y 360. Check the whole thought, including face movement.
- Hooks, takeaways, and text CTAs are plain white outlined text at weight 800, without cards, pills, badges, buttons, or highlight blocks. Custom text: `overlay(html, top=372, motion="cut")` with `text-overlay` CSS. Graphic overlays retain `motion="ease"`.
- No white border on images or B-roll windows: round corners only (`BORDER = 0` in build.py).
- Split panel content ends by ~560 px (the caption sits in the panel at y 1845).
- Plain top text and captions stay white. In explanatory diagrams only, at most one highlight-color accent; error color only for wrong states. No decorative emoji.
- Show actual apps, articles, files and receipts as evidence. Never generate fake screenshots, testimonials, receipts, or results. If an asset is missing, stay on the face and report it.
- Match B-roll to what is said and when it is said.
- Check the intended platform's UI/crop at delivery; the safe box is a baseline, not proof that every TikTok or Shorts overlay clears every device.
- Voice remains dominant over any supplied music/effects. Do not add background music automatically.
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
check.py means fix and rebuild. A render that times out is usually Google Fonts: re-run one visual at
a time (`render.py <workdir> <id>`) until it prints `rendered`.

## Step 6: Cover

```
python S/cover.py <workdir> --title "Two Lines Max|*One Highlighted Line*" --frame <seconds> --out "<folder>/<name> - cover.jpg"
```

A frame of you (smiling, eyes on the lens, not mid-word: pull frames every 0.4 s and pick by eye),
your logo top centre, a fade in your primary color, the title on boxes. The title is the video's
title, not the on-screen hook: 6 words max, two lines. Open `<workdir>/cover/cover-check.jpg`: the
whole title must sit inside the 4:5 grid view and under the chin.

## Step 7: YouTube copy (only when the reel ends on a comment-a-keyword ask)

A keyword ask only works where your comment automation runs. Set `YOUTUBE_END` in edit.py to 0.3 s
after the last word before the ask (the ask starts at its lead-in, not at the keyword; use the
quietest point of a shorter gap), then `python S/build.py <workdir> --youtube`. Check the last second
shows no keyword card and its last 4 s of audio does not contain the ask. Follow, save and send asks
stay; no second copy needed.

## Optional: three hook versions

Film three openings and one body. Edit version A in full (openings B and C dropped in cuts.txt), then
`python S/variants.py <workdir-A> B <opening take> --from .. --to ..` builds B and C with the same
body, moving every body time by the difference. Rewrite only the opening's captions, the hook text
and any card that belonged to A's opening, then render and build. Check a frame of each version at
the same three body moments: they must match. Only the winner needs a cover and a YouTube copy.

## Step 8: Review the cuts

To let the user improve the cut themselves and learn from the source-time changes, follow
[cut-review.md](references/cut-review.md). After the checked reel is at its final path:

```
python S/review.py <workdir> --prepare
python S/review.py <workdir>
```

`Edit cuts.cmd` beside the reel reopens the linked picture/voice timeline. Edge trims can
restore raw footage. Save records draft feedback; Export creates a separate reviewed video
and durable learning history. Existing visuals travel with their footage. Restored handles
use the raw take, without newly authored captions or graphics. Preserve the user's working
timeline when preparing again. Do not open the UI while the user is recording their desktop.

## Step 9: Report

Lead with the file. Then: path and size, loudness, cover path and title (+2 alternates), style and
why, hook (+2 alternates), the beat plan as a short table (with any zooms, and any script mark that
was dropped), words to check with timestamps, anything skipped or assumed, the takes used and any
dropped.

---

## Learn a style from reference reels

The user gives 3 to 5 reels they like (links or video files). The skill studies how they are edited
and keeps the lessons, so their own reels borrow the taste, not the content.

```
python S/references.py <link or file> <link or file> ...     # --out <folder>, default local/references
```

For each reel it downloads the video (links need `yt-dlp`: `pip install yt-dlp`; if a download fails,
for example behind a login, it says so and the user downloads the file themselves and passes it), then
writes into `<out>/<name>/`: `sheet.jpg` (one frame per second with the safe box drawn), `words.txt`
(the transcript with word times), and `analysis.md` (duration, cuts and average shot length, speaking
pace, pauses, loudness). It ends with `<out>/summary.md`, the numbers side by side.

Then:

1. **Look at every contact sheet** and read every `analysis.md`. Note what each reel does with text
   (where, how big, how many words, how long it stays), captions, what is shown on screen and when,
   B-roll and full screens, the face, pacing and cuts, and sound.
2. **Write the patterns into `local/style.md`**, each one with the reels it was seen in. **A pattern
   needs at least 2 of the reels.** One reel's habit is not a rule.
3. **Take inspiration, never copy.** Record how they edit, never what they say or show: no hook lines,
   no graphics, no music, no branding, no exact layouts or colors of theirs. The user's own brand and
   look stay theirs. Copying is what makes reels look like everyone else's.
4. **The user's own rules win.** A pattern that disagrees with `deltas.md`, `local/WORKFLOW.md` or the
   rules above is written down as "not adopted" with the reason, and the user's rule stays. Show the
   user the new `local/style.md` and let them strike anything they do not want.
5. Every later edit reads `local/style.md` at Step 0 and uses it where it fits the reel.

## Learning from feedback

When the user corrects an edit: fix it, then add the lesson to `deltas.md` in this folder (date,
reel, what they said, the rule it implies). The second time the same lesson comes up, write it into
`local/WORKFLOW.md` (or into this file, if it is general enough to help everyone) as a rule. Explicit
instructions to update the skill apply immediately; the repeat rule only concerns inferred preferences.

## Setup notes

- Needs ffmpeg, Python with `faster-whisper playwright pillow numpy`, Microsoft Edge or Google Chrome
  (set `"browser"` in the brand), and the Whisper **small** model in `~/.cache/faster-whisper-small`.
  `yt-dlp` is optional, only for downloading reference reels from links.
- Rendering pulls fonts from Google Fonts, so it needs internet.
- Personal files live in `local/` (brand, workflow, learned style, downloaded references) and next to
  it in `deltas.md`, `history/` and `assets/sfx/`. All of them are git-ignored.
