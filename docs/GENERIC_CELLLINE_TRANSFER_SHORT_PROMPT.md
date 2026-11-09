# Short Research Prompt Format

```text
Work only on RunPod in /workspace/vc-demo. Do not read or run the local repo.

BASE_BRANCH: <current framework branch>
RUN_BRANCH: <same branch, or an explicitly requested isolated run branch>
TASK_ID: <requested task/cell line>
RUN_TYPE: <framework_cpu_validation | formal_research>
RUN_DIR: <fresh directory for formal research; temporary fixtures for CPU tests>
TASK_SOURCE: <task document/data contract>
RESOURCE_LIMIT: <explicit user authorization, deadline and cost limit>
OPTIONAL_SCIENTIFIC_TARGET: <only if required; register before confirmation>

Read CODEX_AGENT_COOKBOOK.md, docs/RESEARCH_PROTOCOL.md,
docs/GENERIC_RESEARCH_RUNBOOK.md and the applicable task/acquisition docs.
Use the shared research_v2 entrypoint, implement missing task-provider work in this
Codex session, complete the requested authorized scope, and report layered verdicts.
Push only approved source/contracts/tests/small results and give branch/commit/report.
```

Do not paste universal rules into each prompt, preselect an example second task,
require a demo-specific score/epoch count, or authorize cloud spending implicitly.
CPU validation is not permission to start a scientific run. Legacy 64x16/150x40/full
classification profiles do not define universal research adequacy.
