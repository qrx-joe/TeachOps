from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.fixture_replay import (
    ARTIFACT_NAMES,
    FixtureReplayError,
    replay_normal_fixture,
)


class FixtureReplayTest(unittest.TestCase):
    def test_replay_produces_exactly_four_labelled_artifacts(self) -> None:
        source = ROOT / "demo" / "normal-case" / "expected-output"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "output"
            summary = replay_normal_fixture(source, output)

            self.assertEqual(summary["evidence_type"], "fixture replay")
            self.assertFalse(summary["live_agentteams_run"])
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                sorted(ARTIFACT_NAMES),
            )
            packet = json.loads(
                (output / "evidence_packet.json").read_text(encoding="utf-8")
            )
            self.assertEqual(packet["status"], "READY")
            self.assertIn(
                "evidence_type: fixture replay",
                (output / "review_decision.md").read_text(encoding="utf-8"),
            )

    def test_replay_rejects_missing_provenance(self) -> None:
        source = ROOT / "demo" / "normal-case" / "expected-output"
        with tempfile.TemporaryDirectory() as temp_dir:
            broken = Path(temp_dir) / "broken"
            broken.mkdir()
            for name in ARTIFACT_NAMES:
                (broken / name).write_bytes((source / name).read_bytes())
            packet_path = broken / "evidence_packet.json"
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            packet["evidence_type"] = "live"
            packet_path.write_text(
                json.dumps(packet, ensure_ascii=False), encoding="utf-8"
            )

            with self.assertRaisesRegex(FixtureReplayError, "来源标记"):
                replay_normal_fixture(broken, Path(temp_dir) / "output")


if __name__ == "__main__":
    unittest.main()
