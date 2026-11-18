#!/usr/bin/env bash
# Download open-license (OFL) display fonts for marketing screenshots.
# These are for composing store images only — never bundle them into the app
# unless the project decides to.
#   fetch_fonts.sh OUT_DIR [extra google/fonts paths like "ofl/fredoka/Fredoka[wdth,wght].ttf"]
set -euo pipefail
out="${1:?usage: fetch_fonts.sh OUT_DIR [extra paths]}"
shift || true
mkdir -p "$out"
paths=("ofl/lilitaone/LilitaOne-Regular.ttf" "ofl/nunito/Nunito[wght].ttf" "$@")
for p in "${paths[@]}"; do
  name="$(basename "$p" | sed 's/\[.*\]//')"
  url="https://github.com/google/fonts/raw/main/$(printf '%s' "$p" | sed 's/\[/%5B/g; s/\]/%5D/g')"
  if [ ! -s "$out/$name" ]; then
    curl -fsSL -o "$out/$name" "$url"
  fi
  echo "font: $out/$name"
done
