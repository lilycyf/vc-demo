# Official K562 Generic Cell-Line Transfer Smoke Report

## Verdict

The generic Official Cell-Line Harness v1 template was instantiated with `CELL_LINE_ID=K562` without using `TEMPLATE_CELL_LINE_ID` or `TARGET_CELL_LINE_ID` parameters. Discovery, task contract validation, public scaffold audit, backend/root audit, and artifact acquisition dispatch completed.

The 64 proposal / 16 trained rollout search did **not** proceed to proposal generation or training because strict backend preflight blocked on a real missing artifact: `official_string_gnn_model_dir` at `/home/Models/STRING_GNN`. This is a valid strict artifact boundary, not a fallback or training failure.

Therefore this self-instantiation run does not itself reach full Phase-3 trained-rollout completion, but it verifies that the generic template correctly routes K562 into task/artifact/acquisition closure instead of bypassing missing artifacts.

## Parameters

- `CELL_LINE_ID=K562`
- `TASK_SOURCE=DISCOVER_FROM_PUBLIC_VCHARNESS`
- `SPLIT_SOURCE=DISCOVER_FROM_TASK_SOURCE`
- `TARGET_GENE_ORDER_SOURCE=DISCOVER_FROM_TASK_SOURCE`
- Branch: `official-k562-transfer-smoke`

## Task Contract

- Status: `passed`
- Split sizes: `{'train': 1388, 'val': 154, 'test': 421}`
- Target genes: `6640`
- Issues: `[]`

## Public Scaffold Discovery

- Status: `passed`
- Public track: `/workspace/_external/VCHarness/K562_cls`
- Static count: `309`
- Memory count: `153`
- Public best score: `0.512766198238068`

## Backend And Root Audit

- Backend status: `failed`
- Missing required artifacts: `['official_string_gnn_model_dir']`
- Root configs audited: `['configs/official_k562_roots/root_aido_embedding_mlp.json', 'configs/official_k562_roots/root_aido_gnn_embedding_mlp.json', 'configs/official_k562_roots/root_public_best_node_smoke.json']`
- external_static_node use: only `configs/official_k562_roots/root_public_best_node_smoke.json`, an explicit public wrapper.

## 64x16 Search Attempt

- Command wrapper: `scripts/run_official_cellline_harness_search.py --cell-line K562 ...`
- Exit code: `1`
- Stop reason: strict preflight missing `official_string_gnn_model_dir`
- Generated proposals: `0`
- Trained rollouts: `0`
- Pruned proposals: `0`
- Pending implementations: `0`
- Failed trainings: `0`
- Blocked/acquisition: `1`

## Artifact Acquisition Closure

- Queue: `experiments/official_k562_auto_impl_64x16/acquisition_queue.json`
- Report: `experiments/official_k562_auto_impl_64x16/artifact_acquisition/artifact_acquisition_report.json`
- Artifact `official_string_gnn_model_dir`: action `generated_codex_research_task`, status `requires_codex_research_download_or_build`, task `experiments/official_k562_auto_impl_64x16/artifact_acquisition/ACQUIRE_official_string_gnn_model_dir.md`

## Guardrail Audit

- Fallback used: `0`
- Compact/native proxy used: `0`
- Pruned node training: `0`
- Non-trained backprop: `0`
- Forbidden files committed: checked before commit

## Recommendation

Do not proceed to multi-cell-line paper-scale from this self-instantiation run until `official_string_gnn_model_dir` is acquired from a source-backed public/official artifact or the backend is redesigned to make roots that do not require that exact public checkpoint independently runnable under strict audit. Do not fallback.

## Raw Preflight Output

