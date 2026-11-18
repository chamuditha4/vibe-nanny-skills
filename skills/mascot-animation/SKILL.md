---
name: mascot-animation
description: Animate a mascot or character into transparent loops (idle, wave, celebrate, thinking, agent working/waiting/done states) and export sprite sheets plus metadata JSON and transparent WebM, using a Replicate image-to-video model on a green screen and the open-source Mascot Studio pipeline for background removal. Use when the user asks to animate a mascot, make a mascot move, create idle/wave/celebrate loops, build a sprite sheet, or get a transparent mascot video for an app, website, game or AI agent.
---

# Mascot Animation

Still mascot → green-screen video loop → transparent frames → sprite sheet (PNG + JSON) and WebM. Background removal and sheet packing come from [Mascot Studio](https://github.com/chamuditha4/mascot-studio) (MIT, runs locally). Paths below are relative to this skill's folder unless they start with the project root.

Everything runs on the user's machine and their own Replicate account. Nothing is uploaded anywhere else.

## 0. Inputs and secrets

Same convention as the `app-redesign-studio` skill:

```text
design-inputs/replicate.env   REPLICATE_API_TOKEN=...
design-inputs/brand/          the mascot (any style), optional
design-inputs/brief.md        which states/moves, where they will be used, optional
```

1. Add `design-inputs/` to the project `.gitignore` before writing anything there.
2. If `replicate.env` is missing, create it with an empty `REPLICATE_API_TOKEN=` line and ask the user to paste the token into the file, not into chat.
3. Never print the token or put it on a command line, in code, a commit or a summary. The scripts read the env file themselves.
4. Check access without spending credits: `python3 ../app-redesign-studio/scripts/replicate.py --check --model <owner/model> --env-file <project>/design-inputs/replicate.env`.

Work in the session scratchpad (`gen/`) for intermediates. Only final assets go into the project.

## 1. A still reference on green

The video model animates from a single still. It must be:

- the final mascot, full body, centered, with generous margin on every side (moves like waving need room);
- on one flat pure chroma-key green (`#00FF00`) with no shadow, gradient or floor;
- free of green inside the character (green parts get keyed out).

If the user only has a mascot on another background, or in another style, make the still with `google/nano-banana` using the green-screen suffix from `../app-redesign-studio/references/prompts.md` and the existing mascot as the image input. Read the result before going on.

Make one still per state when the start pose differs (e.g. "thinking" starts with a paw on the chin).

## 2. Generate the green-screen loop (Replicate)

1. **Pick an image-to-video model** on Replicate and open its API schema first (`https://replicate.com/<owner>/<model>/api/schema`, or the model page). Image field names differ between models (`image`, `start_image`, `first_frame_image`, ...), and so do duration, resolution and aspect parameters. Do not guess them.
2. **Try one model with one state** before batching. Let the result decide. Models differ a lot on keeping the background flat and the character on-model. If it drifts, try one alternative rather than tweaking prompts forever.
3. **Run it** with the bundled client (MP4 output is supported; `output_format` is only defaulted for image outputs):

   ```bash
   python3 ../app-redesign-studio/scripts/replicate.py --env-file <project>/design-inputs/replicate.env \
     --model <owner/model> --image gen/still-wave.png --image-key <field> \
     --param duration=5 --out gen/video/wave.mp4 --prompt "<prompt>"
   ```

   For several states, use a jobs file (`"model"`, `"image_key"`, `"params"` as defaults; one job per state with `"out": "video/<state>.mp4"`). It runs sequentially and skips finished outputs, so re-running resumes. Video generations cost noticeably more than images: tell the user how many you are about to run.

4. **Prompt rules** (templates in `references/states.md`):
   - locked-off static camera, no zoom, no pan, no cuts;
   - flat solid pure green background for the whole clip, no shadows, no lighting changes;
   - the whole character stays inside the frame;
   - one simple, readable move;
   - starts and ends on the same pose as the still, so it loops;
   - same character, same proportions, same colors, no new objects.

Watch each clip (extract a few frames with ffmpeg and Read them) before processing. Reject clips where the background changes, the camera moves, or the character morphs.

## 3. Set up Mascot Studio (once)

```bash
git clone https://github.com/chamuditha4/mascot-studio <somewhere outside the project>
cd mascot-studio && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt            # Django, Pillow, numpy, rembg
# optional temporal matting (PyTorch, ~2 GB): pip install -r requirements-rvm.txt
```

`ffmpeg` must be on `PATH`. The first run downloads the matting model into `~/.u2net/` (about 100–900 MB depending on the model). Tell the user before that happens.

## 4. Video → sprite sheet

Run with the Mascot Studio venv's Python:

```bash
<mascot-studio>/.venv/bin/python scripts/sprite_sheet.py --studio <mascot-studio> \
  --video gen/video/wave.mp4 --out gen/sheets/Wave --webm
```

Options: `--fps 10` (sampling rate), `--width 500` (frame width before crop), `--model birefnet-general` (`--list-models` for all), `--despill average|red`, `--strength 0.5`, `--backend rvm` for temporal matting on fast motion (fixed 10 fps, needs the RVM extras).

Output: `Wave.png` (sheet, max 4096×4096, cropped to the union bounding box of all frames), `Wave.json`, `Wave_frames/` (cleaned RGBA frames) and `Wave.webm` (VP9 with alpha).

Tips:
- Flat cartoon mascots: try `isnet-anime` or `birefnet-general`. Fine fur or hair: `birefnet-dis` or `ben2`.
- Green fringes on edges: raise `--strength`, or use `--despill red`.
- Edges that boil from frame to frame: `--backend rvm`.

## 5. Review and touch up

1. `python3 ../app-redesign-studio/scripts/contact_sheet.py gen/review/wave.png gen/sheets/Wave_frames --bg "#FFFFFF,#1B1B1F"`, then Read it. Look for leftover green, holes in the character, flicker between frames, a cut-off limb, and a visible jump between the last and first frame.
2. Fix:
   - a bad clip → regenerate the video (step 2);
   - a few bad frames → open Mascot Studio's editor: `python manage.py runserver` in the studio folder, open `http://127.0.0.1:8000`, import `Wave.png` + `Wave.json`, erase stray pixels or re-run AI on single frames, then export. Ask the user to do this part if you cannot drive a browser.
   - a loop seam → trim the clip with ffmpeg so it ends where it starts, then re-run step 4.

## 6. Deliver

Put the final files into the project's assets (e.g. `public/mascot/` or `assets/mascot/`): the `.png` + `.json` per state, and the `.webm` where video is easier. The JSON format:

```json
{ "frameWidth": 406, "frameHeight": 682, "totalFrames": 40, "fps": 10, "duration": 4.0,
  "columns": 7, "rows": 6, "sheetWidth": 2842, "sheetHeight": 4092 }
```

Frames run left to right, top to bottom. A minimal web player:

```js
// <canvas id="mascot"></canvas>
async function playSheet(canvas, base) {
  const meta = await (await fetch(`${base}.json`)).json();
  const img = new Image(); img.src = `${base}.png`; await img.decode();
  const ctx = canvas.getContext("2d");
  canvas.width = meta.frameWidth; canvas.height = meta.frameHeight;
  let i = 0;
  setInterval(() => {
    const sx = (i % meta.columns) * meta.frameWidth, sy = Math.floor(i / meta.columns) * meta.frameHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, sx, sy, meta.frameWidth, meta.frameHeight, 0, 0, meta.frameWidth, meta.frameHeight);
    i = (i + 1) % meta.totalFrames;
  }, 1000 / meta.fps);
}
playSheet(document.getElementById("mascot"), "/mascot/Wave");
```

Or skip the code: `<video src="/mascot/Wave.webm" autoplay loop muted playsinline>` (VP9 alpha plays in Chrome, Edge and Firefox; Safari needs an HEVC-with-alpha file or the sprite sheet). Respect `prefers-reduced-motion` by showing the first frame only.

Final message: which states were made, the files and where they are, the models used, how many paid generations ran, and anything the user should touch up by hand.
