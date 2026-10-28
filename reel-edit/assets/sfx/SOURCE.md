# Sound effects

The hook zoom can play a rising sound under the spoken hook. The file is **not included**: its license
allows using it in your videos but not sharing the file on its own.

To use it:

1. Download "Cinematic trailer riser" (item 790) from Mixkit: https://mixkit.co/free-sound-effects/riser/
   (Mixkit Sound Effects Free License: commercial use, no credit needed).
2. Convert it to WAV and save it here as `riser-hook.wav`:
   `ffmpeg -i <downloaded file> -ar 48000 -ac 2 riser-hook.wav`

Any short riser works. Without the file the hook zoom plays silent, nothing breaks. Set `RISER = False`
in a reel's `edit.py` to turn it off for one reel.
