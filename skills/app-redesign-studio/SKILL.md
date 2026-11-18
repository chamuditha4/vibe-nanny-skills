---
name: app-redesign-studio
description: Redesign a mobile app's UI to match a supplied reference design (Figma exports, UI-kit PNGs, a .fig file) and produce matching brand art, app icon and poster-style App Store / Google Play screenshots, using Replicate image models (nano-banana) for illustrations. Use when the user provides UI references or store-screenshot examples and asks to re-skin/redesign the app, generate illustrations or mascot art, make a new app icon, or create store screenshots "like these". Works best with React Native / Expo apps; the art, icon and screenshot pipeline works for any app with a web or simulator build.
---

# App Redesign Studio

Turns reference designs into a shipped redesign: design tokens → illustrations → screens → verification → app icon → store screenshots. Every stage has a script in `scripts/` and a review checkpoint. Paths below are relative to this skill's folder (wherever it is installed, e.g. `.claude/skills/app-redesign-studio/` or `~/.codex/skills/app-redesign-studio/`) unless they start with the project root.

## 0. Inputs and secrets

Expect a `design-inputs/` folder in the project root (template: `templates/design-inputs/`). If the user gives other paths (e.g. `UI/`), use those.

```text
design-inputs/replicate.env     REPLICATE_API_TOKEN=...
design-inputs/ui/               reference screens (PNG/JPG, optional .fig)
design-inputs/store-reference/  store listing screenshots to imitate
design-inputs/brand/            optional existing mascot / logo
design-inputs/brief.md          optional goals and constraints
```

Setup (do this first):
1. Make sure `design-inputs/` is in the project `.gitignore` before anything is written there.
2. If `replicate.env` is missing, copy `templates/design-inputs/replicate.env.example` and ask the user to paste their token into the file — do not ask them to paste it into chat.
3. Never put the token on a command line, in code, in a commit, in an artifact or in a summary. `scripts/replicate.py` reads the env file itself. If the user already pasted a token into chat, use it via the env file and remind them to rotate it at the end.
4. Verify access without spending credits: `python3 scripts/replicate.py --check --env-file <project>/design-inputs/replicate.env`.

Work in the session scratchpad for generated intermediates (`gen/green`, `gen/keyed`, captures). Only final assets go into the project.

## 1. Understand before designing

1. Read the project's instruction files (CLAUDE.md, spec, README) — they override the reference kit. Note brand rules, required screens, accessibility rules, pricing/claims rules and screenshot rules.
2. Read every reference image. For `.fig` files you can only list/extract embedded bitmaps (`unzip -l file.fig`); ask for PNG exports of frames if images are missing.
3. Read the app's current screens, shared components and design tokens so behavior (calculations, purchases, ads, analytics, storage) is preserved.
4. Write a mapping table: each reference screen → the app screen/component it inspires, or "skip". Flag reference content that must NOT be copied: another brand's illustrations, fake social proof ("24,234 listening"), account/sign-in flows the app doesn't have, personal-name greetings, claims the spec forbids.
5. Ask the user (AskUserQuestion) only the decisions that change the work:
   - Adopt the kit's palette, or keep the brand palette with the kit's layouts?
   - Illustrations: generate with Replicate, or will they supply art?
   - Dark mode from the kit's dark screens?
   - Typography: kit font (check licensing/bundling) or system font?
   - Screens to skip.

## 2. Design tokens

- Extract colors from the reference images (sample pixels with PIL); name them by role, not by hue.
- Check every text/background pair with `scripts/contrast.py "#FFFFFF on #8E97FD" ...`. Kits usually fail WCAG AA on pastel buttons with white text and light-grey secondary text. Keep the pastel as a surface, and derive a darker interactive color with `contrast.py --suggest "#FFFFFF" "#8E97FD"`.
- Define light and dark palettes with identical keys. React Native pattern that worked well: `useColors()` (reads `useColorScheme`) plus `makeStyles((c) => ({...}))`, which caches one StyleSheet per palette. Type the factory as `(c: Palette) => T & StyleSheet.NamedStyles<any>` so literal style values type-check. Set `userInterfaceStyle: "automatic"` and dark splash colors in app.json.
- Font: iOS ships Helvetica Neue; Android does not, so fall back to the default font unless a licensed file is bundled. Put `fontFamily` in text styles, because React 19 function components ignore `Text.defaultProps`.
- Update the spec's design section (e.g. CLAUDE.md colors table) when the palette changes, so the source of truth stays accurate.

