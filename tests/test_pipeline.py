from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.pipeline import PipelinePaths, run_blocked_case, run_normal_case


class PipelineTest(unittest.TestCase):
    def paths_for(self, case: str) -> PipelinePaths:
        input_dir = ROOT / "demo" / case / "input"
        return PipelinePaths(
            lesson_draft=input_dir / "lesson-draft.md",
            learner_summary=input_dir / "learner-summary.json",
            rule_pack=input_dir / "rule-pack.json",
            curriculum_source=input_dir / "curriculum-source.md",
        )

    def test_normal_case_revises_audits_applies_condition_and_reaudits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            summary = run_normal_case(self.paths_for("normal-case"), output_dir)

            self.assertEqual(summary["status"], "COMPLETED")
            revised = (output_dir / "revised-lesson.md").read_text(encoding="utf-8")
            final = (output_dir / "final-lesson.md").read_text(encoding="utf-8")
            initial_audit = json.loads(
                (output_dir / "audit_report.initial.json").read_text(encoding="utf-8")
            )
            final_audit = json.loads(
                (output_dir / "audit_report.final.json").read_text(encoding="utf-8")
            )

            self.assertIn("1/2 与 1/8 谁大", revised)
            self.assertIn("# 教学设计候选修订稿", revised)
            self.assertIn("| 环节 4 课堂小结 | 8 分钟 |", revised)
            self.assertIn("# 教学设计最终稿", final)
            self.assertIn("| 环节 4 课堂小结 | 3 分钟 |", final)
            self.assertEqual(initial_audit["overall"]["total_minutes"], 45)
            self.assertEqual(
                next(x for x in initial_audit["findings"] if x["rule_id"] == "R-005")["result"],
                "WARN",
            )
            self.assertEqual(final_audit["overall"]["total_minutes"], 40)
            self.assertTrue(all(x["result"] == "PASS" for x in final_audit["findings"]))

    def test_missing_evidence_blocks_before_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            summary = run_blocked_case(
                self.paths_for("missing-evidence-case"), output_dir
            )
            packet = json.loads(
                (output_dir / "evidence_packet.json").read_text(encoding="utf-8")
            )

            self.assertEqual(summary["status"], "BLOCKED")
            self.assertFalse(summary["downstream_called"])
            self.assertEqual(packet["blocked_reason"], "E_INPUT_MISSING")
            self.assertTrue(packet["missing_items"])
            self.assertFalse((output_dir / "revised-lesson.md").exists())
            self.assertFalse((output_dir / "audit_report.initial.json").exists())


if __name__ == "__main__":
    unittest.main()
