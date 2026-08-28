#!/usr/bin/env bash
# One-command report builder. Run from Desktop Cursor terminal or say "build my report" to the agent.
set -e
cd "$(dirname "$0")/.."
echo "=== Installing dependencies ==="
pip install -r requirements.txt -q
echo "=== Building report (uses output/zapier/*.json if present) ==="
python3 scripts/build_report.py links.yaml -o output
echo ""
echo "=== Done! Your files: ==="
ls -lh output/*.pptx output/*.pdf 2>/dev/null || true
echo ""
echo "Open the .pptx or .pdf in the output/ folder."
