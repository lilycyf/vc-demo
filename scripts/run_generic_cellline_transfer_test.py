from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@dataclass(frozen=True)
class TransferLevel:
    budget_proposals: int
    budget_trained_nodes: int
    candidate_pool_size: int
    max_children: int
    stop_no_improve: int
    run_type: str
    default_max_epochs: int
    description: str
    artifact_constrained_required: bool = False


LEVELS: dict[str, TransferLevel] = {
    "preflight": TransferLevel(8, 2, 2, 4, 4, "loop_self_test", 1, "minimal wiring smoke"),
    "transfer_64x16": TransferLevel(64, 16, 4, 8, 12, "loop_self_test", 1, "generic transfer loop test; not a model-quality run"),
    "transfer_150x40": TransferLevel(150, 40, 4, 8, 30, "loop_self_test", 1, "medium transfer pressure test; still not a full model-quality run"),
    "full_cellline_run": TransferLevel(300, 100, 6, 10, 60, "full_cellline_run", 8, "formal root-beating full cell-line run with model-quality budget", True),
}


def slugify(cell_line: str) -> str:
    slug = cell_line.strip().lower().replace("+", "plus")
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    return slug or "cell_line"


def default_root_configs(cell_line: str, slug: str) -> list[str]:
    normalized = cell_line.lower().replace("_", "-")
    if normalized in {"k562", "k-562"}:
        loop_dir = Path("configs/official_k562_loop_roots")
        if loop_dir.exists():
            roots = sorted(str(p) for p in loop_dir.glob("*.json"))
            if roots:
                return roots
    root_dir = Path(f"configs/official_{slug}_roots")
    return sorted(str(p) for p in root_dir.glob("*.json"))


def resolve_level_and_epochs(args: argparse.Namespace) -> tuple[str, TransferLevel, int]:
    level_name = args.level
    if level_name is None:
        level_name = "full_cellline_run" if args.run_type == "full_cellline_run" else "transfer_64x16"
    level = LEVELS[level_name]
    if args.run_type == "full_cellline_run" and level.run_type != "full_cellline_run":
        raise SystemExit(
            "RUN_TYPE=full_cellline_run must use --level full_cellline_run. "
            "transfer_64x16/transfer_150x40 are loop/self-test levels."
        )
    if args.run_type == "loop_self_test" and level.run_type == "full_cellline_run":
        raise SystemExit("--level full_cellline_run requires --run-type full_cellline_run.")
    max_epochs = args.max_epochs if args.max_epochs is not None else level.default_max_epochs
    if level.run_type == "full_cellline_run" and max_epochs < 8:
        raise SystemExit("full_cellline_run requires --max-epochs >= 8; 1-epoch smoke budgets are forbidden.")
    if level.run_type == "full_cellline_run" and args.target_val_macro_f1 is None:
        raise SystemExit("full_cellline_run requires --target-val-macro-f1; define the minimum acceptable validation Macro-F1.")
    return level_name, level, max_epochs


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _queue_len(run_dir: Path, name: str) -> int:
    payload = _read_json(run_dir / name)
    items = payload.get("items", [])
    return len(items) if isinstance(items, list) else 0


def _tree_nodes(run_dir: Path) -> dict[str, dict[str, object]]:
    tree = _read_json(run_dir / "tree.json")
    raw = tree.get("nodes", {})
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items() if isinstance(v, dict)}
    return {}


def _best_generated_child_val(run_dir: Path) -> float | None:
    vals: list[float] = []
    for node in _tree_nodes(run_dir).values():
        if node.get("parent") and node.get("status") == "trained" and node.get("best_val_macro_f1") is not None:
            vals.append(float(node["best_val_macro_f1"]))
    return max(vals) if vals else None


def _best_root_val(run_dir: Path) -> float | None:
    vals: list[float] = []
    for node in _tree_nodes(run_dir).values():
        if not node.get("parent") and node.get("status") == "trained" and node.get("best_val_macro_f1") is not None:
            vals.append(float(node["best_val_macro_f1"]))
    return max(vals) if vals else None


def _count_status(run_dir: Path, status: str) -> int:
    return sum(1 for node in _tree_nodes(run_dir).values() if node.get("status") == status)


