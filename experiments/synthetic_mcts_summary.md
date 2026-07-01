# Synthetic MCTS Demo Summary

This run uses only the deterministic synthetic perturbation dataset. Each MCTS iteration selects a trained node, generates one child config, trains that child, reads its metrics, and backpropagates validation Macro-F1 through the tree.

- Trained nodes: 9
- Best validation Macro-F1: 0.3404
- Best-so-far curve: `0:0.3404, 1:0.3404, 2:0.3404, 3:0.3404, 4:0.3404, 5:0.3404, 6:0.3404, 7:0.3404, 8:0.3404`

## Tree Structure

Each parent can keep multiple trained children before UCT descends further, so the demo shows breadth near the root and selective deeper expansion.

- `root_mlp` val=0.3404 test=0.3381 visits=9 children=3
  - `root_mlp_child_1` val=0.2994 test=0.3048 visits=2 children=1
    - `root_mlp_child_1_child_1` val=0.3004 test=0.2929 visits=1 children=0
  - `root_mlp_child_2` val=0.3273 test=0.3275 visits=3 children=2
    - `root_mlp_child_2_child_1` val=0.3303 test=0.3286 visits=1 children=0
    - `root_mlp_child_2_child_2` val=0.3354 test=0.3344 visits=1 children=0
  - `root_mlp_child_3` val=0.3349 test=0.3338 visits=3 children=2
    - `root_mlp_child_3_child_1` val=0.3340 test=0.3370 visits=1 children=0
    - `root_mlp_child_3_child_2` val=0.3373 test=0.3307 visits=1 children=0

## Node Metrics

| Iter | Node | Parent | Hidden | Depth | Dropout | LR | Weight decay | Val Macro-F1 | Test Macro-F1 | Note |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | `root_mlp` | `` | 256 | 2 | 0.1 | 0.0003 | 0.0001 | 0.3404 | 0.3381 | root |
| 1 | `root_mlp_child_1` | `root_mlp` | 256 | 2 | 0.1 | 0.0008 | 0.0001 | 0.2994 | 0.3048 | mutated lr from parent root_mlp |
| 2 | `root_mlp_child_2` | `root_mlp` | 256 | 2 | 0.1 | 0.0005 | 0.0001 | 0.3273 | 0.3275 | mutated lr from parent root_mlp |
| 3 | `root_mlp_child_3` | `root_mlp` | 256 | 2 | 0.1 | 0.0003 | 0.001 | 0.3349 | 0.3338 | mutated weight_decay from parent root_mlp |
| 4 | `root_mlp_child_3_child_1` | `root_mlp_child_3` | 256 | 2 | 0.05 | 0.0003 | 0.001 | 0.3340 | 0.3370 | mutated dropout from parent root_mlp_child_3 |
| 5 | `root_mlp_child_2_child_1` | `root_mlp_child_2` | 256 | 2 | 0.1 | 0.0005 | 0.0005 | 0.3303 | 0.3286 | mutated weight_decay from parent root_mlp_child_2 |
| 6 | `root_mlp_child_1_child_1` | `root_mlp_child_1` | 256 | 2 | 0.1 | 0.0008 | 1e-05 | 0.3004 | 0.2929 | mutated weight_decay from parent root_mlp_child_1 |
| 7 | `root_mlp_child_3_child_2` | `root_mlp_child_3` | 384 | 2 | 0.1 | 0.0003 | 0.001 | 0.3373 | 0.3307 | mutated hidden_dim from parent root_mlp_child_3 |
| 8 | `root_mlp_child_2_child_2` | `root_mlp_child_2` | 256 | 2 | 0.1 | 0.0005 | 0.0001 | 0.3354 | 0.3344 | mutated depth from parent root_mlp_child_2 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3404 |
| 1 | 0.3404 |
| 2 | 0.3404 |
| 3 | 0.3404 |
| 4 | 0.3404 |
| 5 | 0.3404 |
| 6 | 0.3404 |
| 7 | 0.3404 |
| 8 | 0.3404 |
