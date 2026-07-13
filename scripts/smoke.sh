#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m compileall -q src scripts
PYTHONPATH=src python scripts/audit_official_k562_paper_scale_search_space.py   --config configs/official_k562_paper_scale_search_space.json   --output-json /tmp/official_k562_paper_scale_search_space_audit.json   --output-md /tmp/official_k562_paper_scale_search_space_audit.md
PYTHONPATH=src python -m vc_demo.harness.artifact_registry --cell-line K562
