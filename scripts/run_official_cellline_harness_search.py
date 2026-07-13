from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic official cell-line harness search wrapper. Currently dispatches the validated K562 backend when --cell-line is K562.",
        add_help=False,
    )
    parser.add_argument("--cell-line", required=True)
    known, remaining = parser.parse_known_args()
    cell_line = known.cell_line.strip()
    normalized = cell_line.lower().replace("_", "-")
    if normalized not in {"k562", "k-562"}:
        raise SystemExit(
            "run_official_cellline_harness_search.py currently supports only CELL_LINE_ID=K562/K-562. "
            "Other cell lines must first add source-backed task/artifact configs; do not fallback."
        )
    script = Path(__file__).resolve().with_name("run_official_k562_harness_search.py")
    os.execv(sys.executable, [sys.executable, str(script), *remaining])


if __name__ == "__main__":
    main()
