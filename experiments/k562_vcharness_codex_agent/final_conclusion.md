# K562 VCHarness Codex Agent Final Conclusion

## Research Question And Setup

The run tests whether a VCHarness-style Codex proposal agent can find a perturbation response predictor that improves validation Macro-F1 for K562 CRISPR perturbation differential-expression labels over the initial root baselines.

- Dataset/split: existing K562 `real_npz` datasets under `data/cell_lines`, with the prepared train/validation/test split kept fixed.
- Target metric: Macro-F1; validation Macro-F1 is the search reward, and test Macro-F1 is reported for comparison.
- Root configs: `configs/k562_roots/*.json`.
- Command: `python -m vc_demo.harness.run --experiment k562_vcharness_codex_agent --root-configs configs/k562_roots/*.json --run-dir experiments/k562_vcharness_codex_agent --budget-nodes 30 --max-epochs 4 --max-children 3 --stop-no-improve 8 --exploration 0.7 --seed 7 --reset`.
- Stop reason: no improvement for 8 child nodes.
- Trained nodes: 16 total, including 7 roots and 9 children.
- Failed nodes: 0.

## Best Result

- Best root: `root_concat_gated_mlp` with validation Macro-F1 0.6648 and test Macro-F1 0.6101.
- Best overall: `root_concat_gated_mlp_c1_optimizer_refine_4a943707` with validation Macro-F1 0.6709 and test Macro-F1 0.6134.
- Improvement over best root: 0.0060 validation Macro-F1.
- Best path: `root_concat_gated_mlp` -> `root_concat_gated_mlp_c1_optimizer_refine_4a943707`.

Best overall configuration:

- Data/features: `data/cell_lines/k562_concat`.
- Model: `gated_mlp`, hidden_dim=384, depth=2, dropout=0.1.
- Optimizer: lr=0.0005, weight_decay=1e-05.

## Search Behavior

The search first trained all roots, then UCT selected expandable trained parents. The proposal agent produced config-level child candidates without changing data, splits, metric semantics, historical results, or `.gitignore`.

Root branching observed:

- `root_concat_gated_mlp`: 1 child branch(es), val=0.6648
- `root_concat_low_rank_mlp`: 1 child branch(es), val=0.5604
- `root_concat_mlp`: 1 child branch(es), val=0.6445
- `root_concat_regularized_mlp`: 1 child branch(es), val=0.6086
- `root_concat_residual_mlp`: 1 child branch(es), val=0.6193
- `root_delta_mlp`: 1 child branch(es), val=0.5981
- `root_onehot_mlp`: 1 child branch(es), val=0.5955

Proposal strategy counts:

- `feature_to_concat`: 2
- `optimizer_refine`: 7
- `root`: 7

The useful moves were concentrated in `optimizer_refine` and `feature_to_concat`. Optimizer refinement of the best gated concat root gave the winning validation Macro-F1. Converting onehot and delta parents to concat also produced large validation gains relative to those roots, supporting the earlier signal that concat features are the strongest fixed representation in this compact K562 setup.

## Failures

- No failed nodes in the final reset run.

## Conclusion

The experiment found a modest but real improvement over the strongest root baseline: validation Macro-F1 rose from 0.6648 to 0.6709, and test Macro-F1 rose from 0.6101 to 0.6134. The best evidence points to concat biological features plus a gated MLP and slightly more aggressive optimization as the strongest direction under this short four-epoch budget.

Limits: this is one cell line, a compact node budget, and a config-level proposal agent. The result should be treated as a reproducible demo search rather than a full VCHarness paper-scale benchmark.

## Artifacts

- Summary: `experiments/k562_vcharness_codex_agent/search_summary.md`.
- Tree: `experiments/k562_vcharness_codex_agent/tree.json`.
- Failures: `experiments/k562_vcharness_codex_agent/failures.json`.
- Proposals: `experiments/k562_vcharness_codex_agent/proposals/`.
- Ignored node workspaces/checkpoints: `experiments/k562_vcharness_codex_agent/nodes/`.
