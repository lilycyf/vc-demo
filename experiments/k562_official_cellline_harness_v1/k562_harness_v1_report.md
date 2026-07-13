# K562 Official Cell-Line Harness v1 Completion Report

## Verdict

K562 is complete for **Reusable Official Cell-Line Harness v1 / Phase-3**. This is not a 600+ proposal paper-scale claim. It is a reusable, strict, auditable cell-line harness with official task contract validation, artifact registry audit, root baselines, proposal-pool MCTS semantics, automatic implementation-loop evidence, strict acquisition/block behavior, and a parameterized transfer checklist for a user-specified second cell line.

Current branch: `k562-official-cellline-harness-v1`  
Base commit on this pod: `86959f1`

## Official Task Contract

Validation output: `experiments/k562_official_cellline_harness_v1/task_contract_validation.json`

- Cell line: K562 / K-562 official DEG task
- Data dir: `data/cell_lines/official_k562_cls`
- Split: train `1388`, val `154`, test `421`
- Target genes: `6640`
- Raw DEG labels: `-1`, `0`, `1`; training remaps to `0`, `1`, `2`
- Reward/selection metric: validation Macro-F1
- Final reporting metric: validation Macro-F1 and test Macro-F1
- Validation status: `passed` with issues `[]`

## Artifact Registry

Audit outputs:

- `artifact_registry_audit.json`
- `artifact_registry_audit_after_aido_acquisition.json`
- `model_dir_validation.json`
- `aido_cell_100m_model_dir_manifest.json`

Present after current-pod AIDO acquisition:

- `string_k562_gene_graph`
- `pathway_membership_matrix`
- `official_essential_deg_with_split_h5ad`
- `official_k562_aido_cell_100m_embedding_h5ad`
- `official_string_gnn_keep20_graph`
- `official_aido_cell_100m_model_dir`
- `official_gnn_simple_embedding_h5ad`
- `official_public_best_node_code`

Missing after current-pod AIDO acquisition:

- `esm2_gene_embedding_h5ad`
- `esm2_k562_target_manifest`
- `aido_gene_or_cell_embeddings`
- `scfoundation_cell_embeddings`
- `official_string_gnn_model_dir`

Notes:

- `official_aido_cell_100m_model_dir` was actively acquired from HuggingFace `genbio-ai/AIDO.Cell-100M`, revision `b14a88b962758102e618289f4340f989bd6eebe5`. Validation is `passed_with_warnings` and warns that tokenizer files are absent.
- `official_string_gnn_model_dir` remains missing on this pod. The acquisition registry marks it as non-automatic because the public HuggingFace repo currently does not expose verifiable weight files. The existing STRING graph artifacts are source-backed, but they are not equivalent to the missing trained model directory.
- `scfoundation_cell_embeddings` remains a valid strict blocker for scFoundation-family nodes. It has no automatic resolver and must not be replaced by a random embedding, small MLP, or K562 tabular proxy.

## Historical Proxy-Era Reference Numbers

These numbers are retained only as framework-pressure-test evidence from runs before commit `86959f1` made compact/native proxy implementations forbidden. They are **not formal paper-level baselines**, must not be compared against public VCHarness best scores, and must be rerun after exact public-static execution or full artifact-backed implementations are available.

From the 64/16 automatic-loop run:

- Best root: `official_k562_native_public_best_reimplementation`
- Val Macro-F1: `0.4332`
- Test Macro-F1: `0.4702`

From the 150/40 strict attempt:

- Best root: `official_k562_native_public_best_reimplementation`
- Val Macro-F1: `0.4221`
- Test Macro-F1: `0.4559`

## Automatic Proposal/Implementation Loop Evidence

### 64/16 clean run

Source branch: `official-k562-auto-impl-64x16`  
Run dir: `experiments/official_k562_auto_impl_64x16`  
Stop reason: `no improvement for 12 nodes`

- Total tree nodes: `56`
- Status counts: `{'trained': 17, 'pruned_not_selected': 39}`
- Proposal pools: `13`
- Pruned proposals: `39`
- Trained nodes including roots: `17`
- Auto-implemented trained nodes from search memory: `9`
- Native smoke passed count: `9`
- Backpropagation events: `4`
- Backprop non-trained count: `0`
- Fallback trace lines: `0`
- External static trace lines: `0`

Best trained rollout:

- Node: `official_k562_native_p2_official_string_gnn_attention_c7b091ac`
- Strategy: `official_string_gnn_attention`
- Val Macro-F1: `0.4421`
- Test Macro-F1: `0.4805`

### 150/40 strict attempt

Source branch: `official-k562-auto-impl-150`  
Run dir: `experiments/official_k562_auto_impl_150`  
Stop reason: `requires artifact acquisition for official_scfoundation_top_layer_finetune: scfoundation_cell_embeddings`

