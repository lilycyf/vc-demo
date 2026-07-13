You only operate through RunPod SSH in `/workspace/vc-demo`. Do not read or run a local repo.

Goal:
Transfer the completed K562 Official Cell-Line Harness v1 / Phase-3 to a second cell line: hTERT-RPE1. The target is not paper-scale 600+ proposals; the target is to reach the same phase as K562: source-backed task contract, artifact audit, root baselines, proposal-pool MCTS, automatic implementation loop, strict acquisition/block behavior, and final cross-cell-line report.

Base branch:
`official-k562-gap-closing`

New branch:
`official-htert-rpe1-transfer-smoke`

Core rules:
- Work only on RunPod `/workspace/vc-demo`.
- Do not modify K562 data, split, labels, metrics, target gene order, or artifact provenance.
- Do not use fallback models or fabricated artifacts.
- Missing artifacts must go through acquisition first; write an acquisition queue, run the acquisition resolver/tool, and generate `ACQUIRE_<artifact>.md` before declaring a strict blocker. If source/order/shape/provenance cannot be verified after that pass, block.
- Do not reuse K562-specific embeddings for hTERT-RPE1.
- Generated native children must not inherit `external_static_node`.
- `external_static_node` is allowed only for explicit public static wrappers/benchmarks.
- Only trained nodes can backpropagate reward.
- Do not commit `data/`, `nodes/`, checkpoints, weights, `.h5ad`, `.npz`, `/home/Models`, `/workspace/_external`, `__pycache__`, or egg-info.

Step 1: sync and create branch.

```bash
cd /workspace/vc-demo
GIT_SSH_COMMAND="ssh -i /root/.ssh/vc_demo_github_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git fetch origin
git checkout -B official-htert-rpe1-transfer-smoke origin/official-k562-gap-closing
git rev-parse --short HEAD
```

Step 2: read K562 v1 handoff.

```bash
cat experiments/k562_official_cellline_harness_v1/k562_harness_v1_report.md
cat experiments/k562_official_cellline_harness_v1/k562_reusable_checklist.md
cat experiments/k562_official_cellline_harness_v1/k562_harness_v1_audit_summary.json
```

Step 3: audit public hTERT-RPE1 scaffold.

Read only:
- `/workspace/_external/VCHarness/hTERT-RPE1_cls/mcts_data.json`
- `/workspace/_external/VCHarness/hTERT-RPE1_cls/memory`
- `/workspace/_external/VCHarness/hTERT-RPE1_cls/static`

Write:
- `experiments/official_htert_rpe1_transfer/public_scaffold_audit.json`
- `experiments/official_htert_rpe1_transfer/public_scaffold_audit.md`

Record static count, memory count, public best node id/path, public best score, top 10 public nodes, and comparison to K562. K562 reference: static 309, memory 153, public best 0.51277. hTERT-RPE1 reference from current scaffold: static 331, memory 166, public best about 0.51816.

Step 4: establish hTERT-RPE1 task contract.

Preferred official source:
`data/artifacts/official_k562/essential_deg_with_split.h5ad`

If `h5py`, `anndata`, or `scanpy` are missing, install the official requirements in RunPod:

```bash
python -m pip install -r requirements-official-k562.txt
```

Build a generalized official cell-line task builder if the repo still has only K562-specific scripts. Preserve K562 behavior exactly. Generate:

```text
data/cell_lines/official_htert_rpe1_cls/train.tsv
data/cell_lines/official_htert_rpe1_cls/val.tsv
data/cell_lines/official_htert_rpe1_cls/test.tsv
data/cell_lines/official_htert_rpe1_cls/target_genes.tsv
data/cell_lines/official_htert_rpe1_cls/manifest.json
```

Requirements:
- 3-class DEG labels.
- 6640 target genes, or explain and block if official source proves a different contract.
- Fixed train/val/test split.
- Target gene order aligned to official/public scaffold.
- Macro-F1 reward on validation; test Macro-F1 report-only.

Write:
- `experiments/official_htert_rpe1_transfer/task_contract_audit.json`
- `experiments/official_htert_rpe1_transfer/task_contract_audit.md`

If hTERT-RPE1 rows do not exist in the official source, switch to HepG2 only after recording the reason.

Step 5: build hTERT-RPE1 artifact registry and root configs.

Add minimal generalized cell-line configs/helpers while keeping K562 unchanged.

Separate artifacts as:
- reusable: official source parser, STRING source graph/checkpoint only if tensor contract is cell-line independent, pathway source definitions;
- hTERT-RPE1-specific: DEG split, AIDO embedding h5ad, GNN embedding h5ad, scFoundation embeddings, public static wrapper path.

For missing hTERT-RPE1-specific artifacts:
- inspect `configs/artifacts/acquisition_sources.json`;
- inspect repo acquisition/build scripts;
- inspect public GenBio HuggingFace / VCHarness / ModelGenerator sources;
- acquire/build only when source, revision, row order, shape, and provenance are verifiable;
- otherwise write acquisition/blocker.

Write:
- `configs/artifacts/htert_rpe1_registry.json`
- `configs/official_htert_rpe1_roots/*.json`
- `experiments/official_htert_rpe1_transfer/artifact_registry_audit.json`

Step 6: run root baselines if artifacts are present/acquired.

