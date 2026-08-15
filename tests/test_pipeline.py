from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.pipeline import (
    PipelineError,
    PipelinePaths,
    audit_lesson,
    build_evidence_packet,
    revise_lesson,
    run_blocked_case,
    run_normal_case,
)


class PipelineTest(unittest.TestCase):
    def paths_for(self, case: str) -> PipelinePaths:
        input_dir = ROOT / "demo" / case / "input"
        return PipelinePaths(
            lesson_draft=input_dir / "lesson-draft.md",
            learner_summary=input_dir / "learner-summary.json",
            rule_pack=input_dir / "rule-pack.json",
            curriculum_source=input_dir / "curriculum-source.md",
            approval_decision=(
                input_dir / "approval-decision.json" if case == "normal-case" else None
            ),
        )

    def audited_candidate(self) -> tuple[str, dict, dict]:
        paths = self.paths_for("normal-case")
        packet = build_evidence_packet(paths)
        rules = json.loads(paths.rule_pack.read_text(encoding="utf-8"))
        revised = revise_lesson(paths.lesson_draft, packet, rules)
        return revised, packet, rules

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
            self.assertTrue((output_dir / "approval_decision.json").is_file())
            self.assertEqual(
                summary["approval_decision_id"], "RD-normal-deterministic-001"
            )
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

    def test_invalid_evidence_references_are_not_passed(self) -> None:
        revised, packet, rules = self.audited_candidate()
        fake_rationale = revised.replace("EV-004", "EV-999")
        rationale_report = audit_lesson(
            fake_rationale, packet, rules, report_id="AR-test-fake-rationale"
        )
        r2 = next(x for x in rationale_report["findings"] if x["rule_id"] == "R-002")
        self.assertEqual(r2["result"], "WARN")

        fake_goal = revised.replace("证据：EV-001）。", "证据：EV-999）。", 1)
        goal_report = audit_lesson(
            fake_goal, packet, rules, report_id="AR-test-fake-goal"
        )
        r4 = next(x for x in goal_report["findings"] if x["rule_id"] == "R-004")
        self.assertEqual(r4["result"], "WARN")

    def test_misconception_requires_explicit_response_marker(self) -> None:
        revised, packet, rules = self.audited_candidate()
        without_response = re.sub(
            r"【响应学情\s+M-01；证据\s+EV-003】", "", revised
        )
        report = audit_lesson(
            without_response, packet, rules, report_id="AR-test-no-response"
        )
        r3 = next(x for x in report["findings"] if x["rule_id"] == "R-003")
        self.assertEqual(r3["result"], "FAIL")

    def test_every_activity_requires_a_valid_duration(self) -> None:
        revised, packet, rules = self.audited_candidate()
        missing_duration = revised.replace(
            "| 环节 2 认识 1/2 | 12 分钟 |", "| 环节 2 认识 1/2 | — |"
        )
        report = audit_lesson(
            missing_duration, packet, rules, report_id="AR-test-missing-duration"
        )
        r5 = next(x for x in report["findings"] if x["rule_id"] == "R-005")
        self.assertEqual(r5["result"], "WARN")
        self.assertIn("环节 2 认识 1/2", r5["explanation"])

    def test_highest_frequency_misconception_does_not_depend_on_array_order(self) -> None:
        paths = self.paths_for("normal-case")
        learner = json.loads(paths.learner_summary.read_text(encoding="utf-8"))
        learner["misconceptions"].reverse()
        with tempfile.TemporaryDirectory() as temp_dir:
            learner_path = Path(temp_dir) / "learner-summary.json"
            learner_path.write_text(
                json.dumps(learner, ensure_ascii=False), encoding="utf-8"
            )
            packet = build_evidence_packet(
                replace(paths, learner_summary=learner_path)
            )
        ev3 = next(x for x in packet["evidence_items"] if x["evidence_id"] == "EV-003")
        self.assertEqual(ev3["source_item_id"], "M-01")
        self.assertEqual(ev3["observed_frequency"], "17/42")
        self.assertIn("misconceptions[1]（M-01）", ev3["locator"])

    def test_blocked_run_removes_stale_managed_downstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "shared-output"
            run_normal_case(self.paths_for("normal-case"), output_dir)
            summary = run_blocked_case(
                self.paths_for("missing-evidence-case"), output_dir
            )
            self.assertEqual(summary["status"], "BLOCKED")
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                ["evidence_packet.json", "run_summary.json"],
            )

    def test_normal_run_requires_explicit_approval_decision(self) -> None:
        paths = replace(self.paths_for("normal-case"), approval_decision=None)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with self.assertRaisesRegex(PipelineError, "approval_decision"):
                run_normal_case(paths, output_dir)
            self.assertFalse(output_dir.exists())

    def test_rule_pack_controls_marker_and_duration_limit(self) -> None:
        paths = self.paths_for("normal-case")
        packet = build_evidence_packet(paths)
        rules = json.loads(paths.rule_pack.read_text(encoding="utf-8"))
        rule_by_id = {rule["rule_id"]: rule for rule in rules["rules"]}
        rule_by_id["R-003"]["deterministic_check"]["format"] = (
            "[RESP:{source_item_id}:{evidence_id}]"
        )
        rule_by_id["R-005"]["parameters"]["max_total_minutes"] = 45

        revised = revise_lesson(paths.lesson_draft, packet, rules)
        report = audit_lesson(revised, packet, rules, report_id="AR-test-rule-params")
        self.assertIn("[RESP:M-01:EV-003]", revised)
        self.assertEqual(
            next(x for x in report["findings"] if x["rule_id"] == "R-003")["result"],
            "PASS",
        )
        self.assertEqual(
            next(x for x in report["findings"] if x["rule_id"] == "R-005")["result"],
            "PASS",
        )

    def test_invalid_approval_is_not_published(self) -> None:
        paths = self.paths_for("normal-case")
        decision = json.loads(paths.approval_decision.read_text(encoding="utf-8"))
        decision["applies_to_report_id"] = "AR-wrong"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            decision_path = root / "approval-decision.json"
            decision_path.write_text(
                json.dumps(decision, ensure_ascii=False), encoding="utf-8"
            )
            output_dir = root / "output"
            with self.assertRaisesRegex(PipelineError, "审计报告不匹配"):
                run_normal_case(
                    replace(paths, approval_decision=decision_path), output_dir
                )
            self.assertFalse(output_dir.exists())

    def test_refuses_to_clean_unowned_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "unowned-output"
            output_dir.mkdir()
            user_file = output_dir / "revised-lesson.md"
            user_file.write_text("user-owned", encoding="utf-8")
            with self.assertRaisesRegex(PipelineError, "无法证明"):
                run_blocked_case(
                    self.paths_for("missing-evidence-case"), output_dir
                )
            self.assertEqual(user_file.read_text(encoding="utf-8"), "user-owned")


if __name__ == "__main__":
    unittest.main()
