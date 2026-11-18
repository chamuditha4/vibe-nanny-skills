# design-inputs

Everything the `app-redesign-studio` skill reads. This whole folder is local
only — keep `design-inputs/` in `.gitignore`.

```text
design-inputs/
  replicate.env        REPLICATE_API_TOKEN=r8_...   (copy from replicate.env.example)
  ui/                  reference UI kit exports: *.png / *.jpg (one per screen) and the optional *.fig
  store-reference/     screenshots of App Store / Play listings whose style you want to match
  brand/               optional: existing mascot, logo or icon to keep the character consistent
  brief.md             optional: goals, must-keep features, screens to skip, audience, constraints
```

Tips

- Export each Figma frame as its own PNG at 2x or 3x; the agent reads images,
  not the binary `.fig` (it can only pull embedded bitmaps out of a `.fig`).
- Put one store-reference image per style you like; a single contact sheet of a
  competitor listing works well.
- Never paste the Replicate token into chat or commit it. Rotate it if it was shared.
