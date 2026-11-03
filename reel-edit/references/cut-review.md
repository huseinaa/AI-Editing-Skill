# Reviewing cuts and learning from them

Use the same cut-review workflow as program-edit, with the reel's picture and voice linked.
The implementation is self-contained in this skill; program-edit is not required at runtime.

After building and checking a reel folder:

```
python scripts/review.py <workdir> --prepare
python scripts/review.py <workdir>
```

It creates `<reel folder>/_edit/review/` and `Edit cuts.cmd` beside the reel. Open that file
later to resume. The launcher starts a local-only server using windowless Python. If he says
he is filming, prepare the package without opening the browser.

The two linked lanes show picture and voice. Drag clip edges inward to trim or outward to
restore source footage; S splits, Delete removes a selected piece and closes the gap;
arrow keys move one frame, Shift+arrows one second, up/down move between joins, comma/period
slip a selected take by one frame, Ctrl+Z undoes. Every change saves automatically.

The initial preview contains the finished reel's captions, graphics and screen recordings.
Those visuals stay attached to the footage they illustrate when it is shortened. Restoring
footage beyond the original keep uses the raw take, including its original sound and without
newly invented captions or graphics. Explain that limit when relevant. This is a cutting UI;
reordering clips, separating sound, and authoring graphics are outside its scope.

Export produces `<reel title> - reviewed.mp4` (a unique suffix on further exports). The
original export and raw takes remain intact. Do not export his working timeline for him.
The existing platform-specific copy is not silently replaced; after he finishes reviewing,
use the reviewed source decisions if a separate YouTube ending needs rebuilding.

## What is saved

- `project.json`: source paths, original fractional cut times, normalized frame positions,
  caption context and the SHA-256 of the snapshot.
- `baseline.mp4`: immutable snapshot of the checked edit.
- `timeline.ai.json`: original decisions; `timeline.json`: his working decisions.
- `feedback.json` and `review-diff.txt`: source-time removals and restorations on each save.
- `history/<reel>-<export timestamp>.json` in this skill: durable evidence on each successful
  Export, with `learned: false`. Do not delete or conflate separate exports.

The reviewer uses a 30 fps frame grid. Its mapping retains the assembly's fractional source
start/end times; raw timestamps in feedback are derived from those anchors, with the normal
one-frame precision of the normalized edit. Caption text is context, not word alignment.

## Before the next reel, and when he says he finished

Read unlearned exported history and, for active reviews, draft `feedback.json`. Compare
`he_cut`, `he_restored`, edge side, raw source interval and caption context. Use the saved
timelines to distinguish trimming from a slip or acceptance without changes. A split alone
does not prove a pacing preference. Draft work can still change: do not promote it as final.

Write observed patterns to `deltas.md`, with the reel/date and exact evidence. Separate what
he changed from your interpretation of why. Only mark that history entry `learned: true`
after recording its lesson (or noting that no cutting decision changed). Do not infer new
timing rules from an untouched export or a single ambiguous cut. A repeated preference across
two reels can become a default; an explicit instruction applies immediately. Lecture pacing
rules do not transfer automatically to reels.

Keep `_edit` until he exports. Re-running `--prepare` preserves an existing review and working
timeline. If a new render needs a new review baseline, archive the old package explicitly
after checking for unexported changes; never reset his timeline as part of an unrelated re-render.
