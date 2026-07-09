# Data And Artifacts

Large biological data should stay out of ordinary commits. Formal K562 runs expect data and artifacts on the RunPod volume, typically under:

```text
data/cell_lines/official_k562_cls/
data/artifacts/official_k562/
data/artifacts/string/
data/artifacts/pathways/
/home/Models/AIDO.Cell-100M
/home/Models/STRING_GNN
```

Use the registry audit to see what is present:

```bash
python -m vc_demo.harness.artifact_registry --cell-line K562
```

Known source-backed acquisition rules live in:

```text
configs/artifacts/k562_registry.json
configs/artifacts/acquisition_sources.json
ARTIFACT_ACQUISITION_RUNBOOK.md
ARTIFACT_ACQUISITION_AGENT_PROMPT.md
```

If a strict run creates `acquisition_queue.json`, run the artifact acquisition resolver and follow the generated `ACQUIRE_<artifact>.md` task. Do not create random or proxy artifacts and mark them as real.

The legacy `real_npz` loader still exists as an internal training substrate, but the current formal path is the official K562 TSV/H5AD contract built by `scripts/build_official_k562_task.py` and related official artifact scripts.
