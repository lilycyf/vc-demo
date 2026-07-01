# F. Program-Node Harness Upgrade

This upgrade moves the demo from config-level search toward code-level program search while keeping model choices as a manifest, not as a fully implemented monolith.

## Key Design Change

Model choices now live in a blueprint manifest:

```text
src/vc_demo/harness/model_blueprints.py
```

Each blueprint has:

- `id`
- `status`: `implemented` or `planned`
- `category`
- `role`
- `requires`

Only `implemented` blueprints are executable today. Planned blueprints are intentionally listed but not implemented, so the architecture can express a larger VCHarness-style design space without pretending every idea is already runnable.

## Implemented Blueprints

- `dual_path_gated_low_rank`: dual encoders, input-conditioned gate, low-rank target head
- `mixture_of_experts`: router over compact expert MLPs

## Planned Blueprint Examples

- `film_conditioned_residual`
- `target_factor_router`
- `gene_embedding_adapter`
- `ppi_graph_message_passing`
- `foundation_embedding_fusion`
- `cross_attention_gene_perturbation`
- `selective_adapter_finetune`
- `multi_task_cellline_conditioning`

## Program Node Output

An executable child node writes its own model program:

```text
experiments/<experiment>/programs/<node>/model.py
experiments/<experiment>/programs/<node>/README.md
experiments/<experiment>/programs/<node>/proposal.json
```

The child config points to that source file:

```json
{
  "model_type": "custom_program",
  "custom_model_path": "experiments/.../programs/<node>/model.py",
  "custom_model_class": "GeneratedModel"
}
```

## Smoke Test

```bash
cd /workspace/vc-demo
python -m vc_demo.harness.program_run   --experiment k562_program_node_smoke   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_residual_mlp.json   --run-dir experiments/k562_program_node_smoke   --budget-nodes 2   --max-epochs 1   --max-children 2   --stop-no-improve 2   --seed 11   --reset
```

## Formal Run Template

```bash
cd /workspace/vc-demo
python -m vc_demo.harness.program_run   --experiment k562_program_node_search   --root-configs configs/k562_roots/*.json   --run-dir experiments/k562_program_node_search   --budget-nodes 16   --max-epochs 4   --max-children 3   --stop-no-improve 8   --exploration 0.7   --seed 11   --reset
```

This is still not the full paper system, but the search unit is now a code-backed architecture program selected from an extensible model blueprint manifest.
