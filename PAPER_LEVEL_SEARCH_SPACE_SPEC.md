# Paper-Level Search Space Specification

This file upgrades the repo from a demo-size VCHarness-style runbook to a paper-level search-space contract. It is intentionally a specification, not a full implementation. Most biological foundation-model and graph-prior modules are planned blueprints that should be implemented on demand only when the search selects them.

## Purpose

The current framework can prove that a program-node search loop works. A paper-level VCHarness run should prove something stronger: an agent-driven search can explore a broad model-design space and discover useful architectures under a controlled budget.

The paper-scale target is not to pre-code every possible model. The target is to make the design space explicit enough that a Codex agent can generate, implement, train, evaluate, and record selected nodes without inventing undocumented rules mid-run.

## Search Scale

Demo scale:

- 10-30 trained nodes
- one cell line
- mostly lightweight root models
- child nodes often change optimizer, dropout, hidden size, or one compact architecture block
- useful for validating the loop, not enough to validate large-scale model discovery

Paper-level scale should be staged:

| Phase | Goal | Trained Nodes | Purpose |
|---|---:|---:|---|
| Phase 0 | smoke test | 3-5 | verify code, data, metrics, and node artifacts |
| Phase 1 | pilot | 20-50 | verify parent selection and planned-blueprint handling |
| Phase 2 | single-cell-line serious search | 100-200 | approximate paper-style search on one cell line |
| Phase 3 | multi-cell-line replication | 400-800+ | approximate paper-scale total model count |

A node is a complete trainable design, not merely a learning-rate tweak. Each node must define:

- data feature version
- perturbation representation
- cell/gene/protein representation
- architecture program or blueprint
- fusion method
- loss and training schedule
- evaluation metrics
- parent and child relationship
- implementation status
- failure or pending status
- cost and wall-time metadata when available

## Root Families

A paper-level search should start from multiple root families rather than a single baseline. The minimum serious-search target is six or more root families.

Recommended root families:

1. expression MLP baseline
2. delta-expression baseline
3. learned perturbation-embedding baseline
4. gene/protein embedding baseline
5. graph-prior baseline
6. biological foundation-embedding baseline
7. gated multimodal fusion baseline
8. cross-attention multimodal fusion baseline
9. mixture-of-experts baseline
10. selective adapter/fine-tuning baseline

Root families can be implemented, planned, or blocked by missing artifacts. Missing artifacts must be recorded explicitly; do not fake a foundation-model embedding or graph.

## Child Expansion Levels

Every child proposal must state its change level:

| Level | Meaning | Examples |
|---|---|---|
| 1 | training-only refinement | LR, dropout, weight decay, schedule |
| 2 | compact architecture change | residual block, gated MLP, low-rank head |
| 3 | representation change | one-hot perturbation to learned gene embedding |
| 4 | fusion change | concat to gated fusion, cross-attention, MoE |
| 5 | biological prior or foundation module | STRING GNN, ESM2, scFoundation, AIDO |

A serious run must not spend most of its budget on Level 1 changes. If several consecutive children only change training details, the agent must propose or select Level 3-5 candidates.

## Model Space Families

### 1. Cell Expression Encoders

Purpose: encode the cell state or expression feature vector.

Planned options:

- raw expression MLP
- normalized expression MLP
- delta-expression encoder
- HVG encoder
- autoencoder-style expression encoder
- scFoundation-style frozen encoder
- AIDO-style cell encoder

### 2. Perturbation Representation Modules

Purpose: represent the perturbation itself.

Planned options:

- one-hot perturbation
- learned perturbation embedding
- gene ID embedding
- perturbation effect embedding
- dose or condition embedding
- prior-informed perturbation embedding

### 3. Gene And Protein Foundation Embeddings

Purpose: encode biological semantics of the perturbed or target genes.

Planned options:

- ESM2 protein embedding projection
- AIDO gene/protein embedding projection
- gene text description embedding
- pathway embedding
- pretrained gene embedding table

These usually require external artifacts. Do not download large artifacts unless explicitly approved by the user.

### 4. Graph Priors

Purpose: model gene-gene, protein-protein, pathway, or regulatory structure.

Planned options:

- STRING/PPI message passing
- graph attention over target genes
- pathway pooling
- perturbation propagation graph module
- graph Laplacian smoothing

Graph modules require aligned graph edges. If graph data is unavailable, the node should become `needs_implementation` or `blocked_missing_artifact`, not silently degrade into a fake graph.

