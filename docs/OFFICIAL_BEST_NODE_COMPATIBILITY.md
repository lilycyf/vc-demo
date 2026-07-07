# Official Best-Node Compatibility

The public VCHarness K562 best node is `node2-1-1-1-1-1`. It requires more than the official K562 TSV data contract:

- Python packages: `lightning.pytorch`, `transformers`, `peft`, `anndata`, `scanpy`, `pandas`, `torch`
- AIDO model dir: `/home/Models/AIDO.Cell-100M`
- STRING_GNN model dir: `/home/Models/STRING_GNN`
- AIDO public node entrypoint: `AutoModel.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)` and `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`
- STRING_GNN public node entrypoint: `AutoModel.from_pretrained(STRING_MODEL_DIR, trust_remote_code=True)` plus `graph_data.pt` and `node_names.json`

Run the strict environment check:

```bash
python scripts/check_official_best_node_compatibility.py \
  --output experiments/official_k562_task_contract/best_node_compatibility.json
```

Run the public best-node entrypoint check:

```bash
python scripts/check_official_best_node_compatibility.py \
  --attempt-load \
  --output experiments/official_k562_task_contract/best_node_compatibility_load.json
```

Run the official ModelGenerator AIDO direct-load check:

```bash
PYTHONPATH=/workspace/_external/ModelGenerator/huggingface/aido.cell \
python scripts/check_official_best_node_compatibility.py \
  --attempt-load \
  --attempt-modelgenerator-aido-load \
  --output experiments/official_k562_task_contract/best_node_compatibility_after_deps.json
```

The distinction matters:

- `AutoModel` / `AutoTokenizer` is the entrypoint used by the public VCHarness best-node code.
- `CellFoundationConfig` / `CellFoundationModel` from ModelGenerator is the current official AIDO.Cell README path.
- AIDO.Cell uses a fixed 19,264-gene expression matrix with alignment and preprocessing, not a normal text tokenizer.

Current interpretation:

- If the ModelGenerator direct load passes, the AIDO.Cell-100M weights are usable.
- If `AutoTokenizer` still fails, the public best node cannot be run unchanged.
- If `/home/Models/STRING_GNN` is absent, the best node cannot be run unchanged because it requires STRING_GNN weights, `graph_data.pt`, and `node_names.json`.

This check is deliberately strict. If dependency, tokenizer, model-class, or STRING_GNN loading fails, the correct behavior is to record a blocker and acquire or reconstruct the missing official asset. Do not train a fallback and call it the public best node.
