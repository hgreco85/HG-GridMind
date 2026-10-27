#!/usr/bin/env bash
# Vendors the REAL Meterless H-MEM reference engine (Apache-2.0) into ./vendor/hmem (gitignored).
# Pinned to the upstream commit used for the hackathon evidence. Zero API keys, USD 0.
set -euo pipefail
cd "$(dirname "$0")"
REF=1742dec56a66e58eef9dda2d2b865823758ca8cd
npm install --no-audit --no-fund
if [ ! -f vendor/hmem/src/index.ts ]; then
  rm -rf vendor/_src && mkdir -p vendor
  git clone --quiet https://github.com/Meterless/Meterless.git vendor/_src
  git -C vendor/_src checkout --quiet "$REF"
  rm -rf vendor/hmem && cp -r vendor/_src/engines/hmem/reference vendor/hmem
  mkdir -p vendor/hmem/_licence && cp vendor/_src/LICENSE vendor/hmem/_licence/LICENSE
  rm -rf vendor/_src
fi
echo "H-MEM engine ready: vendor/hmem (upstream Meterless/Meterless@$REF)"
