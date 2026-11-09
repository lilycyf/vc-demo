# Generic Research Runbook v2

## Scope

Use this runbook for new regression, classification, lineage or other registered
tasks. Task-specific parsing, group construction, model code and scientific meaning
remain providers. Read CODEX_AGENT_COOKBOOK.md, RESEARCH_PROTOCOL.md and the relevant
task/source and artifact documentation. Do not inherit an example task or model menu.

The active Codex performs the research work using the shared CLI. A returned
next_action is a work instruction, not permission to end a full run after one node.
No internal Codex API is needed or permitted. This runbook does not itself authorize
cloud spend or a new scientific experiment.

## Task Provider Guides

Task-specific adapters do not change this loop or become an implicit default.
For the T47D source/split, portable model interface and engineering-only acceptance,
read `docs/T47D_RESEARCH_V2_RUNBOOK.md`. Its preparation command does not initialize
a Session or authorize a scientific run; unvalidated legacy modules remain explicit
implementation/acceptance work rather than being certified by registration alone.

## Prepare And Register

1. Confirm repository, branch, fresh run directory, requested scope and resource
   authorization. Preserve existing work and watchdogs; do not create a branch unless
   needed/requested. CPU mechanism tests are not a scientific run.
2. Inspect primary sources and independent sample counts. Define TaskSpec and exact
   strong baselines; retain full preprocessing/scaling/training recipes.
3. Implement or adapt the provider and its negative tests. A missing adapter is
   implementation work, not justification for another task, proxy or synthetic data.
4. Produce development row/group/label/seed/fold contracts and content-addressed
   input roles. Keep confirmation data out of search requests and validate actual
   provider isolation. Register custom metrics before model selection, if needed.
5. Declare coverage/optimization/confirmation budgets and actual training policies,
   practical-effect/stopping rules and cost coefficients. No universal node/epoch
   minimum, mandatory foundation family or obligatory positive result.
6. Arm independent hard resource protection. Session deadline checks alone cannot
   interrupt an arbitrary provider call or stop cloud billing.

```bash
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" \
  init --spec "$TASK_SPEC"
```

Task/provider contracts and exact JSON fields are defined once in RESEARCH_PROTOCOL.md.
Use its schema rather than copying historical task-specific flags.

## Operate The Actual Shared Loop

```bash
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" context
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" propose --file "$PROPOSALS"
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" select
```

Read the immutable snapshot, actual OOF predictions/diagnostics and baseline recipes.
Develop multiple falsifiable proposals conditioned on that evidence. Manifests are
inventories, not ceilings. A justified UCT-parent override is allowed; label actual
policy semantics honestly. Existing queued hypotheses can receive logged estimate
updates using `rerank --file <{evidence_id,updates}>` before global selection.

For the selected node, immediately investigate/acquire real artifacts and implement
the candidate. Run model/provider-specific compile and native forward/backward smoke;
smoke never supplies a scientific reward. Preserve agent-written model code. If the
implementation improves on the proposed blueprint, declare its actual design and why.

```bash
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" \
  seal --node "$NODE" --file "$ACTUAL_IMPLEMENTATION"
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" execute --node "$NODE"
```

The engine verifies contents, OOF contracts, actual receipt/checkpoints and metric
identity before credit. Duplicate semantic measurements reuse evidence; deliberate
replicates must be explicit and are not new architectures or independent samples.

After success, inspect feedback and diagnostics, update queued estimates and submit
new proposals before selecting again. Coverage has separate state/credit; it does
not prevent later optimization from the strongest benchmark or a useful covered model.

On failure, act in this Codex session. Repair/reseal before any committed result;
when an existing scientific receipt/recipe would change, use a new candidate identity.
If genuinely infeasible after actual attempts:

```bash
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" \
  skip --node "$NODE" --file "$REASON_AND_ATTEMPTS"
```

Continue other feasible queued hypotheses. No fallback, no requires_external_codex
terminal state, no resolver-missing excuse. Respect resource limits and true source/
access/validation constraints. The same shared loop handles them across task types.

If the registered policy permits true feasible-space exhaustion, `exhaustion --file`
records reason/attempts. Retained queued candidates still run; no unhandled selected
candidate is silently parked. Report incomplete scope explicitly at a resource stop.

## Freeze, Confirm And Deliver

Separate best observed candidate, confirmation finalist and supported replacement.
No convincing increment may correctly retain the strongest baseline. Do not force
every child to retain a dense branch, and do not tune on confirmation to manufacture gain.
Record predeclared control outcomes with `control --file <control.json>` using actual
trained evidence. An unused component is N/A, not a positive attribution result.

```bash
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" freeze --nodes <finalists>
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" confirm --node <finalist>
PYTHONPATH=src python scripts/run_research_harness.py --run-dir "$RUN_DIR" report
```

Only previously fitted checkpoints/calibrators may be loaded. Confirmation closes
selection. Existing exposed groups are not fresh blind evidence after restart/versioning.

When the task includes challenges or sensitivity analyses, register their actual
providers, data/exposure scopes, target finalists and separate model/calibration fit
budgets before freezing. Initial TaskSpec registration or `plan-analysis` from the
current development evidence is allowed. Do not add questions after viewing outcomes
and label them predeclared. No task-specific analysis family belongs in the shared loop.

After freeze, follow `next_action`: finish frozen confirmation, then each required
registered analysis using `analyze --node <finalist> --analysis <id>`. The optional
analysis protocol in RESEARCH_PROTOCOL.md supports explicitly budgeted refits for
LOCO/temporal/matched-control work; main confirmation remains predict-only. Analysis
outputs never feed ranking or trigger new candidates. Resume reads durable receipts
and verifies actual contents, rather than rerunning completed work. Report missing
analyses separately from primary-search completion; do not stop at a single receipt
when registered scope remains. This engineering work itself grants no experiment budget.

Deliver layered execution/protocol/capability/artifact/attribution/scientific/transfer
verdicts. Include phase counts, unique semantic candidates, replicates, actual policies,
paired uncertainty, applicable controls, attempts/costs, exposure and limitations.
Unit tests cannot establish framework benefit; use equal-resource policy comparisons
and tasks not used to develop the framework before claiming general improvement.

Commit only approved source, contracts, tests, small results/reports; never datasets,
fitted weights, node output arrays, environments, keys or tokens. Validate staged paths
and preserve historical results. Do not launch another experiment unless requested.
