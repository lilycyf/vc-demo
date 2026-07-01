# Codex Agent Search Runbook

This runbook is a generic protocol for running a VCHarness-style model search with Codex acting as the proposal agent. It intentionally does not define the scientific topic. The topic, dataset, metric, experiment name, and command should be supplied in the user task that points Codex to this document.

## Purpose

Use a repeatable search loop to improve a model/pipeline for a user-specified research question:

1. Train one or more root candidate pipelines.
2. Use MCTS or another configured search policy to select which trained parent node to expand.
3. Use Codex-agent judgment to propose the next child node within the allowed edit boundary.
4. Train/evaluate the child node.
5. Record the proposal, result, and search-tree state.
6. Stop by the task-defined budget or stopping rule.
7. Produce a final conclusion tied to the user's research question.

## Required Inputs From The User Task

Before running, identify these fields from the user's task. If any are missing and cannot be inferred from the repo, ask before starting the formal run.

- Research question: what scientific or modeling question is being tested.
- Dataset and split: where the data lives and which train/validation/test split must be preserved.
- Target metric: the metric used for search reward and final comparison.
- Baseline/root configs: which initial candidates must be trained first.
- Experiment name and run directory.
- Search budget: node budget, epoch budget, time/cost limit if any.
- Stop rule: no-improvement threshold, max nodes, or other user-defined stop condition.
- Allowed edits: which files Codex may change before/during the experiment.
- Forbidden edits: data, splits, metric semantics, previous results, or any other protected surface.
- Final deliverables: summary files, conclusion file, commit/push expectations.

## Role Of The Codex Agent

Codex has two roles:

- Experiment runner: execute the configured harness command and monitor outputs.
- Proposal agent: when allowed by the user task, improve or implement the proposal policy that generates child nodes.

The search policy should choose which parent to expand. The proposal agent should decide how to turn that parent into a valid child candidate. Keep those responsibilities separate unless the user explicitly asks to redesign the search algorithm.

## Node Definition

A node is one complete executable candidate pipeline. Depending on the project, this may include:

- data representation or feature source
- model family or architecture
- fusion/head design
- training objective or loss variant
- optimizer and regularization settings
- training schedule or budget
- any task-specific preprocessing that is allowed by the user

A child node must be valid, trainable, and comparable to its parent under the same target metric. Do not create changes that make the result incomparable unless the user explicitly asks for exploratory, non-comparable runs.

## Allowed And Forbidden Changes

Follow the user's task-specific allowed/forbidden lists. If the lists are absent, use this conservative default:

Allowed by default:

- proposal policy code
- small model definitions that remain compatible with existing configs
- experiment configs
- report/conclusion documents
- logging improvements

Forbidden by default:

- raw data
- processed data and split definitions
- metric semantics
- previous committed results
- large binary outputs
- checkpoint files
- ignored node workspaces unless explicitly requested

## Required Records Per Node

For every attempted child node, preserve or generate records containing:

- parent node id
- child node id
- parent-selection score or rationale
- proposal strategy or change category
- hypothesis
- concrete config/code changes
- validation metric
- test metric, if part of the task protocol
- comparison to parent
- comparison to best root/baseline
- failure reason and traceback summary if failed

Prefer machine-readable proposal files plus a human-readable summary.

## Running The Experiment

Use the command provided in the user task. If the repo provides a harness CLI, prefer it over ad hoc scripts.

Before the formal run:

```bash
git pull --ff-only
git status --short --ignored
```

If the task permits proposal-agent edits, make those edits first, then run a small smoke test when feasible. The smoke test should verify that the loop can train roots, expand at least one child, and write tree/summary/proposal files. Do not treat smoke-test metrics as scientific results.

During the formal run:

- keep the train/validation/test split fixed
- use the target metric as the search reward
- do not stop only because early children underperform
- record failures instead of silently dropping them
- preserve enough metadata for another Codex/user to inspect the search path

## Stopping

Stop only when one of the user-task stopping conditions is met, such as:

- maximum node budget reached
- no improvement for the configured number of nodes
- time/cost/GPU budget reached
- repeated infrastructure failure blocks meaningful progress
- explicit user stop instruction

If the harness stops automatically, report its exact stop reason.

## Final Conclusion

Create the final deliverable requested by the user task. If no exact format is supplied, write a markdown conclusion containing:

1. Research question and setup
   - command used
   - dataset/split
   - target metric
   - budget and stop reason

2. Best result
   - best baseline/root result
   - best overall node result
   - improvement over best baseline/root
   - path from root to best node

3. Search behavior
   - nodes trained
   - nodes failed
   - branches explored
   - proposal categories that helped or failed

4. Interpretation
   - what appears to matter most for the research question
   - whether evidence supports the user-specified hypothesis
   - limits of the run

5. Reproducibility and artifacts
   - summary path
   - tree path
   - proposal path
   - any uncommitted/ignored artifact locations

## Git Hygiene

Before committing:

```bash
git status --short --ignored
```

Commit only source code, configs, small JSON/markdown summaries, proposal metadata, and final conclusions requested by the task.

Do not commit:

- raw or processed datasets unless the repo explicitly tracks them
- training node directories containing checkpoints or bulky artifacts
- checkpoint files
- pycache
- package build artifacts
- secrets or tokens

Commit message should describe the actual task performed, for example:

```bash
git add <allowed files>
git commit -m "Run <experiment-name> agent search"
git push origin <branch>
```

## Task Instruction Template

Use this template when assigning a concrete experiment to Codex:

```text
请连接实验机器，在 <repo_path> 中执行 git pull --ff-only，然后完整阅读 <runbook_path>。

本次研究课题是：<research_question>。

数据与 split：<dataset_and_split>。
目标指标：<metric>，搜索 reward 使用 <reward_metric>。
baseline/root configs：<root_configs>。
实验名与目录：<experiment_name>, <run_dir>。
预算与停止条件：<budget_and_stop_rule>。

你在本次任务中既是实验 runner，也是 proposal agent。你可以修改：<allowed_edits>。你不可以修改：<forbidden_edits>。

请先确认当前代码和数据是否满足任务要求；如需改 proposal policy，请在允许范围内修改并做小 smoke test；然后运行正式实验。结束后生成 <final_deliverable>，总结 best root、best overall、提升幅度、最佳路径、失败节点、搜索行为和结论。最后只提交允许提交的文件并 push。
```
