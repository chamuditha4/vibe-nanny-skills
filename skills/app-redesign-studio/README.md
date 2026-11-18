# App Redesign Studio

A Claude Code / Codex skill (part of [Vibe Nanny skills](https://github.com/chamuditha4/vibe-nanny-skills)) that redesigns a mobile app from reference designs and produces matching art, an app icon and store screenshots.

It takes a UI kit (Figma exports / PNGs), a few store-listing screenshots you like and a Replicate token. It then:

1. **Plans:** maps each reference screen to your app's screens and asks only the decisions that matter.
2. **Colors:** builds light and dark design tokens with WCAG AA contrast checks.
3. **Illustrations:** flattens your mascot to the kit's style with `google/nano-banana`, generates scenes on a green screen and keys them locally into small transparent PNGs.
4. **Screens:** rebuilds them (responsive, dark mode, Reduce-Motion aware) and verifies them in a web build.
5. **App icon:** composes the iOS icon, the Android adaptive icon, a splash mark and a preview.
6. **Store screenshots:** creates poster-style screenshots from **real app captures**, never AI-generated UI.

Works best with React Native / Expo apps. The art, icon and screenshot scripts work for any app.

## Install

```bash
git clone https://github.com/chamuditha4/vibe-nanny-skills
cp -r vibe-nanny-skills/skills/app-redesign-studio ~/.claude/skills/   # Claude Code
cp -r vibe-nanny-skills/skills/app-redesign-studio ~/.codex/skills/    # Codex
```

Or copy the folder into a project's `.claude/skills/` to share it with a team. Or install the whole set as a Claude Code plugin (see the repo README). Restart Claude Code (or Codex) and the skill appears as `app-redesign-studio`.

Requirements:

- Python 3 with Pillow and NumPy.
- Node 18+ and `playwright-core` (for captures).
- A Replicate account.

## Use

In your app's project root:

```text
design-inputs/            add to .gitignore
  replicate.env           REPLICATE_API_TOKEN=...   (never commit)
  ui/                     reference screens (PNG/JPG, optional .fig)
  store-reference/        store screenshots whose style you want
  brand/                  optional existing mascot / logo
  brief.md                optional goals and constraints
```

Then ask Claude Code, for example: *"Redesign the app using design-inputs/ui and make store screenshots like design-inputs/store-reference"*, or run `/app-redesign-studio`.

## Contents

| Path | What it does |
|---|---|
| `SKILL.md` | The workflow Claude follows, with checkpoints and guardrails |
| `scripts/replicate.py` | Replicate client: single and batch jobs, `--check`, rate-limit retry; reads the token from an env file |
| `scripts/chroma_key.py` | Green-screen keyer that handles drifting greens, edge un-mixing, shadow removal and palette quantizing |
| `scripts/contrast.py` | WCAG contrast ratios and nearest passing shade |
| `scripts/contact_sheet.py` | Review grids of assets on light and dark grounds |
| `scripts/capture_screens.cjs` | Playwright step runner that captures real screens from a web build |
| `scripts/compose_store_screenshots.py` | Poster-style store screenshots from a JSON config |
| `scripts/compose_app_icon.py` | Store icons, Android adaptive foreground, splash mark, preview |
| `scripts/fetch_fonts.sh` | Open-license display fonts for store art |
| `references/prompts.md` | Tested prompts and known misses |
| `references/expo-web-preview.md` | Running Expo/RN apps on web safely for checks and captures |
| `templates/` | Starter inputs folder, illustration jobs, capture config, a complete screenshot config |

## Script quick reference

```bash
python3 scripts/replicate.py --check --env-file design-inputs/replicate.env
python3 scripts/replicate.py --jobs gen/jobs.json --env-file design-inputs/replicate.env
python3 scripts/chroma_key.py gen/green gen/keyed --max-size 640 --quantize
python3 scripts/contact_sheet.py sheet.png gen/keyed --bg "#FFCF86,#03174C" --labels
python3 scripts/contrast.py "#FFFFFF on #8E97FD"
python3 scripts/compose_app_icon.py --art keyed/bust.png --badge keyed/badge.png --bg "#8E97FD" --out-dir assets/brand
PLAYWRIGHT_CORE=/tmp/pw/node_modules/playwright-core node scripts/capture_screens.cjs capture.config.json
python3 scripts/compose_store_screenshots.py screenshots.config.json
```

## Security

- The Replicate token lives only in `design-inputs/replicate.env`, which is git-ignored.
- The scripts never print it.
- If a token was ever pasted into a chat or a commit, rotate it.
