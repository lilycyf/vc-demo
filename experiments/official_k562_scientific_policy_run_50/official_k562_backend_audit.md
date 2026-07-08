# Official K562 Harness Backend Audit

- Status: `passed`
- Backend: `official_k562_tsv_mcts_harness`
- Registry: `configs/artifacts/k562_registry.json`
- Data contract status: `passed`
- Required artifacts: official_essential_deg_with_split_h5ad, official_k562_aido_cell_100m_embedding_h5ad, official_gnn_simple_embedding_h5ad, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_public_best_node_code
- Missing required artifacts: none

## Root Configs

| Config | Node | Dataset | Data dir | Embeddings |
|---|---|---|---|---|
| `configs/official_k562_root_aido_embedding_mlp.json` | `official_k562_root_aido_embedding_mlp` | `official_k562_tsv` | `data/cell_lines/official_k562_cls` | `data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad` |
| `configs/official_k562_root_aido_gnn_embedding_mlp.json` | `official_k562_root_aido_gnn_embedding_mlp` | `official_k562_tsv` | `data/cell_lines/official_k562_cls` | `data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad, data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad` |
| `configs/official_k562_public_best_node_smoke.json` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `official_k562_tsv` | `data/cell_lines/official_k562_cls` | `` |
| `configs/official_k562_native_public_best_reimplementation.json` | `official_k562_native_public_best_reimplementation` | `official_k562_tsv` | `data/cell_lines/official_k562_cls` | `data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad, data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad` |

## Issues

- none

## Notes

- This backend lets vc_demo.harness.program_run search on the official K562 TSV task.
- The public VCHarness best node remains a separate compatibility benchmark and may use external node code.
- Strict artifact mode must block or acquire missing artifacts; do not train fallback nodes for claimed official artifacts.
