#!/usr/bin/env python3
"""Headless Mascot Studio run: green-screen video -> transparent frames -> sprite sheet.

Uses the processing pipeline from Mascot Studio
(https://github.com/chamuditha4/mascot-studio) without starting its web UI.

  sprite_sheet.py --studio ../mascot-studio --video gen/wave.mp4 --out out/Wave --webm

Writes:
  out/Wave.png          packed sprite sheet (max 4096x4096)
  out/Wave.json         metadata: frameWidth, frameHeight, totalFrames, fps, duration,
                        columns, rows, sheetWidth, sheetHeight
  out/Wave_frames/      cleaned RGBA frames (frame_NNNN.png), for review and touch-up
  out/Wave.webm         VP9 video with alpha (with --webm)

Needs ffmpeg on PATH and Mascot Studio's requirements (pip install -r requirements.txt).
The first run downloads the chosen matting model into ~/.u2net/.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def load_pipeline(studio):
    studio = Path(studio).expanduser().resolve()
    if not (studio / "processor" / "pipeline.py").is_file():
        sys.exit(f"Not a Mascot Studio checkout: {studio} (expected processor/pipeline.py). "
                 "Clone it with: git clone https://github.com/chamuditha4/mascot-studio")
    sys.path.insert(0, str(studio))
    from processor import pipeline  # noqa: E402

    return pipeline


def encode_webm(frames_dir, fps, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
           "-i", str(frames_dir / "frame_%04d.png"),
           "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30",
           "-auto-alt-ref", "0", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg webm encode failed: {r.stderr.strip()}")


def main():
    ap = argparse.ArgumentParser(description="Green-screen mascot video to sprite sheet via Mascot Studio's pipeline.")
    ap.add_argument("--studio", required=True, help="path to a mascot-studio checkout")
    ap.add_argument("--video", help="input green-screen video (mp4)")
    ap.add_argument("--out", help="output base path, e.g. out/Wave (writes .png and .json)")
    ap.add_argument("--fps", type=int, default=10, help="frames per second to sample (default 10; rvm always uses 10)")
    ap.add_argument("--width", type=int, default=500, help="frame width before cropping (default 500)")
    ap.add_argument("--backend", choices=["rembg", "rvm"], default="rembg",
                    help="rembg: per-frame matting (default). rvm: temporal Robust Video Matting, needs requirements-rvm.txt")
    ap.add_argument("--model", default="birefnet-general", help="rembg matting model (see --list-models)")
    ap.add_argument("--despill", choices=["average", "red"], default="average")
    ap.add_argument("--strength", type=float, default=0.5, help="despill strength 0.0-1.0")
    ap.add_argument("--webm", action="store_true", help="also encode a transparent VP9 WebM")
    ap.add_argument("--list-models", action="store_true", help="print the available matting models and exit")
    args = ap.parse_args()

    pipeline = load_pipeline(args.studio)
    if args.list_models:
        for key, (_session, desc) in pipeline.REMBG_MODELS.items():
            print(f"{key:20s} {desc}")
        return
    if not args.video or not args.out:
        ap.error("--video and --out are required")

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is not on PATH")
    video = Path(args.video).resolve()
    if not video.is_file():
        sys.exit(f"Video not found: {video}")
    if args.backend == "rembg" and args.model not in pipeline.REMBG_MODELS:
        sys.exit(f"Unknown model {args.model!r}. Options: {', '.join(pipeline.REMBG_MODELS)}")

    base = Path(args.out).resolve()
    base.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = base.parent / f"{base.name}_frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)

    fps = args.fps
    if args.backend == "rvm":
        fps = 10  # the pipeline's RVM path samples at a fixed 10 fps
        print("matting with rvm ...", flush=True)
        frames = pipeline.remove_backgrounds_rvm(video, frames_dir, width=args.width,
                                                 despill_method=args.despill, despill_strength=args.strength)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            raw = pipeline.extract_frames(video, Path(tmp), width=args.width, fps=fps)
            if not raw:
                sys.exit("ffmpeg extracted no frames")
            print(f"extracted {len(raw)} frames; matting with {args.model} ...", flush=True)
            frames = pipeline.remove_backgrounds(raw, frames_dir, model=args.model,
                                                 despill_method=args.despill, despill_strength=args.strength)
    if not frames:
        sys.exit("no frames were produced")

    png, meta = pipeline.stitch_sheet(frames, base, fps=fps)
    print("saved", png)
    print("saved", meta)
    print("frames", frames_dir)
    if args.webm:
        webm = Path(str(base) + ".webm")
        encode_webm(frames_dir, fps, webm)
        print("saved", webm)


if __name__ == "__main__":
    main()
