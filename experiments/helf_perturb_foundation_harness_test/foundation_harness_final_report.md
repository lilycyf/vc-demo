# HELF Perturbation Foundation Harness Test

## Run Summary

- Branch: `helf-perturb-foundation-harness-test`
- Run dir: `experiments/helf_perturb_foundation_harness_test`
- Task: `HELF_PERTURB_DEG`
- Stop reason: `trained-node budget exhausted (24/24)`
- Target validation Macro-F1: `0.36`
- Objective status: `passed` because best generated child val Macro-F1 `0.369406` >= `0.36`.

## Counts

- generated_proposals: `96`
- trained_selected_rollouts: `24`
- pruned_not_selected: `26`
- skipped: `0`
- blocked: `46`
- requires_artifact_acquisition: `46`
- failed: `0`
- fallback_count: `0`
- proxy_count: `0`
- backprop_nontrained_count: `0`
- backprop_nontrained_audit: `0`

## Best Lightweight Root

- Config: `configs/helf_perturb_roots/root_residual_mlp.json`
- Val Macro-F1: `0.349249`
- Test Macro-F1: `0.350482`

## Best Generated Child

- Node: `helf_perturb_root_residual_mlp_p95_focal_loss`
- Strategy: `focal_loss`
- Proposal type: `lightweight_executable_transform`
- Val Macro-F1: `0.369406`
- Test Macro-F1: `0.364078`
- Delta vs best root val: `0.020157`
- Delta vs target val: `0.009406`

## Foundation Artifact Acquisition / Blockers

- `scgpt_whole_human_checkpoint`: `46` selected proposal(s) blocked pending source-backed acquisition/build.

## Search Semantics Audit

- Proposal types: `{'root': 4, 'foundation_artifact_blueprint': 48, 'lightweight_executable_transform': 48}`
- Node statuses: `{'trained': 28, 'requires_artifact_acquisition': 46, 'pruned_not_selected': 26}`
- Foundation proposals were allowed into the candidate pool with priority.
- Missing foundation artifacts were not faked: selected artifact-dependent proposals were marked `requires_artifact_acquisition` and written to `acquisition_queue.json`.
- Only selected lightweight executable rollouts were trained.
- Pruned proposals were not trained.
- Only trained nodes emitted `trained_and_backpropagated` trace events.
- Fallback/proxy count remained zero.

## Notes

- The source h5ad-derived HELF task dataset already existed on RunPod, so no data regeneration was required.
- The Blackwell GPU is incompatible with the installed PyTorch CUDA build, so the documented HELF CPU path (`VC_DEMO_FORCE_CPU=1`) was used.
- No data, nodes, checkpoints, weights, h5ad, npz, pycache, or egg-info files should be committed.

## Artifact Acquisition Report

See `artifact_acquisition_report.md` for the source-backed scGPT acquisition/blocker rationale.
