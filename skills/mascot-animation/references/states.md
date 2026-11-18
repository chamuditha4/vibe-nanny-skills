# Mascot states and prompt templates

Start with 3–4 states. Each one is a separate short clip (3–5 s) that starts and ends on the same pose.

| State | Use it for | Move |
|---|---|---|
| `idle` | default, always on screen | gentle breathing bob, one blink |
| `wave` | onboarding, greetings, empty states | raises one arm, waves twice, lowers it |
| `celebrate` | success, purchase, streaks | small hop with both arms up, lands |
| `thinking` | loading, "let me check" | paw to chin, looks up, slight head tilt |
| `sad` / `concerned` | errors, offline | shoulders drop, small sigh |

For AI agents and dev tools, map states to agent status:

| State | Agent status | Move |
|---|---|---|
| `working` | running a task | types on a small laptop, or busy hands |
| `waiting` | needs the user's input | looks toward the viewer, taps foot |
| `done` | task finished | thumbs up or a small nod |
| `error` | task failed | scratches head, confused |

## Shared suffix (append to every video prompt)

```text
Static locked-off camera, no zoom, no pan, no camera movement, no cuts. The background is one flat solid pure chroma-key green (#00FF00) for the entire clip, with no shadows, no floor, no lighting changes and no gradient. The whole character stays fully inside the frame at all times. Same character, same proportions, same colors and same flat 2D style as the first frame; no new objects appear. The clip starts and ends in exactly the same pose as the first frame so it loops seamlessly.
```

## Per-state prompts

- **idle:** `The character stands in place, breathing gently with a subtle up-and-down bob, and blinks once. Calm and friendly.`
- **wave:** `The character raises its right arm and waves hello twice with a big smile, then lowers the arm back to its starting pose.`
- **celebrate:** `The character does a small happy hop with both arms raised, lands softly in the same spot, then returns to its starting pose.`
- **thinking:** `The character lifts one hand to its chin, looks up thoughtfully with a slight head tilt, then returns to its starting pose.`
- **working:** `The character types quickly on a small laptop it is holding, focused and busy, staying in the same spot.`
- **waiting:** `The character looks toward the viewer expectantly and taps one foot twice, then returns to its starting pose.`
- **done:** `The character gives a confident thumbs up and a small nod, then returns to its starting pose.`

## Still frames for poses that start differently

When a state starts in a different pose (e.g. `working` with a laptop), first make a still on green with `google/nano-banana` using the mascot as the image input, then animate that still.

```text
The exact same character from the reference image, same flat style, <starting pose>. Full body, centered, generous margin on every side. The background must be one flat solid pure chroma-key green (#00FF00) filling the entire canvas, with no shadows and no gradient. Do not use any green in the character.
```

## Known misses

- Models often add a floor shadow or a light vignette. Reject the clip: shadows become grey smudges after keying.
- Fast moves (jumps, spins) blur, and per-frame matting boils on motion blur. Use `--backend rvm`, or ask for a slower move.
- If the loop seam jumps, trim the clip to the frame closest to the first one before making the sheet.
