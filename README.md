# Vibe Nanny skills

Free design skills for **Claude Code** and **Codex**: redesign your app from reference designs, make a mascot and matching art, ship a new app icon and store screenshots, and animate your mascot into sprite sheets.

Everything runs on your machine with your own [Replicate](https://replicate.com) account. There is no Vibe Nanny server, account or API. Your files and generated assets stay with you.

| Skill | What it does |
|---|---|
| [`app-redesign-studio`](skills/app-redesign-studio) | Turns a UI kit or reference screens into a redesign: design tokens with contrast checks, mascot and scene illustrations (generated on green, keyed locally), rebuilt screens, an app icon, and poster-style App Store / Google Play screenshots from real app captures. Works best with React Native / Expo; the art, icon and screenshot scripts work for any app. |
| [`mascot-animation`](skills/mascot-animation) | Animates your mascot into transparent loops (idle, wave, celebrate, thinking, agent states): a green-screen clip from a Replicate image-to-video model, then background removal and sprite-sheet packing with [Mascot Studio](https://github.com/chamuditha4/mascot-studio). Outputs a PNG sheet + JSON metadata and a transparent WebM. |

## Install

### Claude Code (plugin)

```text
/plugin marketplace add chamuditha4/vibe-nanny-skills
/plugin install vibe-nanny@vibe-nanny-skills
```

### Claude Code (plain skills)

```bash
git clone https://github.com/chamuditha4/vibe-nanny-skills
cp -r vibe-nanny-skills/skills/* ~/.claude/skills/        # for you
# or: cp -r vibe-nanny-skills/skills/* <project>/.claude/skills/   # for a team, via the repo
```

### Codex

```bash
git clone https://github.com/chamuditha4/vibe-nanny-skills
cp -r vibe-nanny-skills/skills/* ~/.codex/skills/
```

Restart the agent after installing. Keep the two skill folders side by side: `mascot-animation` reuses scripts from `app-redesign-studio`.

## Requirements

- Python 3 with Pillow and NumPy
- A Replicate account and API token (you pay Replicate directly for what you generate)
- For screen captures: Node 18+ and `playwright-core`
- For mascot animation: `ffmpeg` and a local clone of [Mascot Studio](https://github.com/chamuditha4/mascot-studio) (its `requirements.txt` installs rembg; the first run downloads a matting model)

## Use

In your project root, create a git-ignored `design-inputs/` folder:

```text
design-inputs/
  replicate.env           REPLICATE_API_TOKEN=...   (never commit, never paste into chat)
  ui/                     reference screens (PNG/JPG, optional .fig)
  store-reference/        store screenshots whose style you like
  brand/                  your existing mascot or logo, optional
  brief.md                goals and constraints, optional
```

Then ask your agent, for example:

- *"Redesign the app using design-inputs/ui and make store screenshots like design-inputs/store-reference."*
- *"Animate our mascot: idle, wave and celebrate loops as sprite sheets for the web."*

## Mascot Studio

[Mascot Studio](https://github.com/chamuditha4/mascot-studio) is our open-source (MIT) tool that turns green-screen character videos into sprite sheets, with AI background removal and a browser editor for frame-by-frame touch-up. The `mascot-animation` skill drives its pipeline headlessly (`skills/mascot-animation/scripts/sprite_sheet.py`) and sends you to its editor when a frame needs a hand fix.

## Rather have it done for you?

The skills are free. If you would rather hand the work to the people who wrote them, the Vibe Nanny team does app redesigns, mascots, animated mascots, app icons and store screenshots as fixed-price services: [vibenanny.dev/#packages](https://vibenanny.dev/#packages). That is how this project is funded.

## Security

- The Replicate token lives only in `design-inputs/replicate.env`, which must be git-ignored. The scripts read it from there and never print it.
- If a token was ever pasted into a chat or committed, rotate it.

## License

[MIT](LICENSE)
