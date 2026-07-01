# RunPod Handoff

## Pod

- Pod ID: `7taingax3un14r`
- Pod name: `identical_coral_mongoose`
- GPU: NVIDIA L4, 24 GB VRAM
- Template: Runpod PyTorch 2.4.0 / CUDA 12.4 / Python 3.11
- Workspace: `/workspace`
- Repo: `/workspace/vc-demo`
- Network volume: `upper_yellow_bovid`, 20 GB, mounted at `/workspace`

The network volume persists after pod deletion, so delete it manually when the experiment is finished.

## Access

Use the RunPod console Connect tab for Jupyter or Web Terminal.

SSH direct command shown by RunPod:

```bash
ssh root@157.157.221.29 -p 43267 -i ~/.ssh/id_ed25519
```

Current caveat: the local SSH key was not accepted by this pod, so Jupyter/Web Terminal is the reliable access path unless RunPod SSH keys are updated.

## What is prepared

This repo was empty except for `.gitattributes`. I added a minimal VCHarness-style scaffold:

- synthetic one-cell-line perturbation dataset interface
- configurable perturbation MLP
- train/evaluate command that writes checkpoint, metrics, and node memory
- toy MCTS child-proposal driver
- two root configs
- agent prompt template
- smoke-test script

## Commands

```bash
cd /workspace/vc-demo
bash scripts/smoke.sh
```

After smoke test, inspect:

```bash
cat experiments/nodes/root_mlp/metrics.json
cat experiments/tree.json
ls experiments/proposals
```

## Next agent task

The next Codex window should first run the smoke test, then choose one of these branches:

A. Keep synthetic data and demonstrate the full harness loop cheaply.
B. Replace `SyntheticPerturbationDataset` with a real one-cell-line dataset loader and keep the same training/MCTS interface.

For the requested demo path, start with A.

## Smoke Test Result

Status: passed on CUDA/L4.

- `root_mlp`: best validation Macro-F1 = `0.3331`, test Macro-F1 = `0.3357`
- `root_regularized_mlp`: best validation Macro-F1 = `0.3334`, test Macro-F1 = `0.3350`
- MCTS proposal tree: `experiments/tree.json`
- Proposed children: `3` JSON configs under `experiments/proposals/`

Current git status:

```text
?? HANDOFF.md
?? README.md
?? agent_prompt_template.md
?? configs/
?? experiments/
?? pyproject.toml
?? requirements.txt
?? scripts/
?? src/
```

Note: scaffold files and smoke-test outputs are currently on the RunPod volume. They have not been pushed back to GitHub.
