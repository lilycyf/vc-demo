# Prompt Template: Codex Program-Node Experiment Agent

Use this prompt when launching a Codex agent for a concrete task.

```text
You are working in /workspace/vc-demo on RunPod.

First run:

git pull --ff-only

Then read, in order:
1. E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md
2. F_PROGRAM_NODE_HARNESS_UPGRADE.md
3. PAPER_LEVEL_SEARCH_SPACE_SPEC.md
4. PUBLIC_ARTIFACT_ALIGNMENT.md
5. CODEX_AGENT_OPERATING_RULES.md
6. <TASK_FILE>.md

Follow the task file exactly. You are both the experiment runner and the implementation agent. Use public paper-aligned behavior where specified; when a detail is missing but required for the loop, implement it as an explicit repo-specific completion and record it. Use the harness files already in the repo instead of writing ad hoc search scripts. Treat PAPER_LEVEL_SEARCH_SPACE_SPEC.md as the search-space contract: do not pre-implement all planned models, but do consider the planned biological-prior, foundation-embedding, graph, and multimodal-fusion blueprints when the search selects them. Also read TARGET_AWARE_ARTIFACT_MODEL_SPACE.md and PAPER_LEVEL_FRAMEWORK_UPGRADE_2.md when the task involves ESM2/AIDO/scFoundation/STRING artifacts; prefer target-aware artifact use over simply appending a foundation embedding to tabular features.

If program_run produces needs_implementation nodes, read implementation_queue.json and the node's IMPLEMENTATION_REQUEST.md. Implement only selected node-local model.py files, run compile/smoke checks, then train them with python -m vc_demo.harness.train_pending. Record any missing external artifact or fallback instead of faking AIDO/ESM2/scFoundation/STRING data.

Keep data, splits, and metric semantics unchanged. Do not commit data, nodes, checkpoints, pycache, egg-info, secrets, or tokens.

At the end, write the requested final_conclusion.md, commit only allowed files, and push to the task branch. Do not push to master.
```


Strict artifact rule: in formal testing, do not implement fallback models for missing AIDO/scFoundation/STRING/pathway/pretrained artifacts. If the registry says a required artifact is missing, stop and record `blocked_missing_artifact`. Use `--allow-missing-artifact-fallbacks` only when the user explicitly asks for a separate ablation.
