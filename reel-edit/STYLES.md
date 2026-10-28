# Edit styles and the visual idea bank

## The five styles

| Style | What's on screen | Use it for |
|---|---|---|
| **CLEAN** | Your face the whole time, hook card, captions, one CTA card. Hook zoom + riser, an in/out zoom pair when the story turns, 1 or 2 hard zooms on the punchline | Stories, confessions, strong opinions, personal proof |
| **PUNCH** | CLEAN + a hard zoom on every emphasis beat (every 4 to 6 s) + 2 to 4 takeaway cards. One highlighted word per caption is allowed | Contrarian takes, myth-busts, "stop doing X", fast lists |
| **EXPLAINER** | Graphics: takeaway cards, split panels, full screens, lists that build on your words | Concepts, definitions, frameworks, "X vs Y", steps |
| **DEMO** | Your own screen recordings and footage: full screen, split under your face, or a small window. Face on every reveal | Build in public, tool walkthroughs, before/after |
| **OFFER** | CLEAN base + 1 to 3 proof cutaways + one keyword card on the ask | Selling something |

Styles are defaults, not cages. Combine them when a video needs it and say so ("EXPLAINER, with PUNCH
zooms on the two hot lines").

### Picking a style, fast

```
Is the value in WHAT you explain?          -> EXPLAINER
Is it in something REAL you can show?      -> DEMO
Is it in YOUR conviction, story or take?   -> CLEAN (calm) or PUNCH (energetic)
Is the job to get a DM today?              -> OFFER
```

### Rules per style

- **CLEAN.** Nothing changes on screen except captions, the hook card, zooms and the CTA. If it runs
  past 30 s, add a mid takeaway card or a zoom near the halfway mark.
- **PUNCH.** Zoom in on the stressed word, cut back when the thought ends. Never two hard zooms in a
  row. Takeaway cards on the claims, not on every sentence.
- **EXPLAINER.** Every graphic answers "what is being described right now". Lists build item by item
  on the spoken word. Back to the face for opinions and the punchline.
- **DEMO.** Clips 3 to 5 s, cut on the word that names the thing. If there's no real footage for a
  line, use a graphic or stay on the face. Never stock footage.
- **OFFER.** Never invent scarcity (fake seat counts, fake deadlines). No income or result claims you
  can't prove. One ask.

## The visual idea bank (line type -> visual)

| The line... | Visual | Mode | Component |
|---|---|---|---|
| The hook | Bold card, one highlighted word | overlay, first ~2.7 s | `hook_card` |
| A claim or takeaway | Cause pills -> one result line | overlay | `takeaway` |
| "X vs Y" | Two boxes | split | `vs` |
| "X means Y" | One huge word + one line | full | `statement` |
| A list | Rows that light up on each word | full / split | `list_rows`, `steps` |
| A scenario ("imagine you click...") | A mockup that changes per beat | split | `browser`, `phone`, `demo_app` |
| A mistake and its fix | Crossed-out wrong, then the right one | split | `wrong_right` |
| "The AI does X" | Prompt bubble + reply | split | `chat` |
| A real number | One big stat (real, with a source) | full | `big_number` |
| Something real you built | Your screen recording | split / full / small window | `broll` |
| The spoken hook | Slow zoom in + rising sound, cut back on the next line | none | `ZOOM "hook"` + `RISER` |
| A reflective line | Slow zoom in that holds | none | `ZOOM "in"` |
| The realization after it | Slow zoom back out | none | `ZOOM "out"` |
| A punchline or emphasis | Hard zoom in and cut | none | `PUNCH` |
| The CTA | Follow / Send / Keyword card | overlay | `follow_card`, `send_card`, `keyword_card` |

**Density check before rendering:** find any stretch longer than ~5 s where nothing changes but the
captions. In EXPLAINER, DEMO and PUNCH, fill it with a zoom or a card.
