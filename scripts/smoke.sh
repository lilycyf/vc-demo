#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m pip install -r requirements.txt
python -m pip install -e .
python -m vc_demo.train --config configs/root_mlp.json --output-dir experiments/nodes/root_mlp --max-epochs 2
python -m vc_demo.train --config configs/root_regularized_mlp.json --output-dir experiments/nodes/root_regularized_mlp --max-epochs 2
python -m vc_demo.mcts --tree experiments/tree.json --steps 3
