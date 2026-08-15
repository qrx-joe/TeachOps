"""Replay the four fixed normal-case artifacts with provenance validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.fixture_replay import replay_normal_fixture


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay the TeachOps normal-case fixture (not an AgentTeams live run)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "demo" / "normal-case" / "fixture-replay-output",
    )
    args = parser.parse_args()
    summary = replay_normal_fixture(
        ROOT / "demo" / "normal-case" / "expected-output", args.output_dir
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
