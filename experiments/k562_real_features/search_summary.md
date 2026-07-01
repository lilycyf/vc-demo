# K562 Multi-Feature Search Summary

This search trains multiple real-data K562 root configs, then expands candidate child nodes with an MCTS-style UCT policy.

- Stop reason: no improvement for 6 nodes
- Trained nodes: 19
- Failed nodes: 0
- Best node: `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` val=0.6516 test=0.5790
- Best root: `root_concat_mlp` val=0.5403 test=0.5079
- Improvement over best root: 0.1113 validation Macro-F1

## Root Baselines

| Node | Data dir | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| `root_concat_mlp` | `data/cell_lines/k562_concat` | 0.5403 | 0.5079 |
| `root_concat_regularized_mlp` | `data/cell_lines/k562_concat` | 0.4222 | 0.4040 |
| `root_delta_mlp` | `data/cell_lines/k562_delta` | 0.4117 | 0.4062 |
| `root_onehot_mlp` | `data/cell_lines/k562_onehot` | 0.4224 | 0.4085 |

## All Trained Nodes

| Iter | Node | Parent | Data dir | Hidden | Depth | Dropout | LR | Weight decay | Val | Test |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | `root_concat_mlp` | `` | `data/cell_lines/k562_concat` | 384 | 2 | 0.1 | 0.0003 | 0.0001 | 0.5403 | 0.5079 |
| 0 | `root_concat_regularized_mlp` | `` | `data/cell_lines/k562_concat` | 384 | 3 | 0.2 | 0.0002 | 0.0005 | 0.4222 | 0.4040 |
| 0 | `root_delta_mlp` | `` | `data/cell_lines/k562_delta` | 256 | 2 | 0.1 | 0.0003 | 0.0001 | 0.4117 | 0.4062 |
| 0 | `root_onehot_mlp` | `` | `data/cell_lines/k562_onehot` | 256 | 2 | 0.1 | 0.0003 | 0.0001 | 0.4224 | 0.4085 |
| 1 | `root_concat_mlp_child_1` | `root_concat_mlp` | `data/cell_lines/k562_concat` | 384 | 2 | 0.1 | 0.0008 | 0.0001 | 0.6414 | 0.5818 |
| 2 | `root_concat_mlp_child_1_child_1` | `root_concat_mlp_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.1 | 0.0005 | 0.0001 | 0.6305 | 0.5898 |
| 3 | `root_concat_mlp_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.1 | 0.0005 | 0.001 | 0.6436 | 0.5919 |
| 4 | `root_concat_mlp_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.05 | 0.0005 | 0.001 | 0.6300 | 0.5722 |
| 5 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.05 | 0.0005 | 0.0005 | 0.6346 | 0.5785 |
| 6 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6483 | 0.5868 |
| 7 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6398 | 0.5778 |
| 8 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 384 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6383 | 0.5840 |
| 9 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6516 | 0.5790 |
| 10 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6381 | 0.5746 |
| 11 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6470 | 0.5788 |
| 12 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 1e-05 | 0.6391 | 0.5799 |
| 13 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 0.0 | 0.6467 | 0.5846 |
| 14 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 512 | 2 | 0.05 | 0.0005 | 0.0 | 0.6400 | 0.5865 |
| 15 | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` | `data/cell_lines/k562_concat` | 128 | 2 | 0.05 | 0.0005 | 0.0 | 0.3955 | 0.3902 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.5403 |
| 0 | 0.5403 |
| 0 | 0.5403 |
| 0 | 0.5403 |
| 1 | 0.6414 |
| 2 | 0.6414 |
| 3 | 0.6436 |
| 4 | 0.6436 |
| 5 | 0.6436 |
| 6 | 0.6483 |
| 7 | 0.6483 |
| 8 | 0.6483 |
| 9 | 0.6516 |
| 10 | 0.6516 |
| 11 | 0.6516 |
| 12 | 0.6516 |
| 13 | 0.6516 |
| 14 | 0.6516 |
| 15 | 0.6516 |

## Tree

- `root_concat_mlp` status=trained visits=16 val=0.5403 test=0.5079
  - `root_concat_mlp_child_1` status=trained visits=15 val=0.6414 test=0.5818
    - `root_concat_mlp_child_1_child_1` status=trained visits=14 val=0.6305 test=0.5898
      - `root_concat_mlp_child_1_child_1_child_1` status=trained visits=13 val=0.6436 test=0.5919
        - `root_concat_mlp_child_1_child_1_child_1_child_1` status=trained visits=12 val=0.6300 test=0.5722
          - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1` status=trained visits=11 val=0.6346 test=0.5785
            - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=10 val=0.6483 test=0.5868
              - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=9 val=0.6398 test=0.5778
                - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=8 val=0.6383 test=0.5840
                  - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=7 val=0.6516 test=0.5790
                    - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=6 val=0.6381 test=0.5746
                      - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=5 val=0.6470 test=0.5788
                        - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=4 val=0.6391 test=0.5799
                          - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=3 val=0.6467 test=0.5846
                            - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=2 val=0.6400 test=0.5865
                              - `root_concat_mlp_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1_child_1` status=trained visits=1 val=0.3955 test=0.3902
- `root_concat_regularized_mlp` status=trained visits=1 val=0.4222 test=0.4040
- `root_delta_mlp` status=trained visits=1 val=0.4117 test=0.4062
- `root_onehot_mlp` status=trained visits=1 val=0.4224 test=0.4085

## Limitations

This is a single-cell-line K562 search. It is not the paper's four-cell-line benchmark, and current child generation is rule-based rather than an AI coding agent that edits model code.