## 3. Illustrations (Replicate)

1. **Flatten the mascot first.** If the brand mascot is 3D/photo, generate a flat version matching the kit (prompt in `references/prompts.md`). Try `google/nano-banana` and `black-forest-labs/flux-kontext-pro` once each and let the reference style decide. Nano-banana has matched flat pastel kits best. Save the winner as the reference image for all later jobs.
2. **Batch scenes on green.** Copy `templates/jobs.illustrations.example.json`, one job per screen art (welcome, feature cards, calculator headers, paywall, empty/error/not-found states, medicine/object icons). Run it in the background:
   `python3 scripts/replicate.py --jobs gen/jobs.json --env-file <project>/design-inputs/replicate.env`
   Low-credit accounts get HTTP 429 on parallel calls, so the script runs jobs one at a time and retries. It also skips outputs that already exist, so re-running it resumes an interrupted batch.
3. **Key locally:** `python3 scripts/chroma_key.py gen/green gen/keyed --max-size 900`. The keyer samples each image's own drifting green, un-mixes edges and removes green ground shadows while keeping teal and blue art.
4. **Review:** `python3 scripts/contact_sheet.py gen/sheet.png gen/keyed --bg "#FFCF86,#03174C" --labels`, then Read the sheet. Check for:
   - a missing signature outfit (repeat it in every prompt);
   - green objects that got erased;
   - fringes on dark backgrounds;
   - a character that doesn't match the reference.

   Fix a scene by regenerating it, or by editing the approved render with the "keep this illustration exactly the same" prompt.
5. **Install:** re-run the keyer into the app assets with `--max-size 640 --quantize`. Flat art is visually identical and about 10× smaller (8 MB → 600 KB). Register the assets in one illustrations module with short accessibility labels.

## 4. Implement the redesign

- Build shared primitives first (tokens, Card, Button variants, icon buttons with accessible labels, inputs, chips/tabs, headers, feature cards, tiles), then screens. Keep all business logic and analytics calls intact. Only change layout and styling.
- Map kit patterns to app purposes. Examples that worked:
  - welcome → first-launch onboarding with the disclaimer;
  - course detail → calculator screen with an illustrated hero;
  - track list → "show the math" steps;
  - reminder time wheel → date wheel;
  - sign-up splash → paywall;
  - category rail → history/favorites filters;
  - player screen → skip.
- **Responsive:** add a shared `useResponsive()` helper (width, height, fontScale, `stacked`, `compact`, `scaled()`) and use it for:
  - artwork and hero sizes scaled to the screen width;
  - one-column layouts on narrow screens or large text;
  - no `numberOfLines` truncation on titles, so Dynamic Type wraps instead;
  - row heights that grow with the font scale in fixed-height controls such as wheels;
  - `maxFontSizeMultiplier` on huge numerals.
- **Motion:** decorative animation (e.g. a floating mascot) runs on the native driver and stops when `AccessibilityInfo.isReduceMotionEnabled()` is true, including when that setting changes while the app is open.
- **Pricing and claims:** any discount, "launch price" or urgency copy must be genuine and driven by one config flag. Put the regular-price math in a pure module with a unit test. Keep Restore Purchases, Privacy and Terms next to every buy button.
- When adding routes with Expo typed routes, add the new path to `.expo/types/router.d.ts` (or regenerate it) so `tsc` passes.

## 5. Verify

1. Run the project's typecheck and tests after each stage.
2. Visual check through a web build. Follow `references/expo-web-preview.md` for temporary stubs, never killing the user's own dev server, and cleanup. Capture light, dark, 320×568, 390×844 and ~820×1180 with `scripts/capture_screens.cjs`, then Read contact sheets.
3. Compare against the reference kit side by side, and fix obvious gaps before calling it done.
4. Tell the user what couldn't be verified on web: native-only modules, Reduce Motion, large text sizes, purchases.

## 6. App icon

