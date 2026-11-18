# Prompt library (tested)

All prompts below produced usable results with `google/nano-banana`. Append the
**green-screen suffix** to every asset that needs a transparent background, and
pass the **flat mascot reference** as the image input for every character scene.

## Green-screen suffix

```text
The background must be one flat solid pure chroma-key green color (#00FF00) filling the entire canvas edge to edge, with no shadows, no ground shadow, no gradient and no texture on the background. Do not use any green color anywhere in the illustration itself.
```

The model rarely returns true #00FF00 (expect a drifting pastel green) — `chroma_key.py` handles that. The second sentence matters: plants, green pills or green clothing get keyed out otherwise.

## Style suffix (flat UI-kit illustration)

```text
Use the exact same <character> from the reference image, same flat 2D vector style: simple geometric shapes, flat pastel colors, soft two-tone shading, no outlines, no gradients, no text, no letters, no numbers. <Character> always wears <signature outfit>. Subject centered with generous margin, full body visible.
```

Repeat the signature outfit in every prompt — scenes that omitted it lost the lab coat.

## Step 1 — convert an existing (3D/photo) mascot into the kit's flat style

Image input: the existing mascot render. Compare `google/nano-banana` and `black-forest-labs/flux-kontext-pro`; nano-banana matched flat pastel UI kits far better (kontext added outlines and fur texture).

```text
Redraw this exact <animal> character as a flat 2D vector illustration for a calm wellness-style mobile app: simple geometric shapes, flat pastel colors with only soft two-tone shading, no outlines, no fur texture, no gradients, friendly closed-mouth smile. Keep the <key markings> and <fur colors>. Dress it in a soft <brand color name> (<hex>) <outfit>. Full body, standing, holding <signature prop>. Plain pure white background, centered, no text.
```

Save the winner as the reference for everything else.

## Scene ideas that map UI-kit art to utility-app screens

| Screen | Prompt fragment |
|---|---|
| Welcome / onboarding | sitting cross-legged peacefully with eyes gently closed and paws together |
| Date / calendar feature | standing beside a large wall calendar page with one day circled, pointing at it |
| Quantity / counting | counting tablets on a counting tray with a spatula, a neat pile beside it |
| History | reading a long clipboard checklist, a small clock floating beside it |
| Favorites | happily hugging a big soft yellow star |
| Paywall | relaxing in a <brand color> armchair holding a tablet computer, floor lamp and pot of pink flowers |
| Empty state | looking curiously into an empty open cardboard box |
| Error | scratching its head beside a large calculator, mildly confused but calm |
| Not found | holding a magnifying glass, searching, calm friendly expression |

## Editing an existing white-background scene onto green (keeps composition)

Image input: the approved white-background render.

```text
Keep this illustration exactly the same (same character, pose, objects, colors and composition). Only replace the white background. <optional fix, e.g. "Also replace the green potted plant with a pot of soft pink flowers."> <green-screen suffix>
```

## Flat object icons (no character)

Image input: any approved scene, for style only.

```text
A single flat 2D vector app icon illustration of <object>, drawn in the same flat pastel illustration style as the reference image (simple geometric shapes, soft two-tone shading, no outlines, no gradients). No character, no text, no letters. Object centered and filling about 70% of the canvas. <green-screen suffix>
```

## App icon parts

```text
App icon mascot portrait: the exact same <character> from the reference image, head and shoulders only, facing the viewer straight on, big friendly closed-mouth smile, bright eyes, wearing the <outfit> collar. Large, bold, simple shapes that stay readable at very small icon sizes. Centered, filling about 80% of the canvas. <style suffix> <green-screen suffix>
```

```text
A single flat 2D vector icon of a small white desk calendar page with two dark charcoal binder rings on top and a bold orange checkmark in the middle, rounded corners, same flat pastel style as the reference image. No character, no text, no numbers. Centered, filling about 70% of the canvas. <green-screen suffix>
```

Front-facing, bold busts read at 40 px; winking three-quarter poses did not.

## Store-screenshot mascot poses (edge peeks)

Use aspect `3:4` for tall poses. "Cut off at the bottom edge" makes the art sit naturally on the canvas edge.

```text
<character> peeking up from the very bottom edge of the image: only the head, shoulders and both paws are visible, paws resting on the bottom edge, the body cut off by the bottom edge of the image. Big friendly smile, looking up and to the left.
<character> leaning in from the right edge of the image, upper body only, the body cut off by the right edge, waving hello with one paw, cheerful smile, looking to the left.
<character> upper body, cut off at the bottom edge of the image, proudly holding up <product prop> in both paws, cheerful smile.
<character> full body jumping in celebration with both arms raised high, big open smile, a few small yellow sparkles and one big soft yellow star floating above.
```

Known miss: "a scattered cluster of capsules, no character" still drew the character when the mascot was passed as the image input — pass a non-character image (or none) for props.
