# K562 Full Drain Target Rerun Final Audit

- Run dir: `experiments/k562_full_drain_target_rerun`
- Stop reason: unresolved source-backed artifact blocker: official_string_gnn_model_dir expected at /home/Models/STRING_GNN is not publicly/materially available in acquired source; only .gitattributes was downloadable from genbio-ai/STRING_GNN, so strict mode forbids fallback/proxy training of STRING_GNN checkpoint-dependent nodes
- Generated proposals: 198
- Trained selected rollouts: 30
- Pruned proposals: 126
- Skipped: 1
- Blocked/acquisition: 1
- Failed: 1
- Pending: 0
- Queued candidates remaining: 34
- Global queue fully drained: False

## Best Root

- `official_k562_root_aido_gnn_embedding_mlp` val 0.488099, test 0.543651

## Best Generated Child

- `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` (official_string_neighborhood_attention) val 0.494783, test 0.521812
- Delta vs best root: +0.006684
- Delta vs target 0.50: -0.005217
- Root-beating objective achieved: True
- Score target achieved: False

## Strict Artifact Blocker

- Artifact: `official_string_gnn_model_dir`
- Expected path: `/home/Models/STRING_GNN`
- Attempted primary source: `genbio-ai/STRING_GNN` on Hugging Face.
- Result: repository download/list yielded only `.gitattributes`; no substantive checkpoint/config/weights were available.
- Public VCHarness code requires an actual STRING_GNN model directory and 256-dim embeddings; the existing STRING graph text file is not equivalent.
- Action: kept artifact missing/acquisition-blocked; no fallback/proxy training was used.

## Guardrail Audit

- fallback count: 0
- compact/proxy count: 0
- non-trained backprop count: 0
- backend anomaly count: 0

## Notes

The run did not stop because a pending node finished. It continued through additional queued candidates and stopped after the strict source-backed acquisition boundary for the missing STRING_GNN checkpoint model directory was reached. The global queue was not fully drained because that blocker is a documented real stop condition for this run.
