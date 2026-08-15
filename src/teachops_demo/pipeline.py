"""Deterministic, dependency-free TeachOps demo pipeline.

This module implements the smallest executable loop needed by the fixed demo:
Evidence -> revised lesson -> audit -> conditional change -> re-audit.
It intentionally does not call an LLM or claim to be an AgentTeams live run.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PipelineError(RuntimeError):
    """Raised when a deterministic contract cannot be satisfied safely."""


@dataclass(frozen=True)
class PipelinePaths:
    lesson_draft: Path
    learner_summary: Path
    rule_pack: Path
    curriculum_source: Path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"缺少必需输入：{path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"JSON 无法解析：{path}: {exc}") from exc


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require_synthetic(learner_summary: dict[str, Any]) -> None:
    if learner_summary.get("synthetic") is not True:
        raise PipelineError("E_DATA_QUALITY：学情摘要必须显式标记 synthetic: true")


def _learner_evidence(
    learner_summary: dict[str, Any], *, id_offset: int = 0
) -> list[dict[str, str]]:
    misconceptions = learner_summary.get("misconceptions") or []
    observations = learner_summary.get("observation_notes") or []
    if not misconceptions or not observations:
        raise PipelineError("E_DATA_QUALITY：学情摘要缺少 misconceptions 或 observation_notes")

    misconception = misconceptions[0]
    return [
        {
            "evidence_id": f"EV-{3 + id_offset:03d}",
            "source": "learner-summary.json（synthetic）",
            "locator": "misconceptions[0]（M-01）",
            "summary": (
                f"{misconception['pattern']}，观测频率 "
                f"{misconception['observed_frequency']}。"
            ),
            "quote_type": "原文摘录",
            "verify_status": "VERIFIED",
        },
        {
            "evidence_id": f"EV-{4 + id_offset:03d}",
            "source": "learner-summary.json（synthetic）",
            "locator": "observation_notes[0]",
            "summary": str(observations[0]),
            "quote_type": "原文摘录",
            "verify_status": "VERIFIED",
        },
    ]


def build_evidence_packet(paths: PipelinePaths) -> dict[str, Any]:
    """Build a READY packet, or a BLOCKED packet when curriculum is missing."""

    learner_summary = _read_json(paths.learner_summary)
    _require_synthetic(learner_summary)
    fixture_date = str(learner_summary.get("generated_at", "unknown"))

    if not paths.curriculum_source.is_file():
        packet = {
            "evidence_type": "fixture replay",
            "generator": "teachops-demo deterministic runner",
            "packet_id": "EP-missing-deterministic-001",
            "case": "missing-evidence-case",
            "status": "BLOCKED",
            "blocked_reason": "E_INPUT_MISSING",
            "generated_at": fixture_date,
            "evidence_items": _learner_evidence(learner_summary, id_offset=98),
            "missing_items": [
                "curriculum-source.md（关键课标证据缺失，无法验证 CUR 引用）"
            ],
            "next_action": "补交课程标准来源文件后重跑；不得调用修订步骤。",
        }
        return packet

    curriculum = paths.curriculum_source.read_text(encoding="utf-8")
    required_markers = ("CUR-01", "CUR-02")
    missing_markers = [marker for marker in required_markers if marker not in curriculum]
    if missing_markers:
        raise PipelineError(f"E_DATA_QUALITY：课程标准缺少条目 {missing_markers}")

    def quote_for(marker: str) -> str:
        section_match = re.search(
            rf"###\s+{re.escape(marker)}.*?(?=\n###\s+CUR-|\Z)",
            curriculum,
            flags=re.DOTALL,
        )
        if not section_match:
            raise PipelineError(f"无法定位课程标准条目：{marker}")
        quote_match = re.search(r"^>\s*(.+)$", section_match.group(0), re.MULTILINE)
        if not quote_match:
            raise PipelineError(f"课程标准条目没有短引用：{marker}")
        return quote_match.group(1).strip()

    evidence_items = [
        {
            "evidence_id": "EV-001",
            "source": "curriculum-source.md →《义务教育数学课程标准（2022年版）》",
            "locator": "CUR-02 第二学段‘数与运算’内容要求",
            "summary": quote_for("CUR-02"),
            "quote_type": "原文摘录",
            "verify_status": "VERIFIED",
        },
        {
            "evidence_id": "EV-002",
            "source": "curriculum-source.md →《义务教育数学课程标准（2022年版）》",
            "locator": "CUR-01 课程理念",
            "summary": quote_for("CUR-01"),
            "quote_type": "原文摘录",
            "verify_status": "VERIFIED",
        },
        *_learner_evidence(learner_summary),
    ]
    return {
        "evidence_type": "fixture replay",
        "generator": "teachops-demo deterministic runner",
        "packet_id": "EP-normal-deterministic-001",
        "case": "normal-case",
        "status": "READY",
        "generated_at": fixture_date,
        "evidence_items": evidence_items,
        "missing_items": [],
    }


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PipelineError(f"修订定位失败：{label} 预期出现 1 次，实际 {count} 次")
    return text.replace(old, new, 1)


def revise_lesson(lesson_draft: Path, packet: dict[str, Any]) -> str:
    """Apply the four evidence-backed changes to a complete lesson document."""

    if packet.get("status") != "READY":
        raise PipelineError("E_EVIDENCE_INSUFFICIENT：Evidence Packet 非 READY")
    evidence_ids = {item["evidence_id"] for item in packet["evidence_items"]}
    if not {"EV-001", "EV-002", "EV-003", "EV-004"}.issubset(evidence_ids):
        raise PipelineError("E_EVIDENCE_INSUFFICIENT：缺少修订所需证据")

    text = lesson_draft.read_text(encoding="utf-8")
    replacements = [
        (
            "# 教学设计初稿：分数的初步认识（第 1 课时）",
            "# 教学设计候选修订稿：分数的初步认识（第 1 课时）",
            "文档标题",
        ),
        (
            "1. 结合分物情境初步认识几分之一，会读、写简单分数，知道分数各部分的名称（课标条目：CUR-02）。",
            "1. 结合分物情境初步认识几分之一，会读、写简单分数，知道分数各部分的名称（课标条目：CUR-02；证据：EV-001）。",
            "教学目标 1",
        ),
        (
            "2. 通过折纸、涂色等操作活动，直观理解几分之一的含义，能比较两个同分母分数的大小（课标条目：CUR-02）。",
            "2. 通过折纸、涂色等操作活动，直观理解几分之一的含义，能比较两个同分母分数的大小（课标条目：CUR-02；证据：EV-001）。",
            "教学目标 2",
        ),
        (
            "3. 在小组合作交流中发展数感和合作意识。",
            "3. 能在小组内用分数的语言描述折纸结果，说清平均分与几分之一的含义（课标条目：CUR-02；证据：EV-001、EV-002）。",
            "教学目标 3",
        ),
        (
            "| 目标 3 | — |",
            "| 目标 3 | 任务 C：小组折纸汇报；按‘说清平均分、说清几分之一’两条标准互评 |",
            "目标 3 评价任务",
        ),
        (
            "| 环节 3 认识几分之一 | 12 分钟 | 折出 1/4、1/8 并涂色表示；完成同分母比较：1/4 与 3/4 谁大 |",
            "| 环节 3 认识几分之一与误解辨析 | 17 分钟 | 折出 1/4、1/8 并涂色；完成同分母比较；增加‘1/2 与 1/8 谁大’投票与同样大圆纸叠放辨析，并引用学情误解证据 EV-003 |",
            "环节 3",
        ),
        (
            "1. 采用\"分月饼\"情境导入：平均分物是学生的已有经验（见学情摘要先备知识），从\"分不完整数\"的认知冲突引出分数（课标条目：CUR-02）。",
            "1. 采用\"分月饼\"情境导入：平均分物是学生的已有经验，从认知冲突引出分数（课标条目：CUR-02；证据：EV-001）。",
            "关键设计理由 1",
        ),
        (
            "2. 环节 2 采用小组合作折纸：三年级学生注意力持续时间有限，动手操作活动更能维持课堂参与。",
            "2. 环节 2 采用小组合作折纸：合成观察显示连续专注约 15-20 分钟，因此在第 12 分钟后安排动手操作维持参与（证据：EV-004；仅限本演示学情）。",
            "关键设计理由 2",
        ),
        (
            "本初稿为 TeachOps 演示用合成样例（synthetic），故意保留若干可审计问题，用于展示 Evidence→Design→Audit 流程，不作为实际教学使用。",
            "本候选修订稿由固定合成样例生成，用于验证 Evidence→Design→Audit 确定性闭环，不作为实际教学使用。",
            "文档说明",
        ),
    ]
    for old, new, label in replacements:
        text = _replace_once(text, old, new, label)

    marker = (
        "> 生成说明：本文件由 TeachOps deterministic runner 根据 "
        f"{packet['packet_id']} 生成，属于 fixture replay，不是 AgentTeams live 结果。\n\n"
    )
    return text.replace("\n", "\n" + marker, 1)


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    if next_heading is None:
        return text[start:]
    end = text.find(next_heading, start + len(heading))
    return text[start:] if end < 0 else text[start:end]


def audit_lesson(
    lesson_text: str,
    packet: dict[str, Any],
    rule_pack: dict[str, Any],
    *,
    report_id: str,
) -> dict[str, Any]:
    """Evaluate all five demo rules without an LLM."""

    if packet.get("status") != "READY":
        return {
            "evidence_type": "fixture replay",
            "generator": "teachops-demo deterministic runner",
            "report_id": report_id,
            "complete": False,
            "missing": ["READY evidence_packet.json"],
            "findings": [],
        }

    evidence_ids = {item["evidence_id"] for item in packet["evidence_items"]}
    rules = {rule["rule_id"] for rule in rule_pack.get("rules", [])}
    if rules != {"R-001", "R-002", "R-003", "R-004", "R-005"}:
        raise PipelineError(f"规则包不符合演示契约：{sorted(rules)}")

    goals_section = _section(lesson_text, "## 一、教学目标", "## 二、评价任务")
    assessment_section = _section(lesson_text, "## 二、评价任务", "## 三、教学过程")
    process_section = _section(lesson_text, "## 三、教学过程", "## 四、关键设计理由")
    rationale_section = _section(lesson_text, "## 四、关键设计理由", "## 五、说明")
    goals = re.findall(r"^\s*(\d+)\.\s+(.+)$", goals_section, re.MULTILINE)
    assessment_rows = {
        int(number): value.strip()
        for number, value in re.findall(
            r"^\|\s*目标\s+(\d+)\s*\|\s*(.*?)\s*\|$",
            assessment_section,
            re.MULTILINE,
        )
    }
    rationale_items = re.findall(
        r"^\s*\d+\.\s+(.+)$", rationale_section, re.MULTILINE
    )

    r1_pass = bool(goals) and all(
        assessment_rows.get(int(number), "") not in {"", "—", "-"}
        for number, _ in goals
    )
    r2_pass = bool(rationale_items) and all(
        re.search(r"EV-\d{3}", item) for item in rationale_items
    )
    r3_pass = all(token in process_section for token in ("1/2", "1/8", "EV-003"))
    r4_pass = bool(goals) and all(
        re.search(r"CUR-\d{2}", body) and re.search(r"EV-\d{3}", body)
        for _, body in goals
    )
    durations = [
        int(value)
        for value in re.findall(r"^\|\s*环节.+?\|\s*(\d+)\s*分钟\s*\|", process_section, re.MULTILINE)
    ]
    total_minutes = sum(durations)
    r5_pass = bool(durations) and total_minutes <= 40

    findings = [
        {
            "rule_id": "R-001",
            "result": "PASS" if r1_pass else "FAIL",
            "location": "评价任务对应表",
            "evidence_ids": ["EV-001"] if "EV-001" in evidence_ids else [],
            "explanation": "每条目标均有非空评价任务。" if r1_pass else "存在无评价任务的目标。",
            "suggestion": "" if r1_pass else "为每条目标补充可执行评价任务。",
        },
        {
            "rule_id": "R-002",
            "result": "PASS" if r2_pass else "FAIL",
            "location": "关键设计理由",
            "evidence_ids": sorted(set(re.findall(r"EV-\d{3}", rationale_section))),
            "explanation": "每条关键理由均引用 Evidence ID。" if r2_pass else "存在未引用 Evidence ID 的关键理由。",
            "suggestion": "" if r2_pass else "补充可回溯证据，或删除无据断言。",
        },
        {
            "rule_id": "R-003",
            "result": "PASS" if r3_pass else "FAIL",
            "location": "教学过程",
            "evidence_ids": ["EV-003"] if r3_pass else [],
            "explanation": "已显式处理 1/2 与 1/8 的高频误解。" if r3_pass else "未发现针对最高频误解的显式活动。",
            "suggestion": "" if r3_pass else "增加分子为 1 的分数大小辨析。",
        },
        {
            "rule_id": "R-004",
            "result": "PASS" if r4_pass else "FAIL",
            "location": "教学目标",
            "evidence_ids": sorted(set(re.findall(r"EV-\d{3}", goals_section))),
            "explanation": "每条目标均包含 CUR 与 EV 映射。" if r4_pass else "存在未同时映射 CUR 与 EV 的目标。",
            "suggestion": "" if r4_pass else "补齐课程标准条目和 Evidence ID。",
        },
        {
            "rule_id": "R-005",
            "result": "PASS" if r5_pass else "WARN",
            "location": "教学过程总时长",
            "evidence_ids": [],
            "explanation": f"共 {total_minutes} 分钟；上限为 40 分钟。",
            "suggestion": "" if r5_pass else "将环节 4 从 8 分钟压缩至 3 分钟后重新审计。",
        },
    ]
    has_fail = any(item["result"] == "FAIL" for item in findings)
    needs_human = has_fail or any(item["result"] == "WARN" for item in findings)
    return {
        "evidence_type": "fixture replay",
        "generator": "teachops-demo deterministic runner",
        "report_id": report_id,
        "complete": True,
        "findings": findings,
        "overall": {
            "has_fail": has_fail,
            "needs_human_decision": needs_human,
            "total_minutes": total_minutes,
        },
    }


def apply_conditional_time_fix(revised_lesson: str) -> str:
    """Apply the explicit human condition: reduce lesson summary by five minutes."""

    fixed = _replace_once(
        revised_lesson,
        "| 环节 4 课堂小结 | 8 分钟 |",
        "| 环节 4 课堂小结 | 3 分钟 |",
        "附条件批准：压缩环节 4",
    )
    fixed = _replace_once(
        fixed,
        "# 教学设计候选修订稿：分数的初步认识（第 1 课时）",
        "# 教学设计最终稿：分数的初步认识（第 1 课时）",
        "最终稿标题",
    )
    return fixed.replace(
        "> 生成说明：",
        "> 条件落实：依据导师附条件批准，将环节 4 从 8 分钟压缩至 3 分钟。\n>\n> 生成说明：",
        1,
    )


def run_normal_case(paths: PipelinePaths, output_dir: Path) -> dict[str, Any]:
    """Run READY -> revise -> audit -> condition -> re-audit."""

    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_evidence_packet(paths)
    _write_json(output_dir / "evidence_packet.json", packet)
    if packet["status"] != "READY":
        raise PipelineError("正常样例意外进入 BLOCKED")

    revised = revise_lesson(paths.lesson_draft, packet)
    (output_dir / "revised-lesson.md").write_text(
        revised, encoding="utf-8", newline="\n"
    )
    rules = _read_json(paths.rule_pack)
    initial_audit = audit_lesson(
        revised, packet, rules, report_id="AR-normal-deterministic-initial"
    )
    _write_json(output_dir / "audit_report.initial.json", initial_audit)

    r5 = next(item for item in initial_audit["findings"] if item["rule_id"] == "R-005")
    if initial_audit["overall"]["has_fail"] or r5["result"] != "WARN":
        raise PipelineError("候选修订未达到‘仅 R-005 WARN’的条件修正前状态")

    final_lesson = apply_conditional_time_fix(revised)
    (output_dir / "final-lesson.md").write_text(
        final_lesson, encoding="utf-8", newline="\n"
    )
    final_audit = audit_lesson(
        final_lesson, packet, rules, report_id="AR-normal-deterministic-final"
    )
    _write_json(output_dir / "audit_report.final.json", final_audit)
    if any(item["result"] != "PASS" for item in final_audit["findings"]):
        raise PipelineError("条件修正后的重新审计未全部通过")

    summary = {
        "evidence_type": "fixture replay",
        "generator": "teachops-demo deterministic runner",
        "case": "normal-case",
        "status": "COMPLETED",
        "steps": [
            "EVIDENCE_READY",
            "REVISED_LESSON_GENERATED",
            "INITIAL_AUDIT_R005_WARN",
            "APPROVAL_CONDITION_APPLIED",
            "FINAL_AUDIT_PASS",
        ],
        "artifacts": [
            "evidence_packet.json",
            "revised-lesson.md",
            "audit_report.initial.json",
            "final-lesson.md",
            "audit_report.final.json",
        ],
    }
    _write_json(output_dir / "run_summary.json", summary)
    return summary


def run_blocked_case(paths: PipelinePaths, output_dir: Path) -> dict[str, Any]:
    """Run the missing-evidence case and prove downstream work is not produced."""

    output_dir.mkdir(parents=True, exist_ok=True)
    packet = build_evidence_packet(paths)
    _write_json(output_dir / "evidence_packet.json", packet)
    if packet["status"] != "BLOCKED":
        raise PipelineError("缺证据样例未按预期进入 BLOCKED")

    summary = {
        "evidence_type": "fixture replay",
        "generator": "teachops-demo deterministic runner",
        "case": "missing-evidence-case",
        "status": "BLOCKED",
        "stopped_after": "EVIDENCE_BUILDING",
        "downstream_called": False,
        "artifacts": ["evidence_packet.json"],
    }
    _write_json(output_dir / "run_summary.json", summary)
    return summary
