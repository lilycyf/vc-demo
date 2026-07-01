# Synthetic MCTS Demo Summary

This run uses only the deterministic synthetic perturbation dataset. Each MCTS iteration selects a trained node, generates one child config, trains that child, reads its metrics, and backpropagates validation Macro-F1 through the tree.

- Trained nodes: 9
- Best validation Macro-F1: 0.3328
- Best-so-far curve: `0:0.3309, 1:0.3309, 2:0.3309, 3:0.3309, 4:0.3309, 5:0.3309, 6:0.3328, 7:0.3328, 8:0.3328`

| Iter | Node | Parent | Hidden | Depth | Dropout | LR | Weight decay | Val Macro-F1 | Test Macro-F1 | Note |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | `root_mlp` | `` | 256 | 2 | 0.1 | 0.0003 | 0.0001 | 0.3309 | 0.3366 | root |
| 1 | `root_mlp_child_1` | `root_mlp` | 256 | 2 | 0.1 | 0.0008 | 0.0001 | 0.2957 | 0.2935 | mutated lr from parent root_mlp |
| 2 | `root_mlp_child_1_child_1` | `root_mlp_child_1` | 256 | 2 | 0.1 | 0.0005 | 0.0001 | 0.3304 | 0.3264 | mutated lr from parent root_mlp_child_1 |
| 3 | `root_mlp_child_1_child_1_child_1` | `root_mlp_child_1_child_1` | 256 | 2 | 0.1 | 0.0005 | 0.001 | 0.3240 | 0.3323 | mutated weight_decay from parent root_mlp_child_1_child_1 |
| 4 | `root_mlp_child_1_child_1_child_1_child_1` | `root_mlp_child_1_child_1_child_1` | 256 | 2 | 0.05 | 0.0005 | 0.001 | 0.3263 | 0.3273 | mutated dropout from parent root_mlp_child_1_child_1_child_1 |
| 5 | `root_mlp_child_1_child_1_child_1_child_1_child_1` | `root_mlp_child_1_child_1_child_1_child_1` | 256 | 2 | 0.05 | 0.0005 | 0.0005 | 0.3308 | 0.3242 | mutated weight_decay from parent root_mlp_child_1_child_1_child_1_child_1 |
| 6 | `root_mlp_child_1_child_1_child_1_child_1_child_1_child_1` | `root_mlp_child_1_child_1_child_1_child_1_child_1` | 256 | 2 | 0.05 | 0.0005 | 1e-05 | 0.3328 | 0.3236 | mutated weight_decay from parent root_mlp_child_1_child_1_child_1_child_1_child_1 |
| 7 | `root_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_mlp_child_1_child_1_child_1_child_1_child_1_child_1` | 384 | 2 | 0.05 | 0.0005 | 1e-05 | 0.2991 | 0.2952 | mutated hidden_dim from parent root_mlp_child_1_child_1_child_1_child_1_child_1_child_1 |
| 8 | `root_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | 384 | 2 | 0.05 | 0.0005 | 1e-05 | 0.3016 | 0.3025 | mutated depth from parent root_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3309 |
| 1 | 0.3309 |
| 2 | 0.3309 |
| 3 | 0.3309 |
| 4 | 0.3309 |
| 5 | 0.3309 |
| 6 | 0.3328 |
| 7 | 0.3328 |
| 8 | 0.3328 |
