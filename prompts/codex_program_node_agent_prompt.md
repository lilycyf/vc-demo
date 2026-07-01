# Prompt Template: Codex Program-Node Experiment Agent

Use this prompt when launching a Codex agent for a concrete task.

```text
You are working in /workspace/vc-demo on RunPod.

First run:

git pull --ff-only

Then read, in order:
1. E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md
2. F_PROGRAM_NODE_HARNESS_UPGRADE.md
3. CODEX_AGENT_OPERATING_RULES.md
4. <TASK_FILE>.md

Follow the task file exactly. You are both the experiment runner and the implementation agent. Use the harness files already in the repo instead of writing ad hoc search scripts.

If program_run produces needs_implementation nodes, read implementation_queue.json and the node's IMPLEMENTATION_REQUEST.md. Implement only the requested node-local model.py, run compile/smoke checks, then train it with python -m vc_demo.harness.train_pending.

Keep data, splits, and metric semantics unchanged. Do not commit data, nodes, checkpoints, pycache, egg-info, secrets, or tokens.

At the end, write the requested final_conclusion.md, commit only allowed files, and push to the task branch. Do not push to master.
```