### 5. Multimodal Fusion

Purpose: combine expression, perturbation, gene/protein, and graph signals.

Planned options:

- concat fusion
- gated fusion
- FiLM conditioning
- cross-attention fusion
- bilinear fusion
- mixture of experts
- residual multimodal fusion
- adapter fusion

Paper-level searches should treat fusion strategy as a first-class search dimension.

### 6. Prediction Heads

Purpose: map fused representations to DEG labels or perturbation-response outputs.

Planned options:

- standard DEG classifier
- class-balanced classifier
- focal-loss classifier
- low-rank target-gene head
- uncertainty/calibration head
- multilabel or ranking head when task semantics require it

### 7. Training Strategy Modules

Purpose: modify optimization without pretending it is a new biological architecture.

Planned options:

- class-weighted loss
- focal loss
- label smoothing
- warmup and cosine schedule
- early stopping
- gradient clipping
- selective freezing/unfreezing
- adapter-only or low-rank fine-tuning

Training-only changes are allowed, but must be labeled Level 1.

## MCTS Selection Contract

The harness must expose auditable MCTS statistics rather than only saying that it is MCTS-like.

Selection supports two formulas:

```text
UCT(parent) = Q(parent) + c * sqrt(log(N) / n(parent))
```

```text
PUCT(parent) = Q(parent) + c_puct * P(parent) * sqrt(N) / (1 + n(parent))
```

Where:

- `Q(parent)` is the mean rollout reward backpropagated through that node.
- `N` is the total visit count among selectable parents.
- `n(parent)` is the visit count of the candidate parent.
- `P(parent)` is an explicit node prior when available, otherwise a normalized weak empirical prior from validation reward.
- reward is validation Macro-F1 unless the task file says otherwise.

Each selection must record:

- selected parent
- selection policy: `uct` or `puct`
- score
- exploitation/Q term
- exploration term
- prior
- visits
- candidate list

Each completed rollout must backpropagate exactly one reward from leaf to root and update:

- visits
- total value
- mean reward
- squared value
- reward variance
- best reward
- last reward
- rollout reward history

If the paper does not publish a more specific formula, this repo treats the above as the paper-compatible MCTS contract. Do not claim exact formula identity beyond the public paper details available to the run.

## On-Demand Implementation Contract

The blueprint registry may contain many planned models. Planned means selectable, not already executable.

When a planned blueprint is selected:

1. create a node with `status = needs_implementation`
2. write `IMPLEMENTATION_REQUEST.md`
3. Codex reads the request and implements only that node-local `model.py`
4. run compile/smoke checks
5. train with `python -m vc_demo.harness.train_pending`
6. record metrics or failure reason
7. continue the search if the task budget allows

The agent must not:

- alter data splits
- tune on the test set
- fake external embeddings or graphs
- silently replace a planned foundation module with a small MLP without recording the fallback
- commit large artifacts, checkpoints, raw data, secrets, or tokens

## Serious-Search Minimum Bar

A one-cell-line paper-style run should aim for at least:

- 6 root families considered
- 30 trained nodes minimum for a small serious run
- 100-200 trained nodes for a fuller single-cell-line run
- 5 planned blueprint proposals
- 2 planned blueprints implemented on demand
- at least 2 tree depths below a root
- at least one Level 4 or Level 5 child
- cost and wall-time tracking in the final report

## Reporting Requirements

The final conclusion must include:

- trained node count
- failed node count
- pending node count
- root families tried
- planned blueprints selected
- planned blueprints implemented
- best root
- best overall node
- improvement over best root
- path to best node
- best-so-far curve or table
- cost and wall-time estimate
- limitations relative to the paper

## Key Principle

Do not make the repo large by pre-implementing everything. Make the search contract large and explicit, then let the agent implement only the blueprints selected by the search.

## Target-Aware Artifact Upgrade

The repo now supports a stronger artifact contract documented in `TARGET_AWARE_ARTIFACT_MODEL_SPACE.md`. For foundation-model routes such as ESM2, AIDO, scFoundation, and STRING, a paper-level child should prefer explicit target-gene or graph-aware use when the artifact exists. The minimum executable example is `model_type: target_aware_bilinear`, which reads `model.artifact_manifest_path` and loads an aligned `target_gene_embeddings.npz` table.

A node should not be described as using a biological foundation artifact merely because a dense model receives appended row-level embedding features. Record whether it uses perturbation-side features only, target-side artifacts, graph edges, or both.
