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
    description: str


LEVELS: dict[str, TransferLevel] = {
    "preflight": TransferLevel(8, 2, 2, 4, 4, "minimal wiring smoke"),
    "transfer_64x16": TransferLevel(64, 16, 4, 8, 12, "generic transfer loop test"),
    "transfer_150x40": TransferLevel(150, 40, 4, 8, 30, "medium generic transfer pressure test"),
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


def build_command(args: argparse.Namespace, roots: list[str], run_dir: Path, experiment: str) -> list[str]:
    level = LEVELS[args.level]
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
        str(args.max_epochs),
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
        f"- Level: `{payload['level']}`",
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
    parser = argparse.ArgumentParser(description="Standard entrypoint for generic cell-line transfer tests.")
    parser.add_argument("--cell-line", required=True, help="Cell line id, for example K562 or a source-backed second cell line.")
    parser.add_argument("--level", choices=sorted(LEVELS), default="transfer_64x16")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--experiment", default=None)
    parser.add_argument("--root-configs", nargs="*", default=None)
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--implementation-repair-attempts", type=int, default=3)
    parser.add_argument("--resume", action="store_true", help="Resume the existing run instead of adding --reset.")
    parser.add_argument("--execute", action="store_true", help="Run the generated command after writing the invocation files.")
    parser.add_argument("--print-command", action="store_true", help="Print the generated command and exit unless --execute is also set.")
    args = parser.parse_args()

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

    run_dir = args.run_dir or Path("experiments") / f"official_{slug}_generic_transfer_v1" / args.level
    experiment = args.experiment or f"official_{slug}_{args.level}"
    command = build_command(args, roots, run_dir, experiment)
    payload = {
        "cell_line": args.cell_line,
        "cell_line_slug": slug,
        "level": args.level,
        "level_description": LEVELS[args.level].description,
        "run_dir": str(run_dir),
        "experiment": experiment,
        "root_configs": roots,
        "resume": args.resume,
        "max_epochs": args.max_epochs,
        "implementation_repair_attempts": args.implementation_repair_attempts,
        "guardrails": {
            "no_fallback": True,
            "no_compact_proxy": True,
            "strict_artifacts": True,
            "validation_macro_f1_reward": True,
            "test_metric_report_only": True,
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
