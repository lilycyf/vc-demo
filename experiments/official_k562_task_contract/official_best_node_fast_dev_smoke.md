# Official K562 Best Node Fast-Dev Smoke

Date: 2026-07-07

Branch: `official-k562-missing-files`

Public node:

```text
/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py
```

Command:

```bash
cd /workspace/_external/VCHarness/K562_cls/static
PYTHONPATH=/workspace/_external/ModelGenerator/huggingface/aido.cell \
python node2-1-1-1-1-1_code.py \
  --fast-dev-run \
  --micro-batch-size 1 \
  --global-batch-size 1 \
  --num-workers 0 \
  --max-epochs 1
```

Data symlinks were prepared under `/workspace/_external/VCHarness/data`:

- `train.tsv -> /workspace/vc-demo/data/cell_lines/official_k562_cls/train.tsv`
- `val.tsv -> /workspace/vc-demo/data/cell_lines/official_k562_cls/val.tsv`
- `test.tsv -> /workspace/vc-demo/data/cell_lines/official_k562_cls/test.tsv`

## Result

The public best node completed one train batch, one validation batch, and one test batch on a single NVIDIA L4.

Observed smoke metrics:

- train loss: approximately `1.370`
- validation F1: approximately `0.333`
- test loss: `1.2349580526351929`
- test predictions: 1 row written by the public node

This is a connectivity and numerical-stability smoke test only. It is not a score reproduction.

## Fix Needed During Smoke

The first successful setup smoke was not sufficient: the first real forward pass initially produced NaN. Diagnosis showed that `AutoModel.from_pretrained("/home/Models/AIDO.Cell-100M")` was not loading AIDO weights correctly because the original checkpoint keys were prefixed with `bert.`, while the direct `CellFoundationModel` AutoModel class expects unprefixed keys.

`scripts/prepare_official_k562_missing_files.py` now:

- preserves the original AIDO checkpoint as `model.original_with_bert_prefix.safetensors`
- writes an AutoModel-compatible `model.safetensors` with stripped `bert.` prefixes
- drops `cls.*` MLM-head keys for the direct backbone path
- sets safetensors metadata `format=pt`
- patches ModelGenerator's `base_model_prefix` to the empty string for this compatibility path
- keeps the `.bert` property alias for public VCHarness code that accesses `self.backbone.model.bert.gene_embedding`

After that fix:

- AIDO `AutoModel` reports `missing=0`, `unexpected=0`
- single-batch logits are finite
- single-batch loss is finite
- full fast-dev train/val/test smoke completes

## Caveat

The STRING_GNN directory is still a public-artifact compatibility reconstruction, not the original unavailable `genbio-ai/STRING_GNN` checkpoint. Full scientific comparison must label this distinction.