```json
{
  "status": "failed",
  "backend": "official_k562_tsv_mcts_harness",
  "data_contract": {
    "status": "passed",
    "data_dir": "data/cell_lines/official_k562_cls",
    "split_sizes": {
      "train": 1388,
      "val": 154,
      "test": 421
    },
    "target_gene_rows": 6640,
    "n_genes_seen": [
      6640
    ],
    "label_counts_by_split": {
      "train": {
        "-1": 405816,
        "0": 8510952,
        "1": 299552
      },
      "val": {
        "-1": 32336,
        "0": 963695,
        "1": 26529
      },
      "test": {
        "-1": 89553,
        "0": 2637627,
        "1": 68260
      }
    },
    "issues": []
  },
  "registry_path": "configs/artifacts/k562_registry.json",
  "required_artifacts": [
    "official_essential_deg_with_split_h5ad",
    "official_k562_aido_cell_100m_embedding_h5ad",
    "official_gnn_simple_embedding_h5ad",
    "official_aido_cell_100m_model_dir",
    "official_string_gnn_model_dir",
    "official_public_best_node_code"
  ],
  "missing_required_artifacts": [
    {
      "id": "official_string_gnn_model_dir",
      "family": "foundation_model_checkpoint",
      "provider": "STRING_GNN",
      "status": "missing_until_downloaded",
      "path": "/home/Models/STRING_GNN",
      "source": "Exact model directory expected by public VCHarness node code; not equivalent to STRING graph edge file.",
      "usable_for": [
        "official_vcharness_best_node"
      ],
      "required_for_blueprints": [
        "official_aido_string_fusion",
        "official_k562_string_gnn_attention",
        "official_public_best_node",
        "official_string_gnn_attention",
        "official_native_public_best_reimplementation"
      ],
      "do_not_fabricate": true,
      "present": false,
      "resolved_status": "missing"
    }
  ],
  "present_artifacts": [
    "string_k562_gene_graph",
    "pathway_membership_matrix",
    "official_essential_deg_with_split_h5ad",
    "official_k562_aido_cell_100m_embedding_h5ad",
    "official_string_gnn_keep20_graph",
    "official_aido_cell_100m_model_dir",
    "official_gnn_simple_embedding_h5ad",
    "official_public_best_node_code"
  ],
  "missing_artifacts": [
    "esm2_gene_embedding_h5ad",
    "esm2_k562_target_manifest",
    "aido_gene_or_cell_embeddings",
    "scfoundation_cell_embeddings",
    "official_string_gnn_model_dir"
  ],
  "root_configs": [
    {
      "path": "configs/official_k562_roots/root_aido_embedding_mlp.json",
      "present": true,
      "node_name": "official_k562_root_aido_embedding_mlp",
      "dataset_type": "official_k562_tsv",
      "data_dir": "data/cell_lines/official_k562_cls",
      "embedding_h5ad": "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad",
      "embedding_h5ads": [],
      "execution_backend": "native_train",
      "script_path": ""
    },
    {
      "path": "configs/official_k562_roots/root_aido_gnn_embedding_mlp.json",
      "present": true,
      "node_name": "official_k562_root_aido_gnn_embedding_mlp",
      "dataset_type": "official_k562_tsv",
      "data_dir": "data/cell_lines/official_k562_cls",
      "embedding_h5ad": null,
      "embedding_h5ads": [
        "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad",
        "data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad"
      ],
      "execution_backend": "native_train",
      "script_path": ""
    },
    {
      "path": "configs/official_k562_roots/root_public_best_node_smoke.json",
      "present": true,
      "node_name": "official_k562_public_best_node2_1_1_1_1_1_smoke",
      "dataset_type": "official_k562_tsv",
      "data_dir": "data/cell_lines/official_k562_cls",
      "embedding_h5ad": null,
      "embedding_h5ads": [],
      "execution_backend": "external_static_node",
      "script_path": "node2-1-1-1-1-1_code.py"
    }
  ],
  "issues": [
    "required artifact official_string_gnn_model_dir is missing at /home/Models/STRING_GNN"
  ],
  "notes": [
    "This backend lets vc_demo.harness.program_run search on the official K562 TSV task.",
    "The public VCHarness best node remains a separate compatibility benchmark and may use external node code.",
    "Strict artifact mode must block or acquire missing artifacts; do not train fallback nodes for claimed official artifacts.",
    "Formal paper-level runs forbid compact/proxy native implementations; use external public static benchmark or full artifact-backed implementations."
  ]
}

```
