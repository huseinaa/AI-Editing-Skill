# The AI Editing Skill

This is the Claude Code skill that edits my reels. I film the takes, drop them in a folder, type one
command, and get a finished video with a cover. It used to take me three 3-hour editing slots a week.
Now it takes one command.

Here's how to install it and use it on your own videos, with your own brand.

---

## What it does

You give it a folder with the takes you filmed on your phone. It:

1. **Joins your takes** in the order you filmed them and cuts the dead air at the start and end of each one.
2. **Cleans your voice.** It removes background noise and room echo, and sets the volume to the level Instagram and YouTube expect.
3. **Writes captions from what you actually said.** It listens to the audio, not your script, and times every caption to your words.
4. **Picks an edit style** from five (CLEAN, PUNCH, EXPLAINER, DEMO, OFFER) based on what you're saying.
5. **Adds the visuals.** You get a text hook, cards, lists that build as you speak, zooms on the important lines, and your screen recordings or images. It keeps all of it inside the area Instagram doesn't cover.
6. **Makes the cover:** a frame of you smiling, your logo and the title.
7. **Exports** a 1080x1920 video ready to post on Reels, Shorts or TikTok.

If you don't like something, tell it in plain words ("the card covers my face", "that cut is too
tight") and it fixes it. It also writes down what you corrected, so it doesn't make the same
mistake twice.

---

## What you need

- **Claude Code.** It needs a paid Claude plan. I use it inside VS Code, but the terminal works too.
- **Python 3.10 or newer:** [python.org/downloads](https://www.python.org/downloads/)
- **ffmpeg**, the video engine:
  - Windows: `winget install Gyan.FFmpeg`
  - Mac: `brew install ffmpeg`
- **Microsoft Edge or Google Chrome.** The graphics are drawn in the browser.

The transcription runs on your own computer, so you don't need an extra AI subscription for it.

---

## Install (about 10 minutes)

**1. Download the skill**

```
git clone https://github.com/huseinaa/ai-editing-skill.git
```

No git? On the GitHub page, click **Code > Download ZIP** and unzip it.

**2. Put it where Claude Code looks for skills**

Copy the `reel-edit` folder into your skills folder:

- Windows: `C:\Users\<you>\.claude\skills\reel-edit`
- Mac: `~/.claude/skills/reel-edit`

**3. Install the Python packages**

```
pip install faster-whisper playwright pillow numpy
```

**4. Download the speech model** (about 480 MB, one time)

```
python -c "from faster_whisper import download_model; import os; download_model('small', output_dir=os.path.expanduser('~/.cache/faster-whisper-small'))"
```

**5. Check everything**

```
python ~/.claude/skills/reel-edit/scripts/doctor.py
```

Every line should say `OK`. A `MISS` line tells you exactly what to install.

---

## Add your brand

Open `reel-edit/brand.json`. Every card, caption and cover reads from it:

| Setting | What it changes |
|---|---|
| `colors` | Your palette. `primary` is the cover fade and title boxes, `bright` is buttons and highlights in cards, `highlight` is the "look here" word, `error` is for wrong or broken things |
| `fonts` | Your font names and the Google Fonts link that loads them |
| `logo` | A PNG of your logo, shown at the top of the cover. Put it in `reel-edit/assets/` |
| `follow_line` | The line on your follow card |
| `caption_language` | `en`, or `ar` for Arabic captions (English words stay in English letters) |
| `browser` | `msedge` or `chrome` |

The easy way: open Claude Code and say *"set up my brand in the reel-edit skill: my colors are ...,
my font is ..., my logo is this file"*, and it fills in the file for you.

Optional: the rising sound under the hook isn't included because its license doesn't allow sharing
the file. `reel-edit/assets/sfx/SOURCE.md` says where to get it for free. Without it, everything
still works.

---

## How to film for it

- **One folder per reel.** Name it like the video, for example `Reels/Why your app breaks`.
- **Film in order, as many takes as you want.** Stop between sentences if you need to. Messed up a
  line? Just say it again: it keeps the last complete one.
- **Screen recordings or clips you want shown:** put them in the same folder and start the name with
  `broll`, like `broll - my dashboard.mp4`.
- Have a script? Paste it when you run the skill. It's used for spelling and the hook, but the
  captions always come from what you actually said.

---

## Use it

In Claude Code:

```
/reel-edit "Reels/Why your app breaks"
```

Optional extras, in plain words:

```
/reel-edit "Reels/Why your app breaks" style=explainer hook="Your app isn't ready"
```

You get, inside the reel's folder:

- `<name> - edited.mp4`, the reel
- `<name> - cover.jpg`, the cover
- a short report covering the style it picked, the hook, the beat plan, and **any words it wasn't sure
  about** (check these, especially if you speak a dialect)

Then just talk to it: *"make the list slower"*, *"move the card up, it covers my eyes"*, *"use the
second take for the intro"*. It edits and re-renders only what changed.

---

## Good to know

- **Check the words it flags.** The speech model is good but not perfect, especially on accents and
  mixed languages.
- **Rendering takes a few minutes per reel.** Faster on a good computer.
- **It needs internet to render**, because the fonts load from Google Fonts.
- **Built and tested on Windows.** It should work on Mac too, and `doctor.py` tells you if anything is
  missing.

---

Built by Husein, [unemployedhusein.com](https://unemployedhusein.com). If you make something with it,
send it to me. Follow for more tips on building proper software with AI.
