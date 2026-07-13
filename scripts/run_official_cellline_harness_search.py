from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def slugify(cell_line: str) -> str:
    slug = cell_line.strip().lower().replace("+", "plus")
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    return slug or "cell_line"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic official cell-line harness search entrypoint.",
        add_help=False,
    )
    parser.add_argument("--cell-line", required=True)
    known, remaining = parser.parse_known_args()
    cell_line = known.cell_line.strip()
    slug = slugify(cell_line)
    normalized = cell_line.lower().replace("_", "-")

    if normalized in {"k562", "k-562"}:
        script = Path(__file__).resolve().with_name("run_official_k562_harness_search.py")
        os.execv(sys.executable, [sys.executable, str(script), *remaining])

    repo = Path.cwd()
    expected = {
        "task_contract": repo / "data" / "cell_lines" / f"official_{slug}_cls" / "manifest.json",
        "artifact_registry": repo / "configs" / "artifacts" / f"{slug}_registry.json",
        "root_config_dir": repo / "configs" / f"official_{slug}_roots",
    }
    missing = [name for name, path in expected.items() if not path.exists()]
    if missing:
        details = "\n".join(f"- {name}: {expected[name]}" for name in missing)
        raise SystemExit(
            f"CELL_LINE_ID={cell_line} is not yet configured for the generic official harness.\n"
            f"Missing source-backed task/artifact config:\n{details}\n"
            "Create these from verified sources first; do not fallback to K562 artifacts."
        )

    raise SystemExit(
        f"CELL_LINE_ID={cell_line} has task/artifact config stubs, but no execution backend is registered yet.\n"
        "Add a source-backed official cell-line backend or dispatcher before running search; do not use K562-only code implicitly."
    )


if __name__ == "__main__":
    main()
