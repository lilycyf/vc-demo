from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


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
    "full_cellline_run": TransferLevel(150, 50, 4, 8, 30, "full_cellline_run", 5, "formal full cell-line run with real model-quality budget", True),
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
    if level.run_type == "full_cellline_run" and max_epochs < 5:
        raise SystemExit("full_cellline_run requires --max-epochs >= 5; 1-epoch smoke budgets are forbidden.")
    return level_name, level, max_epochs


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
    if args.resume:
        return cmd
    return [*cmd, "--reset"]


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
        f"- Max epochs: `{payload['max_epochs']}`",
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
    command = build_command(args, roots, run_dir, experiment, level, max_epochs)
    payload = {
        "cell_line": args.cell_line,
        "cell_line_slug": slug,
        "run_type": level.run_type,
        "level": level_name,
        "level_description": level.description,
        "artifact_constrained_required": level.artifact_constrained_required,
        "run_dir": str(run_dir),
        "experiment": experiment,
        "root_configs": roots,
        "resume": args.resume,
        "max_epochs": max_epochs,
        "implementation_repair_attempts": args.implementation_repair_attempts,
        "guardrails": {
            "no_fallback": True,
            "no_compact_proxy": True,
            "strict_artifacts": True,
            "validation_macro_f1_reward": True,
            "test_metric_report_only": True,
            "full_run_forbids_one_epoch": level.run_type == "full_cellline_run",
            "artifact_constrained_blueprint_filter_required": level.artifact_constrained_required,
        },
    }
    write_plan(run_dir, payload, command)
    command_text = "PYTHONPATH=src " + " ".join(shlex.quote(part) for part in command)
    if args.print_command or not args.execute:
        print(command_text)
        print(f"Invocation written to {run_dir / 'transfer_invocation.md'}")
    if args.execute:
        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = "src" + ((":" + env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
        raise SystemExit(subprocess.call(command, env=env))


if __name__ == "__main__":
    main()
