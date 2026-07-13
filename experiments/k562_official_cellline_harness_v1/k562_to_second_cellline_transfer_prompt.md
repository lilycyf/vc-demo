You only operate through RunPod SSH in `/workspace/vc-demo`. Do not read or run a local repo.

Goal:
Instantiate the generic Official Cell-Line Harness v1 / Phase-3 template on a cell line specified by the user at run time. The target is not paper-scale 600+ proposals. The target is to reach Phase-3 harness level: source-backed task contract, artifact audit, root baselines, proposal-pool MCTS, automatic implementation loop, strict acquisition/block behavior, and a final cross-cell-line report.

Important anti-leakage rule:
This prompt is a generic cell-line harness template. It must not assume, hard-code, prefer, or rank any particular cell line. The experiment Codex must fill in `CELL_LINE_ID` only from the user task that launches the run. K562 is only prior validation evidence for this template, not a runtime template parameter.

Required task parameters supplied by the user:

```text
CELL_LINE_ID=<cell line id provided by user>
TASK_SOURCE=<official/public source path or URL provided by user, or DISCOVER_FROM_PUBLIC_VCHARNESS>
SPLIT_SOURCE=<split source provided by user, or DISCOVER_FROM_TASK_SOURCE>
TARGET_GENE_ORDER_SOURCE=<target gene order source provided by user, or DISCOVER_FROM_TASK_SOURCE>
```

Derived names:

```text
CELL_LINE_SLUG=<lowercase safe slug from CELL_LINE_ID>
TRANSFER_BRANCH=official-${CELL_LINE_SLUG}-transfer-smoke
TRANSFER_RUN_DIR=experiments/official_${CELL_LINE_SLUG}_transfer
ROOT_CONFIG_DIR=configs/official_${CELL_LINE_SLUG}_roots
ARTIFACT_REGISTRY=configs/artifacts/${CELL_LINE_SLUG}_registry.json
SMALL_RUN=experiments/official_${CELL_LINE_SLUG}_auto_impl_64x16
MEDIUM_RUN=experiments/official_${CELL_LINE_SLUG}_auto_impl_150
```

Base branch:
`k562-official-cellline-harness-v1` unless the user explicitly provides another base branch. This branch contains the generic template plus K562 validation evidence.

Core rules:
- Work only on RunPod `/workspace/vc-demo`.
- Do not modify prior K562 validation data, split, labels, metrics, target gene order, or artifact provenance.
- Do not use fallback models, fabricated artifacts, compact/native proxy implementations, or K562 proxy-era scores as formal baselines.
- Do not assume the cell line in this template. Use only `CELL_LINE_ID` from the launch task.
- Missing artifacts must go through acquisition first; write an acquisition queue, run the acquisition resolver/tool, and generate `ACQUIRE_<artifact>.md` before declaring a strict blocker. If source/order/shape/vocabulary/provenance cannot be verified after that pass, block.
- Do not reuse K562-specific embeddings or any other cell-line-specific artifact for the requested cell line.
- Generated native children must not inherit `external_static_node`.
- `external_static_node` is allowed only for explicit public static wrappers/benchmarks.
- Only trained nodes can backpropagate reward.
- Do not commit `data/`, `nodes/`, checkpoints, weights, `.h5ad`, `.npz`, `/home/Models`, `/workspace/_external`, `__pycache__`, or egg-info.

Step 1: sync and create branch.

```bash
cd /workspace/vc-demo
GIT_SSH_COMMAND="ssh -i /root/.ssh/vc_demo_github_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git fetch origin
git checkout -B ${TRANSFER_BRANCH} origin/k562-official-cellline-harness-v1
git rev-parse --short HEAD
```

Step 2: read K562 validation handoff, treating recorded K562 run metrics as historical proxy-era wiring evidence only.

```bash
cat experiments/k562_official_cellline_harness_v1/k562_harness_v1_report.md
cat experiments/k562_official_cellline_harness_v1/k562_reusable_checklist.md
cat experiments/k562_official_cellline_harness_v1/k562_harness_v1_audit_summary.json
```