def full_run_continue_reason(run_dir: Path, target_val_macro_f1: float | None, trained_budget: int) -> tuple[bool, str]:
    manifest = _read_json(run_dir / "run_manifest.json")
    search = manifest.get("search", {})
    stop_reason = str(search.get("stop_reason", "")) if isinstance(search, dict) else ""
    implementation_items = _queue_len(run_dir, "implementation_queue.json")
    acquisition_items = _queue_len(run_dir, "acquisition_queue.json")
    if implementation_items:
        return False, f"implementation queue requires realtime Codex action ({implementation_items})"
    if acquisition_items:
        return False, f"acquisition queue requires source-backed acquisition ({acquisition_items})"
    best_child_val = _best_generated_child_val(run_dir)
    best_root_val = _best_root_val(run_dir)
    if (
        target_val_macro_f1 is not None
        and best_child_val is not None
        and best_child_val >= target_val_macro_f1
        and (best_root_val is None or best_child_val > best_root_val)
    ):
        root_clause = "no trained root" if best_root_val is None else f"best root {best_root_val:.6f}"
        return False, f"target reached and root beaten by generated child ({best_child_val:.6f} >= {target_val_macro_f1:.6f}; {root_clause})"
    trained_children = sum(1 for node in _tree_nodes(run_dir).values() if node.get("parent") and node.get("status") == "trained")
    if trained_children >= trained_budget:
        return False, f"trained rollout budget exhausted ({trained_children}/{trained_budget})"
    if stop_reason.startswith("no improvement"):
        return False, stop_reason
    if stop_reason.startswith("trained-node budget exhausted"):
        return False, stop_reason
    if stop_reason.startswith("proposal budget exhausted") and _count_status(run_dir, "candidate_queued") == 0:
        return False, stop_reason
    queued = _count_status(run_dir, "candidate_queued")
    if queued > 0:
        return True, f"drain global queue ({queued} queued candidates; stop_reason={stop_reason or 'unknown'})"
    if stop_reason in {"pending implementation trained", ""}:
        return True, f"resume after intermediate stop_reason={stop_reason or 'unknown'}"
    return False, stop_reason or "no continuation condition"


def resume_command(args: argparse.Namespace, roots: list[str], run_dir: Path, experiment: str, level: TransferLevel, max_epochs: int) -> list[str]:
    clone = argparse.Namespace(**vars(args))
    clone.resume = True
    return build_command(clone, roots, run_dir, experiment, level, max_epochs)


