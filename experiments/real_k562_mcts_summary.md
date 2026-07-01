# Real K562 MCTS Demo Summary

This run uses a real NPZ-backed perturbation dataset. Each MCTS iteration selects a trained node, generates one child config, trains that child, reads its metrics, and backpropagates validation Macro-F1 through the tree.

- Trained nodes: 4
- Best validation Macro-F1: 0.5107
- Best-so-far curve: `0:0.3207, 1:0.5107, 2:0.5107, 3:0.5107`

## Tree Structure

Each parent can keep multiple trained children before UCT descends further, so the demo shows breadth near the root and selective deeper expansion.

- `real_k562_template_mlp` val=0.3207 test=0.3188 visits=4 children=2
  - `real_k562_template_mlp_child_1` val=0.5107 test=0.4778 visits=2 children=1
    - `real_k562_template_mlp_child_1_child_1` val=0.4936 test=0.4569 visits=1 children=0
  - `real_k562_template_mlp_child_2` val=0.4003 test=0.3781 visits=1 children=0

## Node Metrics

| Iter | Node | Parent | Hidden | Depth | Dropout | LR | Weight decay | Val Macro-F1 | Test Macro-F1 | Note |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | `real_k562_template_mlp` | `` | 256 | 2 | 0.1 | 0.0003 | 0.0001 | 0.3207 | 0.3188 | root |
| 1 | `real_k562_template_mlp_child_1` | `real_k562_template_mlp` | 256 | 2 | 0.1 | 0.0008 | 0.0001 | 0.5107 | 0.4778 | mutated lr from parent real_k562_template_mlp |
| 2 | `real_k562_template_mlp_child_2` | `real_k562_template_mlp` | 256 | 2 | 0.1 | 0.0005 | 0.0001 | 0.4003 | 0.3781 | mutated lr from parent real_k562_template_mlp |
| 3 | `real_k562_template_mlp_child_1_child_1` | `real_k562_template_mlp_child_1` | 256 | 2 | 0.1 | 0.0008 | 0.001 | 0.4936 | 0.4569 | mutated weight_decay from parent real_k562_template_mlp_child_1 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3207 |
| 1 | 0.5107 |
| 2 | 0.5107 |
| 3 | 0.5107 |
