# Codex Agent Operating Rules

This file is intentionally a thin pointer. The canonical rules are now split by purpose:

1. `CODEX_AGENT_COOKBOOK.md` for agent permissions, guardrails, git hygiene, artifact acquisition, and realtime implementation semantics.
2. `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` for generic cell-line transfer and full-run execution.
3. `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md` for acceptance checks.
4. `OFFICIAL_K562_IMPLEMENTATION_LOOP.md` for K562-specific implementation-loop details.
5. `ARTIFACT_ACQUISITION_RUNBOOK.md` for source-backed artifact acquisition.

Do not copy older instructions from chat history or experiment outputs. If these files appear to conflict, prefer the more specific current runbook and update the stale file before running.

## Non-Negotiable Runtime Semantics

- The active Codex window is both experiment runner and implementation agent.
- Do not add internal Codex/OpenAI API calls to the repo.
- Selected implementation nodes must be handled during the current run.
- If a real artifact-backed implementation cannot be produced safely, mark the node `implementation_skipped`, clear it from `implementation_queue.json`, do not train, do not backpropagate, and continue global search.
- Missing artifacts go through acquisition first; only documented source/provenance/alignment failure becomes a blocker.
- No fallback, compact/proxy model, data/split/metric change, test-set tuning, or forbidden file commit in formal runs.