def execute_command_loop(command: list[str], args: argparse.Namespace, roots: list[str], run_dir: Path, experiment: str, level: TransferLevel, max_epochs: int) -> int:
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = "src" + ((":" + env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
    if level.run_type != "full_cellline_run":
        return subprocess.call(command, env=env)
    current = list(command)
    max_cycles = 50
    for cycle in range(1, max_cycles + 1):
        print(f"[full_cellline_run] cycle {cycle}: {' '.join(shlex.quote(part) for part in current)}", flush=True)
        exit_code = subprocess.call(current, env=env)
        if exit_code != 0:
            return exit_code
        should_continue, reason = full_run_continue_reason(run_dir, args.target_val_macro_f1, level.budget_trained_nodes)
        print(f"[full_cellline_run] continuation_check: continue={should_continue} reason={reason}", flush=True)
        if not should_continue:
            return 0
        current = resume_command(args, roots, run_dir, experiment, level, max_epochs)
    print(f"full_cellline_run exceeded max continuation cycles ({max_cycles})", file=sys.stderr)
    return 2


def build_command(args: argparse.Namespace, roots: list[str], run_dir: Path, experiment: str, level: TransferLevel, max_epochs: int) -> list[str]:
    cmd = [
        sys.executable,
        "scripts/run_official_cellline_harness_search.py",
        "--cell-line",
        args.cell_line,
        "--run-dir",
        str(run_dir),
        "--experiment",
        experiment,
        "--root-configs",
        *roots,
        "--budget-proposals",
        str(level.budget_proposals),
        "--budget-trained-nodes",
        str(level.budget_trained_nodes),
        "--candidate-pool-size",
        str(level.candidate_pool_size),
        "--proposal-selection-mode",
        "global_queue" if level.run_type == "full_cellline_run" else "local_top1",
        "--max-epochs",
        str(max_epochs),
        "--max-children",
        str(level.max_children),
        "--stop-no-improve",
        str(level.stop_no_improve),
        "--selection-policy",
        "uct",
        "--official-blueprint-space",
        "--allow-planned-blueprints",
        "--strict-artifacts",
        "--enable-implementation-loop",
        "--implementation-repair-attempts",
        str(args.implementation_repair_attempts),
    ]
    if level.run_type != "full_cellline_run":
        cmd.append("--allow-implementation-skip")
    if args.resume:
        return cmd
    return [*cmd, "--reset"]


def run_dir_has_state(run_dir: Path) -> bool:
    if not run_dir.exists():
        return False
    state_markers = [
        "tree.json",
        "run_manifest.json",
        "implementation_queue.json",
        "acquisition_queue.json",
        "programs",
        "nodes",
    ]
    return any((run_dir / marker).exists() for marker in state_markers)


def write_plan(path: Path, payload: dict[str, object], command: list[str]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "transfer_invocation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    command_text = " ".join(shlex.quote(part) for part in command)
    md = [
        "# Generic Cell-Line Transfer Invocation",
        "",
        f"- Cell line: `{payload['cell_line']}`",
        f"- Slug: `{payload['cell_line_slug']}`",
        f"- Run type: `{payload['run_type']}`",
        f"- Level: `{payload['level']}`",
        f"- Artifact-constrained filter required: `{payload['artifact_constrained_required']}`",
        f"- Proposal selection mode: `{payload['proposal_selection_mode']}`",
        f"- Max epochs: `{payload['max_epochs']}`",
        f"- Target validation Macro-F1: `{payload['target_val_macro_f1']}`",
        f"- Run dir: `{payload['run_dir']}`",
        f"- Experiment: `{payload['experiment']}`",
        f"- Resume: `{payload['resume']}`",
        f"- Root configs: {', '.join(f'`{r}`' for r in payload['root_configs'])}",
        "",
        "## Command",
        "",
        "```bash",
        f"PYTHONPATH=src {command_text}",
        "```",
        "",
        "## Required Runbook",
        "",
        "Follow `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` and validate against `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`.",
    ]
    (path / "transfer_invocation.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standard entrypoint for generic cell-line transfer tests and full runs.")
    parser.add_argument("--cell-line", required=True, help="Cell line id, for example K562 or a source-backed second cell line.")
    parser.add_argument("--run-type", choices=["loop_self_test", "full_cellline_run"], default="loop_self_test")
    parser.add_argument("--level", choices=sorted(LEVELS), default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--experiment", default=None)
    parser.add_argument("--root-configs", nargs="*", default=None)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--target-val-macro-f1", type=float, default=None, help="Required for full_cellline_run: minimum acceptable best generated child validation Macro-F1.")
    parser.add_argument("--implementation-repair-attempts", type=int, default=3)
    parser.add_argument("--resume", action="store_true", help="Resume the existing run instead of adding --reset.")
    parser.add_argument("--execute", action="store_true", help="Run the generated command after writing the invocation files.")
    parser.add_argument("--print-command", action="store_true", help="Print the generated command and exit unless --execute is also set.")
    args = parser.parse_args()

    level_name, level, max_epochs = resolve_level_and_epochs(args)
    slug = slugify(args.cell_line)
    roots = args.root_configs if args.root_configs else default_root_configs(args.cell_line, slug)
    if not roots:
        raise SystemExit(
            f"No root configs found for CELL_LINE_ID={args.cell_line}. Expected configs/official_{slug}_roots/*.json "
            "or explicit --root-configs. Build source-backed roots first; do not reuse K562 roots."
        )
    missing_roots = [root for root in roots if not Path(root).exists()]
    if missing_roots:
        raise SystemExit("Missing root config(s): " + ", ".join(missing_roots))

    run_dir = args.run_dir or Path("experiments") / f"official_{slug}_generic_transfer_v1" / level_name
    experiment = args.experiment or f"official_{slug}_{level_name}"
    if not args.resume and run_dir_has_state(run_dir):
        raise SystemExit(
            f"RUN_DIR already contains run state: {run_dir}. "
            "Use --resume to continue this run, or choose a fresh RUN_DIR for a from-scratch run. "
            "Refusing to overwrite tree/program state because that can erase trained selected rollouts."
        )
    command = build_command(args, roots, run_dir, experiment, level, max_epochs)
    payload = {
        "cell_line": args.cell_line,
        "cell_line_slug": slug,
        "run_type": level.run_type,
        "level": level_name,
        "level_description": level.description,
        "artifact_constrained_required": level.artifact_constrained_required,
        "proposal_selection_mode": "global_queue" if level.run_type == "full_cellline_run" else "local_top1",
        "run_dir": str(run_dir),
        "experiment": experiment,
        "root_configs": roots,
        "resume": args.resume,
        "max_epochs": max_epochs,
        "target_val_macro_f1": args.target_val_macro_f1,
        "implementation_repair_attempts": args.implementation_repair_attempts,
        "guardrails": {
            "no_fallback": True,
            "no_compact_proxy": True,
            "strict_artifacts": True,
            "validation_macro_f1_reward": True,
            "test_metric_report_only": True,
            "full_run_forbids_one_epoch": level.run_type == "full_cellline_run",
            "artifact_constrained_blueprint_filter_required": level.artifact_constrained_required,
            "primary_objective": "best_generated_child_beats_best_root_and_reaches_target_score" if level.run_type == "full_cellline_run" else "loop_mechanics",
            "target_val_macro_f1": args.target_val_macro_f1,
        },
    }
    write_plan(run_dir, payload, command)
    command_text = "PYTHONPATH=src " + " ".join(shlex.quote(part) for part in command)
    if args.print_command or not args.execute:
        print(command_text)
        print(f"Invocation written to {run_dir / 'transfer_invocation.md'}")
    if args.execute:
        raise SystemExit(execute_command_loop(command, args, roots, run_dir, experiment, level, max_epochs))


if __name__ == "__main__":
    main()
