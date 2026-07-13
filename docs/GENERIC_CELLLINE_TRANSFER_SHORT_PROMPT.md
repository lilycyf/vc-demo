# Short Prompt: Generic Cell-Line Transfer Test

Copy this when handing off to an experiment Codex:

```text
Run generic cell-line transfer test on RunPod `/workspace/vc-demo`.
Branch: generic-cellline-runner-fix
CELL_LINE_ID: <CELL_LINE_ID>
TEST_LEVEL: transfer_64x16

Use repo instructions only:
- docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md
- docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md

Use the standard entrypoint:
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py --cell-line <CELL_LINE_ID> --level transfer_64x16 --execute

If pending implementation appears, follow the node-local contracts and the runbook. Do not fallback, do not use compact/proxy implementations, do not leak K562 files, and do not commit forbidden files.

Push results to:
generic-cellline-transfer-test-<cell_line_slug>

Final reply must include selected cell line, commit hash, trained/pending/failed/blocked counts, best root, best child, fallback/proxy/backprop/backend anomaly counts, and pass/block/fail decision.
```