Expected roots:
- hTERT-RPE1 AIDO embedding MLP
- hTERT-RPE1 AIDO+GNN embedding MLP
- hTERT-RPE1 public static wrapper/benchmark

Write:
- `experiments/official_htert_rpe1_transfer/root_baseline_summary.md`

If a root artifact is missing, acquire first. If still unverifiable, block. Do not fallback.

Step 7: run automatic implementation loop.

If the repo has only `scripts/run_official_k562_harness_search.py`, minimally generalize it to `scripts/run_official_cellline_harness_search.py` with a `--cell-line` argument. K562 behavior must remain unchanged.

Run 64 proposals / 16 trained rollouts:

```bash
PYTHONPATH=src python scripts/run_official_cellline_harness_search.py   --cell-line hTERT-RPE1   --run-dir experiments/official_htert_rpe1_auto_impl_64x16   --experiment official_htert_rpe1_auto_impl_64x16   --root-configs configs/official_htert_rpe1_roots/*.json   --budget-proposals 64   --budget-trained-nodes 16   --candidate-pool-size 4   --max-epochs 1   --max-children 8   --stop-no-improve 12   --selection-policy uct   --official-blueprint-space   --allow-planned-blueprints   --strict-artifacts   --enable-implementation-loop   --implementation-repair-attempts 3   --reset
```

If clean, run 150 proposals / 40 trained rollouts:

```bash
PYTHONPATH=src python scripts/run_official_cellline_harness_search.py   --cell-line hTERT-RPE1   --run-dir experiments/official_htert_rpe1_auto_impl_150   --experiment official_htert_rpe1_auto_impl_150   --root-configs configs/official_htert_rpe1_roots/*.json   --budget-proposals 150   --budget-trained-nodes 40   --candidate-pool-size 4   --max-epochs 1   --max-children 8   --stop-no-improve 30   --selection-policy uct   --official-blueprint-space   --allow-planned-blueprints   --strict-artifacts   --enable-implementation-loop   --implementation-repair-attempts 3   --reset
```

Step 8: handle blockers.

If an artifact is missing:
- add it to the run acquisition queue with artifact id, node, strategy, expected path, and source hint;
- run `PYTHONPATH=src python -m vc_demo.harness.artifact_acquisition --queue <queue> --registry <registry> --sources configs/artifacts/acquisition_sources.json --cell-line <CELL_LINE> --output-dir <run>/artifact_acquisition --execute-known`;
- run the explicit resolver if `can_execute_automatically=true`;
- otherwise create an acquisition task/report with source questions and required output contract;
- update registry/audit only after successful source-backed acquisition;
- resume the same run if the artifact becomes present;
- do not write or train fallback `model.py`.

If `requires_external_codex` appears:
- read the node-local `CODEX_IMPLEMENTATION_TASK.md`;
- implement only if required artifacts are present;
- otherwise acquisition/block.

Step 9: write final reports.

Write:
- `experiments/official_htert_rpe1_transfer/final_report.md`
- `experiments/cross_cellline_stage_report.md`

The final report must answer:
- Did hTERT-RPE1 reach K562 Phase-3 / Harness v1?
- If not, which artifact or task contract blocked it?
- K562 current completion level.
- hTERT-RPE1 public scaffold vs K562 public scaffold.
- Root baseline val/test Macro-F1.
- Best trained rollout val/test Macro-F1.
- Best root, best rollout, improvement.
- Generated proposals, trained rollouts, pruned proposals.
- Blocked/acquisition count, failed count, pending count.
- Auto implementation stats: auto implemented, native smoke passed, repair attempts, repair failures, requires_external_codex.
- Fallback count, must be 0.
- Backprop_nontrained count, must be 0.
- Whether external_static_node was only used for public wrapper.
- Whether to proceed to multi-cell-line paper-scale.

Step 10: commit and push.

Allowed:
- source/framework generalization changes;
- hTERT-RPE1 configs/scripts;
- small JSON/MD reports/audits;
- tree/trace/queues/proposals/program metadata/model.py/native smoke JSON.

Forbidden:
- `data/`
- `nodes/`
- checkpoints
- weights
- `.h5ad`
- `.npz`
- `/home/Models`
- `/workspace/_external`
- `__pycache__`
- egg-info

Run staged check:

```bash
python - <<'PY'
import subprocess
paths = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
forbidden = [
    p for p in paths
    if p.startswith("data/")
    or "/nodes/" in p
    or "checkpoint" in p.lower()
    or "__pycache__" in p
    or p.endswith((".pt", ".pth", ".ckpt", ".bin", ".npz", ".h5ad", ".egg-info"))
    or p.startswith("/home/Models")
    or p.startswith("/workspace/_external")
]
print("
".join(paths))
print("FORBIDDEN", forbidden)
raise SystemExit(1 if forbidden else 0)
PY
```

Commit/push:

```bash
git commit -m "Validate hTERT-RPE1 official transfer smoke"
GIT_SSH_COMMAND="ssh -i /root/.ssh/vc_demo_github_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push origin official-htert-rpe1-transfer-smoke
```

Final reply must include:
- branch
- commit
- whether hTERT-RPE1 reached K562 Phase-3
- stop reason
- generated proposals
- trained rollouts
- pruned proposals
- blocked/acquisition
- failed
- pending
- best root
- best trained rollout
- improvement over best root
- fallback count, must be 0
- backprop_nontrained count, must be 0
- recommendation on multi-cell-line paper-scale
