# Artifact Acquisition Runbook

## Ownership And Trigger

Read CODEX_AGENT_COOKBOOK.md, RESEARCH_PROTOCOL.md and GENERIC_RESEARCH_RUNBOOK.md.
Availability is a feasibility gate after scientific selection, never a model-quality
bonus. Acquisition cannot change the task, expand spending or reopen confirmation.

When a selected candidate requires missing resources, the active Codex handles the
work now: inspect its required_artifacts contract, use existing source-backed tools,
search primary sources, download/build, validate and register. A task/queue file is
not completion, a terminal requires_external_codex state or proof of unavailability.

## Required Investigation

1. Identify the actual module type and required contents: graph, vocabulary, aligned
   embedding, pretrained encoder/checkpoint, code or derived representation. A graph
   or cached vector table cannot impersonate missing pretrained model weights.
2. Search the module's official project/model/data sources and appropriate public
   hosts. Do not prefer a provider brand regardless of the task. Record source,
   revision/license/access conditions, expected format and content checksums.
3. Check current files and provenance, not directory existence. Empty directories or
   repositories containing only model cards/.gitattributes are not usable artifacts.
4. If a real public encoder exists but aligned outputs do not, investigate a faithful
   encoder-output build: input normalization, supported vocabulary, dimensions, row/
   target order, training/query access and resource cost. Missing preprocessing or
   a resolver requires implementation/research, not an automatic scientific blocker.
5. Download/build within authorization. Preserve an auditable reproduction recipe
   and reusable manifest; weights/data/environments stay off GitHub.
6. Verify actual task alignment and authentic loading/forward use. Record original_public,
   derived or reconstructed_compatibility; never call an unverified reconstruction
   numerically identical to the original. Honor the proposal's allowed provenance.
7. Seal the content-backed resource and execute only after real validation. If a
   genuinely different module is proposed instead, name a new explicit hypothesis;
   do not keep the required foundation-model claim while silently omitting it.

## Existing Resolver Tools

The legacy cell-line helper remains available for its supported registry schema:

```bash
PYTHONPATH=src python -m vc_demo.harness.artifact_acquisition \
  --queue <queue.json> --registry <explicit active registry.json> \
  --sources configs/artifacts/acquisition_sources.json \
  --cell-line <explicit source-backed cell-line/task scope supported by registry> \
  --output-dir <run_dir>/artifact_acquisition --execute-known
```

Its historical default scope is not a generic task inference. Never omit the active
scope/registry or silently apply a classification/cell-line resolver to another task.
Use a faithful task resolver or current Codex research/build tools when that schema
does not apply. Read generated ACQUIRE_<artifact>.md and act in this session.

In research_v2, required roles remain on the selected candidate until handled.
Seal verifies actual file/directory content identity, required contents and module
type, source/status and alignment. Providers must load/consume the declared resource;
reported role names alone do not prove authenticity or usefulness. Native loader,
vocabulary/order and source tests are task-provider obligations.

## Failure, Local Skip And Continuation

After actual attempts, source not verifiable, unpublished/incomplete/non-equivalent
files, access/license restrictions, unresolved order/shape/leakage risk or approved
resource limits may make this candidate infeasible. Record exactly which boundary
applies, sources/actions checked, evidence files/checksums and any human action needed.

Use the shared skip action with reason and concrete attempts, then continue other
feasible queued candidates. Missing Python packages, helpers, disk preparation,
encoder wrappers or an uncalled resolver are repair/acquisition work, not proof of
an unavailable primary artifact. Do not fabricate resources to keep counters zero.

Historical classification wrappers may require verified_blockers.json receipts to
continue. Those are historical execution details, not an instruction to resume a
closed run or to train every proposal. New v2 work follows the shared session state.

## Forbidden Claims

- Random embeddings or fabricated edges labeled as a real biological artifact.
- A small model/proxy presented as a named pretrained model or authentic checkpoint.
- Marking present from an empty path/directory or a downloadable README only.
- Calling acquired/consumed resources useful without applicable matched controls.
- Treating unavailable artifacts as lower scientific merit before research selection.
- Committing private keys, access tokens, model weights, raw arrays/data or environments.

Task-specific artifact priorities and examples belong in task documentation, not
this universal acquisition policy. Missing source-backed resources block their own
candidate, not unrelated hypotheses or the whole framework by default.
