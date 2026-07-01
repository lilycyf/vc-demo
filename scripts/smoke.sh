#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vc_demo.mcts --tree experiments/smoke/tree.json --reset --steps 3 --max-epochs 1 --summary experiments/smoke/summary.md
python -m vc_demo.train --config configs/root_regularized_mlp.json --output-dir experiments/nodes/root_regularized_mlp --max-epochs 2
