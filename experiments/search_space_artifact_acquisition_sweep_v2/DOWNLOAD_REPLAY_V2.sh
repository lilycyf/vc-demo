#!/usr/bin/env bash
set -euo pipefail
cd /workspace/vc-demo
python scripts/download_paper_model_universe_artifacts.py \
  --base-dir /workspace/models/search_space_artifacts \
  --run-dir experiments/search_space_artifact_acquisition_sweep_v2
