"""Run the deterministic TeachOps demo with uv or Python."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.pipeline import PipelinePaths, run_blocked_case, run_normal_case


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TeachOps deterministic demo")
    parser.add_argument("case", choices=["normal", "missing-evidence"])
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    case_dir = "normal-case" if args.case == "normal" else "missing-evidence-case"
    input_dir = ROOT / "demo" / case_dir / "input"
    output_dir = args.output_dir or ROOT / "demo" / case_dir / "deterministic-output"
    paths = PipelinePaths(
        lesson_draft=input_dir / "lesson-draft.md",
        learner_summary=input_dir / "learner-summary.json",
        rule_pack=input_dir / "rule-pack.json",
        curriculum_source=input_dir / "curriculum-source.md",
        approval_decision=(
            input_dir / "approval-decision.json" if args.case == "normal" else None
        ),
    )
    result = (
        run_normal_case(paths, output_dir)
        if args.case == "normal"
        else run_blocked_case(paths, output_dir)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"output_dir: {output_dir}")


if __name__ == "__main__":
    main()
