#!/usr/bin/env python3
"""Minimal Replicate client for image and video generation (no SDK needed).

The output file type follows the model: use an .mp4 --out for video models
(output_format is only defaulted to png for image outputs).

The API token is read from the REPLICATE_API_TOKEN environment variable, or from
an env file (KEY=VALUE lines) given with --env-file. Default env file lookup:
./design-inputs/replicate.env. The token is never printed.

Single image:
  replicate.py --model google/nano-banana --out out.png \
      --prompt "..." --image ref.png --aspect 1:1

Batch (sequential, skips outputs that already exist):
  replicate.py --jobs jobs.json
  jobs.json = {"model": "google/nano-banana", "defaults": {"aspect": "1:1", "image": ["ref.png"]},
               "suffix": "text appended to every prompt",
               "jobs": [{"out": "a.png", "prompt": "...", "image": ["other.png"], "aspect": "3:4"}]}
  Optional per-job or default keys: "model", "params" (extra model inputs), "image_key"
  (the model's image input field, e.g. "start_image" for some video models).

Check access without spending credits:
  replicate.py --check --model google/nano-banana
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.replicate.com/v1"
UA = "vibe-nanny-skills/1.0 (+python-urllib)"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def load_token(env_file):
    token = os.environ.get("REPLICATE_API_TOKEN")
    if token:
        return token.strip()
    candidates = [env_file] if env_file else ["design-inputs/replicate.env", ".env.replicate"]
    for path in candidates:
        if path and os.path.isfile(path):
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("REPLICATE_API_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No REPLICATE_API_TOKEN found. Set the env var or put REPLICATE_API_TOKEN=... in design-inputs/replicate.env")


def request(token, url, data=None, method=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Prefer": "wait=60", "User-Agent": UA}
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(10):
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 429:  # low-credit accounts are limited to ~1 request burst
                time.sleep(12 + attempt * 3)
                continue
            if err.code == 404:
                raise FileNotFoundError(url)
            sys.exit(f"HTTP {err.code} from Replicate: {err.read().decode(errors='replace')[:300]}")
        except urllib.error.URLError as err:
            if attempt < 3:
                time.sleep(5)
                continue
            sys.exit(f"Network error talking to Replicate: {err}")
    sys.exit("Replicate kept rate-limiting (HTTP 429). Add credit or run jobs more slowly.")


def data_uri(path, max_side=1024):
    from PIL import Image  # local import so --check works without Pillow

    im = Image.open(path)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def image_field(model, uris, override=None):
    if override:
        # List-style fields (e.g. nano-banana's image_input) take every reference.
        return {override: uris if override == "image_input" else uris[0]}
    if "nano-banana" in model:
        return {"image_input": uris}
    if "flux-kontext" in model:
        return {"input_image": uris[0]}
    if "background-remover" in model or "remove-bg" in model:
        return {"image": uris[0]}
    return {"image": uris[0]}


def create_prediction(token, model, inputs):
    try:
        return request(token, f"{API}/models/{model}/predictions", {"input": inputs})
    except FileNotFoundError:
        # Community models have no "official" endpoint: pin the latest version.
        info = request(token, f"{API}/models/{model}")
        version = (info.get("latest_version") or {}).get("id")
        if not version:
            sys.exit(f"Model {model} has no published version")
        return request(token, f"{API}/predictions", {"version": version, "input": inputs})


def run(token, model, inputs, out):
    pred = create_prediction(token, model, inputs)
    while pred["status"] not in ("succeeded", "failed", "canceled"):
        time.sleep(2)
        pred = request(token, pred["urls"]["get"])
    if pred["status"] != "succeeded":
        raise RuntimeError(f"{model} {pred['status']}: {pred.get('error')}")
    output = pred["output"]
    url = output[0] if isinstance(output, list) else output
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with urllib.request.urlopen(req, timeout=180) as resp, open(out, "wb") as fh:
        fh.write(resp.read())
    print("saved", out, flush=True)


def build_inputs(model, prompt, images, aspect, params, image_key=None, out=None):
    inputs = dict(params or {})
    if prompt:
        inputs["prompt"] = prompt
    if aspect:
        inputs.setdefault("aspect_ratio", aspect)
    if out is None or out.lower().endswith(IMAGE_EXTS):
        inputs.setdefault("output_format", "png")
    if images:
        inputs.update(image_field(model, [data_uri(p) for p in images], image_key))
    return inputs


def parse_params(pairs):
    out = {}
    for pair in pairs or []:
        key, _, value = pair.partition("=")
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="google/nano-banana")
    ap.add_argument("--out")
    ap.add_argument("--prompt")
    ap.add_argument("--image", action="append", help="reference image path (repeatable)")
    ap.add_argument("--image-key", help="override the model's image input field name")
    ap.add_argument("--aspect", default=None)
    ap.add_argument("--param", action="append", help="extra model input key=value (JSON values allowed)")
    ap.add_argument("--jobs", help="JSON batch file")
    ap.add_argument("--env-file")
    ap.add_argument("--check", action="store_true", help="verify token and model access only")
    args = ap.parse_args()

    token = load_token(args.env_file)

    if args.check:
        info = request(token, f"{API}/models/{args.model}")
        print(f"ok: {info.get('owner')}/{info.get('name')} (latest version {(info.get('latest_version') or {}).get('id', 'n/a')[:12]})")
        return

    if args.jobs:
        with open(args.jobs) as fh:
            spec = json.load(fh)
        model = spec.get("model", args.model)
        defaults = spec.get("defaults", {})
        suffix = spec.get("suffix", "")
        base = os.path.dirname(os.path.abspath(args.jobs))
        failures = 0
        for job in spec["jobs"]:
            out = os.path.join(base, job["out"]) if not os.path.isabs(job["out"]) else job["out"]
            if os.path.exists(out):
                print("skip (exists)", out)
                continue
            images = job.get("image", defaults.get("image")) or []
            images = [p if os.path.isabs(p) else os.path.join(base, p) for p in ([images] if isinstance(images, str) else images)]
            prompt = " ".join(x for x in [job["prompt"], job.get("suffix", suffix)] if x)
            try:
                run(token, job.get("model", model), build_inputs(job.get("model", model), prompt, images, job.get("aspect", defaults.get("aspect")), {**defaults.get("params", {}), **job.get("params", {})}, job.get("image_key", defaults.get("image_key")), out), out)
            except RuntimeError as err:
                failures += 1
                print("FAILED", out, err, file=sys.stderr)
        print("batch done", "with failures" if failures else "")
        return

    if not args.out or not args.prompt:
        ap.error("--out and --prompt are required (or use --jobs / --check)")
    run(token, args.model, build_inputs(args.model, args.prompt, args.image, args.aspect, parse_params(args.param), args.image_key, args.out), args.out)


if __name__ == "__main__":
    main()
