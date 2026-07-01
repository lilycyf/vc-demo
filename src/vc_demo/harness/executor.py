from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.state import node_dir, write_json
from vc_demo.train import train


def run_node(config: dict[str, Any], run_dir: Path, proposal: dict[str, Any] | None, max_epochs: int | None) -> dict[str, Any]:
    name = str(config["node_name"])
    out_dir = node_dir(run_dir, name)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "config.json", config)
    if proposal is not None:
        write_json(out_dir / "proposal.json", proposal)
    write_json(out_dir / "status.json", {"status": "training"})
    try:
        metrics = train(config, out_dir, max_epochs=max_epochs)
        write_json(out_dir / "status.json", {"status": "trained", "best_val_macro_f1": metrics["best_val_macro_f1"]})
        return metrics
    except Exception as exc:
        write_json(
            out_dir / "status.json",
            {
                "status": "failed",
                "error": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
                "traceback": traceback.format_exc(),
            },
        )
        raise