Step 3: discover and audit the public scaffold for `CELL_LINE_ID`.

Do not assume the public scaffold path. Discover it from `/workspace/_external/VCHarness` by matching `CELL_LINE_ID` to available classification tracks. If no matching public scaffold exists, record that and continue only if the task source can still establish an official task contract.

Read only discovered paths such as:

```text
/workspace/_external/VCHarness/${PUBLIC_TRACK}/mcts_data.json
/workspace/_external/VCHarness/${PUBLIC_TRACK}/memory
/workspace/_external/VCHarness/${PUBLIC_TRACK}/static
```

Write:

```text
${TRANSFER_RUN_DIR}/public_scaffold_audit.json
${TRANSFER_RUN_DIR}/public_scaffold_audit.md
```

Record static count, memory count, public best node id/path, public best score, top 10 public nodes, and comparison to the K562 validation scaffold. The K562 public scaffold reference may be used only as validation sanity evidence: static 309, memory 153, public best 0.51277. Do not use K562 proxy-era native/root metrics as formal benchmark targets.

Step 4: establish the requested cell-line task contract.

Use `TASK_SOURCE`, `SPLIT_SOURCE`, and `TARGET_GENE_ORDER_SOURCE` for `CELL_LINE_ID`. If they are set to discovery modes, discover only from source-backed official/public artifacts and record the exact source.

If `h5py`, `anndata`, or `scanpy` are missing, install the official requirements in RunPod:

```bash
python -m pip install -r requirements-official-k562.txt
```

Build or reuse a generalized official cell-line task builder. Preserve K562 validation behavior exactly. Generate:

```text
data/cell_lines/official_${CELL_LINE_SLUG}_cls/train.tsv
data/cell_lines/official_${CELL_LINE_SLUG}_cls/val.tsv
data/cell_lines/official_${CELL_LINE_SLUG}_cls/test.tsv
data/cell_lines/official_${CELL_LINE_SLUG}_cls/target_genes.tsv
data/cell_lines/official_${CELL_LINE_SLUG}_cls/manifest.json
```

Requirements:
- 3-class DEG labels, unless the source-backed task contract proves a different label space and the run is explicitly blocked for mismatch.
- Fixed train/val/test split.
- Target gene order aligned to the official/public scaffold.
- Macro-F1 reward on validation; test Macro-F1 report-only.
- Record row counts and target gene count from source, not from assumptions.

Write:

```text
${TRANSFER_RUN_DIR}/task_contract_audit.json
${TRANSFER_RUN_DIR}/task_contract_audit.md
```

If the requested `CELL_LINE_ID` cannot establish a source-backed task contract, block and report the reason. Do not silently switch to another cell line.

Step 5: build artifact registry and root configs for `CELL_LINE_ID`.

Add minimal generalized cell-line configs/helpers while keeping K562 validation behavior unchanged.

Separate artifacts as:
- reusable: official source parser, reusable public model directories, STRING source graph if tensor contract is cell-line independent, pathway source definitions;
- cell-line-specific: DEG split, AIDO embedding h5ad, GNN embedding h5ad, scFoundation embeddings, public static wrapper path, aligned target-gene artifacts.

For missing cell-line-specific artifacts:
- inspect `configs/artifacts/acquisition_sources.json`;
- inspect repo acquisition/build scripts;
- search public/official sources only when source provenance can be recorded;
- acquire/build only when source, revision, row order, shape, vocabulary, and provenance are verifiable;
- otherwise write acquisition/blocker.

Write:

```text
${ARTIFACT_REGISTRY}
${ROOT_CONFIG_DIR}/*.json
${TRANSFER_RUN_DIR}/artifact_registry_audit.json
```

Step 6: run root baselines if artifacts are present/acquired.

Expected root families, subject to source-backed artifact availability:
- cell-line-specific AIDO embedding MLP
- cell-line-specific AIDO+GNN embedding MLP
- public static wrapper/benchmark for `CELL_LINE_ID`