1. Generate a bold, front-facing mascot bust and an optional meaning badge (e.g. calendar check) on green, then key them. Prompts are in `references/prompts.md`.
2. `python3 scripts/compose_app_icon.py --art keyed/bust.png --badge keyed/badge.png --bg "#8E97FD" --out-dir <project>/assets/brand`
3. Read `icon-preview.png`. The icon must be legible at 40 px, and the ears and badge must stay inside the Android circle mask.
4. Wire app.json:
   - `icon` → the 1024 file;
   - `android.adaptiveIcon` → the foreground file plus the background color;
   - splash `image` → `splash-icon.png` (with `imageWidth`), and the same image under `dark`.
   If a render script regenerates icons from a source file, overwrite that source too.
5. Tell the user that Expo Go shows the Expo icon: they need a prebuild or EAS build, plus re-uploading the store icons.

## 7. Store screenshots

1. **Study the store reference.** Note the headline style, the highlight treatment, phone size and tilt, how the mascot is placed, and the background rotation. The composer implements the common poster pattern. Tweak `layout`, `themes`, `phone` and per-shot `shift` / `tilt` / `trimTop` before writing new drawing code.
2. **Plan shots from the spec.** If the spec lists screenshot headlines, use them verbatim. Otherwise write 6–8 benefit-led headlines, one phrase per headline marked `*highlighted*`. Screens must show real app UI with values that match unit-tested results. Never AI-generate UI.
3. **Capture real screens.** Follow `references/expo-web-preview.md`, including temporary patches for paywalls, prices and example dates, and reverting them. Copy `templates/capture.config.example.json` and set:
   - a viewport of 390×797 (the 47 pt status bar is added later) at scale 3;
   - seed data by actually calculating and saving;
   - `dismissAfterGoto` for onboarding.

   Then run `PLAYWRIGHT_CORE=/path/to/node_modules/playwright-core node scripts/capture_screens.cjs capture.config.json`.
4. **Generate mascot poses** with edge-peek prompts (aspect 3:4), then key them with `--max-size 2000` (no quantize) so they stay sharp at store size.
5. **Fetch fonts:** `bash scripts/fetch_fonts.sh <work>/fonts` (Lilita One + Nunito, OFL).
6. **Compose.** Copy `templates/screenshots.config.example.json`, then run `python3 scripts/compose_store_screenshots.py screenshots.config.json` and Read `contact-sheet.png`. Iterate until:
   - the mascot doesn't cover the values being proven (move it with `overhang` / `shift`);
   - the status bar matches the page;
   - no half-cut rows sit at the top (`trimTop`);
   - headlines stay clear of the top 120 px and bottom 90 px.
7. **Install** into the project's screenshot folder using the spec's filenames. Crop one image at full resolution to check sharpness. Remind the user that time-limited offers in screenshots go stale.

## 7b. Animated mascot (optional)

If the user wants the mascot to move (idle, wave, celebrate loops, sprite sheets, transparent WebM), hand off to the sibling `mascot-animation` skill (`../mascot-animation/SKILL.md`). It reuses the flat mascot reference from step 3, generates a green-screen loop on Replicate and turns it into a sprite sheet with [Mascot Studio](https://github.com/chamuditha4/mascot-studio).

## 8. Wrap-up checklist

- Typecheck and tests pass. No temporary patches remain: `grep -rn "SCREENSHOT-TEMP\|PREVIEW-TEMP"` returns nothing, and `git status` shows only intended files.
- The spec and delivery docs reflect the new palette, assets and screenshot style.
- Final message:
  - what changed;
  - what was verified, and what only the user can verify on a device;
  - behavior changes;
  - token rotation if the key was ever shared.

## Files

- `scripts/replicate.py` — Replicate client: single or batch jobs, `--check`, 429 retry, community-model version fallback.
- `scripts/chroma_key.py` — adaptive green-screen keyer, with optional quantize.
- `scripts/contrast.py` — WCAG ratios and nearest passing shade.
- `scripts/contact_sheet.py` — review grids on multiple background colors.
- `scripts/capture_screens.cjs` — Playwright step runner for real screen captures.
- `scripts/compose_store_screenshots.py` — poster-style store screenshots from a JSON config.
- `scripts/compose_app_icon.py` — iOS/Play icons, Android adaptive foreground, splash mark, preview.
- `scripts/fetch_fonts.sh` — OFL display fonts for store art.
- `references/prompts.md` — tested prompts, plus known misses.
- `references/expo-web-preview.md` — running RN/Expo apps on web for verification and capture, safely.
- `templates/` — inputs folder, Replicate jobs, capture config, screenshot config (a complete worked example).
