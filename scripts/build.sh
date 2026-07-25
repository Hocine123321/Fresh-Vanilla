#!/usr/bin/env bash
# Rebuilds a .mrpack from pack/modrinth.index.json + overrides/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(python3 -c "import json; print(json.load(open('pack/modrinth.index.json'))['versionId'])")"
OUT_DIR="$ROOT/dist"
OUT_FILE="$OUT_DIR/Fresh-Vanilla-${VERSION}.mrpack"

mkdir -p "$OUT_DIR"
rm -f "$OUT_FILE"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp pack/modrinth.index.json "$STAGE/"
cp -r overrides "$STAGE/"

(cd "$STAGE" && zip -qr "$OUT_FILE" modrinth.index.json overrides)

echo "Built: $OUT_FILE"
