# Prompt Template: Generic Cell-Line Experiment

Use this format for future handoffs. Keep prompts variable-only; do not paste cookbook/runbook rules here.

```text
Work only on RunPod in /workspace/vc-demo. Do not read or run the local repo.

BASE_BRANCH: <base branch>
RUN_BRANCH: <new run branch>
CELL_LINE_ID: <cell line id>
RUN_TYPE: <loop_self_test | full_cellline_run>
TEST_LEVEL: <preflight | transfer_64x16 | transfer_150x40 | full_cellline_run>
RUN_DIR: <fresh experiments/... directory>
TARGET_VAL_MACRO_F1: <required for full_cellline_run, optional otherwise>

First read and follow the current repo docs:
1. CODEX_AGENT_COOKBOOK.md
2. docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md
3. docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md
4. ARTIFACT_ACQUISITION_RUNBOOK.md
5. OFFICIAL_K562_IMPLEMENTATION_LOOP.md only if CELL_LINE_ID=K562 or the task is explicitly K562-specific

Run the requested experiment from scratch in RUN_DIR, push RUN_BRANCH, and report:
- branch and commit hash
- run dir
- generated proposals / trained selected rollouts / pruned / skipped / blocked / failed
- best root val/test
- best generated child val/test
- objective status against TARGET_VAL_MACRO_F1
- acquisition/blocker summary
- forbidden staged check result
```
