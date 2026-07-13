# Short Prompt: Generic Cell-Line Runs

## Full cell-line run

Copy this when the user asks to truly/fully run a cell line:

```text
Run official generic cell-line full run on RunPod `/workspace/vc-demo`.
Branch: generic-cellline-runner-fix
CELL_LINE_ID: <CELL_LINE_ID>
RUN_TYPE: full_cellline_run

Use repo instructions only:
- docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md
- docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md

Use the standard entrypoint:
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py --cell-line <CELL_LINE_ID> --run-type full_cellline_run --level full_cellline_run --execute

This is not a smoke test. Do not use transfer_64x16. Do not use 1 epoch. Before training, apply the artifact-constrained blueprint rule from the runbook: acquire public source-backed artifacts when possible; if an artifact is proven unavailable, exclude dependent blueprints from the main full run and report them separately. No fallback, no compact/proxy, no test-set tuning, and no forbidden files.

Push results to:
<cell_line_slug>-full-official-run

Final reply must include commit hash, generated/trained/pruned/blocked counts, best root val/test, best child val/test, whether best child beats root, artifact exclusions/blockers, fallback/proxy/backprop/backend anomaly counts, and forbidden staged check result.
```

## Loop self-test

Copy this only when the user asks to test the runner mechanics:

```text
Run generic cell-line loop self-test on RunPod `/workspace/vc-demo`.
Branch: generic-cellline-runner-fix
CELL_LINE_ID: <CELL_LINE_ID>
RUN_TYPE: loop_self_test
TEST_LEVEL: transfer_64x16

Use the standard entrypoint:
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py --cell-line <CELL_LINE_ID> --run-type loop_self_test --level transfer_64x16 --execute

This is a loop/runner validation only; do not use the result to judge model superiority.
```