For K562 self-instantiation loop tests, use `configs/official_k562_loop_roots/*.json` for the 64/16 MCTS loop check. This excludes the public static wrapper so a missing `/home/Models/STRING_GNN` checkpoint cannot mask proposal-pool, prune, train-selected-only, and backprop-trained-only behavior. Public wrapper benchmark remains a separate strict acquisition/benchmark path.

Write:

```text
${TRANSFER_RUN_DIR}/root_baseline_summary.md
```

If a root artifact is missing, acquire first. If still unverifiable, block. Do not fallback.

Step 7: run automatic implementation loop.

If the repo has only a K562-specific runner, minimally generalize it to `scripts/run_official_cellline_harness_search.py` with a `--cell-line` argument. K562 validation behavior must remain unchanged.

Run 64 proposals / 16 trained rollouts:

```bash
PYTHONPATH=src python scripts/run_official_cellline_harness_search.py \
  --cell-line ${CELL_LINE_ID} \
  --run-dir ${SMALL_RUN} \
  --experiment official_${CELL_LINE_SLUG}_auto_impl_64x16 \
  --root-configs ${ROOT_CONFIG_DIR}/*.json \
  --budget-proposals 64 \
  --budget-trained-nodes 16 \
  --candidate-pool-size 4 \
  --max-epochs 1 \
  --max-children 8 \
  --stop-no-improve 12 \
  --selection-policy uct \
  --official-blueprint-space \
  --allow-planned-blueprints \
  --strict-artifacts \
  --enable-implementation-loop \
  --implementation-repair-attempts 3 \
  --reset
```

If `CELL_LINE_ID=K562` and the goal is generic self-instantiation, first run the same command with `--root-configs configs/official_k562_loop_roots/*.json`. A run blocked only by the public wrapper's STRING_GNN artifact is an acquisition result, not a MCTS-loop pass.

If clean, run 150 proposals / 40 trained rollouts:

```bash
PYTHONPATH=src python scripts/run_official_cellline_harness_search.py \
  --cell-line ${CELL_LINE_ID} \
  --run-dir ${MEDIUM_RUN} \
  --experiment official_${CELL_LINE_SLUG}_auto_impl_150 \
  --root-configs ${ROOT_CONFIG_DIR}/*.json \
  --budget-proposals 150 \
  --budget-trained-nodes 40 \
  --candidate-pool-size 4 \
  --max-epochs 1 \
  --max-children 8 \
  --stop-no-improve 30 \
  --selection-policy uct \
  --official-blueprint-space \
  --allow-planned-blueprints \
  --strict-artifacts \
  --enable-implementation-loop \
  --implementation-repair-attempts 3 \
  --reset
```

Step 8: handle blockers.

If an artifact is missing:
- add it to the run acquisition queue with artifact id, node, strategy, expected path, source hint, and cell-line specificity;
- run `PYTHONPATH=src python -m vc_demo.harness.artifact_acquisition --queue <queue> --registry <registry> --sources configs/artifacts/acquisition_sources.json --cell-line <CELL_LINE_ID> --output-dir <run>/artifact_acquisition --execute-known`;
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

```text
${TRANSFER_RUN_DIR}/final_report.md
experiments/cross_cellline_stage_report.md
```

The final report must answer:
- Did `CELL_LINE_ID` reach Phase-3 / Harness v1 level?
- If not, which artifact or task contract blocked it?
- K562 validation completion level.
- `CELL_LINE_ID` public scaffold vs K562 validation scaffold.
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
- `CELL_LINE_ID` configs/scripts;
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
print("\n".join(paths))
print("FORBIDDEN", forbidden)
raise SystemExit(1 if forbidden else 0)
PY
```

Commit/push:

```bash
git commit -m "Validate official second-cell-line transfer smoke"
GIT_SSH_COMMAND="ssh -i /root/.ssh/vc_demo_github_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git push origin ${TRANSFER_BRANCH}
```

Final reply must include:
- branch
- commit
- `CELL_LINE_ID`
- whether `CELL_LINE_ID` reached Phase-3
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
