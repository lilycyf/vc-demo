from __future__ import annotations

import argparse
from pathlib import Path

from vc_demo.harness.feedback import build_framework_feedback, write_framework_feedback


def main() -> None:
    parser = argparse.ArgumentParser(description="Infer framework-level feedback from a completed run and write framework_feedback.json/md.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--target-val-macro-f1", type=float, default=None)
    args = parser.parse_args()
    feedback = build_framework_feedback(args.run_dir, target_val_macro_f1=args.target_val_macro_f1)
    write_framework_feedback(args.run_dir, feedback)
    print(f"wrote {args.run_dir / 'framework_feedback.json'}")
    print(f"wrote {args.run_dir / 'framework_feedback.md'}")


if __name__ == "__main__":
    main()
