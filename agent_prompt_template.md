# Agent Prompt Template

You are extending a VCHarness-style one-cell-line experiment.

Goal: propose one child node that may improve validation Macro-F1 for CRISPR KO DEG classification.

Stable interface:

- Input config: JSON under `configs/` or `experiments/proposals/`
- Training command: `python -m vc_demo.train --config CONFIG --output-dir experiments/nodes/NODE_NAME`
- Metric file: `experiments/nodes/NODE_NAME/metrics.json`
- Primary selection metric: `best_val_macro_f1`

Allowed changes for A-level demo:

- change MLP width/depth/dropout
- change learning rate, weight decay, batch size, epochs
- add a small model module if it keeps the same forward signature
- update proposal notes explaining why this child should be tried

Do not download large datasets or foundation-model embeddings unless explicitly requested.