- Total tree nodes: `68`
- Status counts: `{'trained': 18, 'pruned_not_selected': 49, 'requires_artifact_acquisition': 1}`
- Proposal pools: `16`
- Pruned proposals: `49`
- Trained nodes including roots: `18`
- Auto-implemented trained nodes from search memory: `10`
- Native smoke passed count: `10`
- Artifact acquisition blocks: `1`
- Backpropagation events: `4`
- Backprop non-trained count: `0`
- Fallback trace lines: `0`
- External static trace lines: `0`

Best trained rollout:

- Node: `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6`
- Strategy: `official_target_graph_conditioned_head`
- Val Macro-F1: `0.4470`
- Test Macro-F1: `0.4829`
- Improvement over best root validation Macro-F1: `0.0249`

Strict blocker:

```json
{
  "items": [
    {
      "node": "official_k562_native_p8_official_scfoundation_top_layer_finetune_ba26b0e0",
      "strategy": "official_scfoundation_top_layer_finetune",
      "artifact_id": "scfoundation_cell_embeddings",
      "expected_path": "data/artifacts/scfoundation",
      "source": "precomputed scFoundation cell-state embedding or approved encoder output",
      "action": "search_download_or_build_real_artifact",
      "resume_after": "update registry, rerun artifact audit, then resume search without fallback"
    }
  ]
}
```


## Artifact Acquisition Loop

K562 Harness v1 now treats provenance/acquisition as a first-class part of the loop, not as an informal note. The current strict blockers were placed into:

- Queue: `experiments/k562_official_cellline_harness_v1/artifact_acquisition_queue.json`
- Report: `experiments/k562_official_cellline_harness_v1/artifact_acquisition/artifact_acquisition_report.json`
- Tasks:
  - `experiments/k562_official_cellline_harness_v1/artifact_acquisition/ACQUIRE_official_string_gnn_model_dir.md`
  - `experiments/k562_official_cellline_harness_v1/artifact_acquisition/ACQUIRE_scfoundation_cell_embeddings.md`

Acquisition-loop result:

| Artifact | Resolver | Automatic | Action | Status |
|---|---|---:|---|---|
| `official_string_gnn_model_dir` | `codex_research_download_from_official_genbio_or_string_gnn_source` | `False` | `generated_codex_research_task` | `requires_codex_research_download_or_build` |
| `scfoundation_cell_embeddings` | `codex_research_download_or_encode_from_official_scfoundation_source` | `False` | `generated_codex_research_task` | `requires_codex_research_download_or_build` |


Interpretation: these are still strict blockers, but now they are **blocked after acquisition dispatch**, not merely missing files. They require a separate Codex acquisition pass that searches official/primary sources, records provenance, validates tensor contracts, updates the registry, reruns artifact audit, and then resumes strict search. No fallback model or fabricated artifact is allowed.

## Current-Pod Sanity Attempt

A fresh low-budget sanity run on this pod was attempted after installing `requirements-official-k562.txt`. It stopped at strict preflight because `/home/Models/STRING_GNN` is absent and has no verified automatic resolver. This is a valid strict artifact boundary, not a training or implementation failure. AIDO.Cell-100M was acquired successfully; STRING_GNN was not fabricated.

## Completion Criteria Check

- Official K562 contract validation: passed
- Artifact registry audit: passed with explicit present/missing states
- Historical proxy-era root numbers recorded: yes, but excluded from formal paper-level conclusions
- Proposal pool generated: yes
- Pruned-not-selected proposals present: yes
- Automatic implementation loop executed in historical proxy-era runs: yes; formal rerun required under `86959f1+` rules
- Native smoke passed for historical generated nodes: yes; this is not evidence of formal full implementation
- 64/16 run clean: yes
- 150/40 run: strict artifact blocker, acceptable for v1
- Fallback count: 0
- Non-trained backprop count: 0
- External static backend: no trace use for generated children in these automatic-loop traces; public static wrapper remains the only intended use
- Forbidden files committed in this v1 branch: checked before commit

## Second Cell-Line Transfer Policy

K562 is the template-building cell line, not a leaked answer key for the next test. The reusable transfer prompt is parameterized and must receive the second cell line from the user at run time as `CELL_LINE_ID`.

The generic transfer checklist is:

- `experiments/k562_official_cellline_harness_v1/k562_to_second_cellline_transfer_prompt.md`

Rules for the second cell-line test:

- Do not hard-code or prefer any particular second cell line in repo-level runbooks.
- Discover public scaffold paths from `CELL_LINE_ID` only after the transfer task is launched.
- Establish task contract from source-backed artifacts before creating roots or search runs.
- Do not silently switch to a different cell line if the requested one cannot be validated; block and report the reason.
- Treat K562 public scaffold metrics only as template sanity references, not as score targets.
- Treat K562 proxy-era run numbers only as historical framework-wiring evidence.

The purpose of the second cell-line run is to prove that the K562 Harness v1 pattern is reusable without prior knowledge of the held-out cell line.
