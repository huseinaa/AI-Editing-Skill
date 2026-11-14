# Edit styles and the visual idea bank

## The five styles

| Style | What's on screen | Use it for |
|---|---|---|
| **CLEAN** | Your face, the hook and CTA as white pills, stationary 3-4-word captions. Zoom only when the delivery benefits | Stories, confessions, strong opinions, personal proof |
| **PUNCH** | CLEAN with selective emphasis on the strongest lines. No zoom schedule, graphic quota, or colored caption words | Contrarian takes, myth-busts, "stop doing X", fast lists |
| **EXPLAINER** | Light screens: the real thing or a simple diagram in the panel, the face in the square under it. Names and labels as top pills | Concepts, definitions, frameworks, "X vs Y", steps |
| **DEMO** | Your own screen recordings on light screens (`screen()`), the face in the square. Face full screen on every reveal | Build in public, tool walkthroughs, before/after |
| **OFFER** | CLEAN base + relevant real proof + a plain keyword CTA; no cutaway quota | Selling something |

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

- **CLEAN.** Let the face and delivery carry the thought. Duration alone does not justify an extra graphic or zoom.

- **PUNCH.** Zoom in on the stressed word, cut back when the thought ends. Never two hard zooms in a
  row. Plain takeaways only when they add something to the claim.
- **EXPLAINER.** Every graphic answers "what is being described right now". Lists build item by item
  on the spoken word. Back to the face for opinions and the punchline.
- **DEMO.** Time footage to the phrase it illustrates, starting on the word naming the thing. Missing real evidence: stay on the face and report the missing asset. Clearly hypothetical diagrams may explain abstract ideas; never fabricate proof.
- **OFFER.** Never invent scarcity (fake seat counts, fake deadlines). No income or result claims you
  can't prove. One ask.

## The visual idea bank (line type -> visual)

| The line... | Visual | Mode | Component |
|---|---|---|---|
| The hook | A white pill at the top, on frame one | overlay | `hook_card` |
| A name, label or number ("Supabase", "20+ automations") | A white pill with an icon tile, a tag beside it; its states change in place | overlay | `top_pill`, `tag`, `icon`, `brand_logo` |
| Something worth seeing, medium size | A split: the thing on top, the face in a tall rectangle. Rotate light, blurred backdrop and hard split | light / blur / hard | `light`, `light(.., layout="blur")`, `hard`, `top_screen`, `panel`, `screen`, `box`, `heading` |
| Something small (a logo, a number, a price) | A floating card above the head, the face stays full screen | overlay | `float_card`, `image` |
| A demo or a big screen to read | Screen first, the face small at the top left | corner | `corner` |
| A source being explained or reacted to | The speaker cut out, standing in front of it | cutout | `cutout`, `image` |
| A claim or takeaway | One concise statement in a white pill | overlay | `takeaway` |
| "X vs Y" | Two boxes | split | `vs` |
| "X means Y" | One huge word + one line | full | `statement` |
| A list | Actual example per named item, or minimal progressive text for abstract steps | full / split | `list_rows`, `steps` |
| A scenario ("imagine you click...") | A mockup that changes per beat | split | `browser`, `phone`, `demo_app` |
| A mistake and its fix | Crossed-out wrong, then the right one | split | `wrong_right` |
| "The AI does X" | Prompt bubble + reply | split | `chat` |
| A real number, a big reveal | One big stat (real, with a source), full takeover for 1 to 3 s | full | `big_number` |
| Something real you built | Your screen recording | split / full / small window | `broll` |
| The spoken hook | Face first; optional hook zoom (no riser) | none | `ZOOM "hook"` |
| A reflective line | Optional reflective zoom that holds | none | `ZOOM "in"` |
| The realization after it | Optional return from chosen zoom | none | `ZOOM "out"` |
| A punchline or emphasis | Optional purposeful punch-in | none | `PUNCH` |
| The CTA | A white pill: Follow / Send / Comment KEYWORD | overlay | `follow_card`, `send_card`, `keyword_card` |
| A pill or card arriving, the face shrinking | A soft pop, a soft whoosh (automatic) | sound | `AUTO_SFX`, `SFX` |

**Purpose check before rendering:** identify what each visual or effect explains, demonstrates,
or adds to the delivery. Remove decorative filler; no timer-based quota. Check real evidence,
face clearance, readable captions and voice clarity. See the [15-rule audit](references/natural-editing.md).
