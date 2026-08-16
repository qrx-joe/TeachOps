"""Deterministic, dependency-free TeachOps demo pipeline.

This module implements the smallest executable loop needed by the fixed demo:
Evidence -> revised lesson -> audit -> conditional change -> re-audit.
It intentionally does not call an LLM or claim to be an AgentTeams live run.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from fractions import Fraction
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
    approval_decision: Path | None = None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"缺少必需输入：{path}") from exc
    except json.JSONDecodeError as exc:
        # 文件存在但内容非法属于数据质量问题，不属于"文件缺失"，不得误报为 BLOCKED。
        raise PipelineError(f"E_DATA_QUALITY：JSON 无法解析：{path}: {exc}") from exc


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


_MANAGED_ARTIFACTS = {
    "approval_decision.json",
    "audit_report.final.json",
    "audit_report.initial.json",
    "evidence_packet.json",
    "final-lesson.md",
    "revised-lesson.md",
    "run_summary.json",
}


def _publish_staged(stage: Path, output_dir: Path, artifact_names: list[str]) -> None:
    """Publish one completed run and remove only stale TeachOps-owned artifacts."""

    expected = set(artifact_names)
    if not expected <= _MANAGED_ARTIFACTS:
        raise PipelineError(f"发现未注册产物：{sorted(expected - _MANAGED_ARTIFACTS)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_managed = [
        output_dir / name for name in _MANAGED_ARTIFACTS if (output_dir / name).exists()
    ]
    if existing_managed:
        summary_path = output_dir / "run_summary.json"
        try:
            previous_summary = _read_json(summary_path)
        except PipelineError as exc:
            raise PipelineError("输出目录含受管文件，但无法证明它由 TeachOps 生成") from exc
        if previous_summary.get("generator") != "teachops-demo deterministic runner":
            raise PipelineError("拒绝清理非 TeachOps 生成的输出目录")
    for name in _MANAGED_ARTIFACTS:
        target = output_dir / name
        if target.exists() and not target.is_file():
            raise PipelineError(f"受管产物路径不是文件：{target}")
        if name not in expected:
            target.unlink(missing_ok=True)
    for name in artifact_names:
        source = stage / name
        if not source.is_file():
            raise PipelineError(f"暂存运行缺少产物：{source}")
        source.replace(output_dir / name)


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

    def frequency(item: dict[str, Any]) -> tuple[int, int]:
        match = re.fullmatch(
            r"\s*(\d+)\s*/\s*(\d+)\s*",
            str(item.get("observed_frequency", "")),
        )
        if not match or int(match.group(2)) <= 0:
            raise PipelineError(
                f"E_DATA_QUALITY：错误的 observed_frequency：{item.get('observed_frequency')}"
            )
        return int(match.group(1)), int(match.group(2))

    indexed = list(enumerate(misconceptions))
    misconception_index, misconception = max(
        indexed,
        key=lambda pair: Fraction(*frequency(pair[1])),
    )
    misconception_id = str(misconception.get("id", "")).strip()
    if not misconception_id:
        raise PipelineError("E_DATA_QUALITY：最高频误解缺少 id")
    return [
        {
            "evidence_id": f"EV-{3 + id_offset:03d}",
            "source": "learner-summary.json（synthetic）",
            "locator": f"misconceptions[{misconception_index}]（{misconception_id}）",
            "summary": (
                f"{misconception['pattern']}，观测频率 "
                f"{misconception['observed_frequency']}。"
            ),
            "evidence_kind": "learner_misconception",
            "source_item_id": misconception_id,
            "observed_frequency": str(misconception["observed_frequency"]),
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
            "evidence_kind": "learner_observation",
            "source_item_id": "observation_notes[0]",
        },
    ]


def _missing_evidence_inputs(paths: PipelinePaths) -> list[str]:
    """列出全部缺失的必需 Evidence 输入，逐项返回而非用泛化错误掩盖。

    Skill Contract 要求 Manager 和导师能针对每个缺失文件行动，因此每个缺失
    文件单独成条；文件存在但内容非法时由调用方继续走 E_DATA_QUALITY，
    不在这里误报为"缺失"。
    """
    missing: list[str] = []
    if not paths.curriculum_source.is_file():
        missing.append("curriculum-source.md（关键课标证据缺失，无法验证 CUR 引用）")
    if not paths.learner_summary.is_file():
        missing.append("learner-summary.json（合成聚合学情缺失，无法生成学情侧证据）")
    return missing


def build_evidence_packet(paths: PipelinePaths) -> dict[str, Any]:
    """Build a READY packet, or a BLOCKED packet when Evidence inputs are missing.

    契约：课标或学情文件缺失/不可读时返回 status=BLOCKED 并逐项列出
    missing_items；文件存在但 JSON 非法或缺少 synthetic 标记时抛 E_DATA_QUALITY，
    不得误报为文件缺失。BLOCKED 产物不得进入修订与审计步骤。
    """

    missing = _missing_evidence_inputs(paths)
    learner_items: list[dict[str, Any]] = []
    learner_summary: dict[str, Any] | None = None
    fixture_date = "unknown"
    if paths.learner_summary.is_file():
        learner_summary = _read_json(paths.learner_summary)
        _require_synthetic(learner_summary)
        fixture_date = str(learner_summary.get("generated_at", "unknown"))
        if missing:
            # BLOCKED 时保留已能整理的学情条目备查（契约允许），
            # 但 status 必须为 BLOCKED，下游一律不得引用。
            learner_items = _learner_evidence(learner_summary, id_offset=98)

    if missing:
        return {
            "evidence_type": "fixture replay",
            "generator": "teachops-demo deterministic runner",
            "packet_id": "EP-missing-deterministic-001",
            "case": "missing-evidence-case",
            "status": "BLOCKED",
            "blocked_reason": "E_INPUT_MISSING",
            "generated_at": fixture_date,
            "evidence_items": learner_items,
            "missing_items": missing,
            "next_action": "补交缺失的 Evidence 输入文件后重跑；不得调用修订与审计步骤。",
        }

    # missing 为空 ⇒ 两个 Evidence 输入都存在且已解析为合法学情。
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
            "evidence_kind": "curriculum",
            "source_item_id": "CUR-02",
        },
        {
            "evidence_id": "EV-002",
            "source": "curriculum-source.md →《义务教育数学课程标准（2022年版）》",
            "locator": "CUR-01 课程理念",
            "summary": quote_for("CUR-01"),
            "quote_type": "原文摘录",
            "verify_status": "VERIFIED",
            "evidence_kind": "curriculum",
            "source_item_id": "CUR-01",
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


def _response_marker(
    rule_pack: dict[str, Any], evidence_id: str, source_item_id: str
) -> str:
    rule_by_id = {rule["rule_id"]: rule for rule in rule_pack.get("rules", [])}
    response_check = (rule_by_id.get("R-003") or {}).get("deterministic_check") or {}
    if response_check.get("type") != "response_marker":
        raise PipelineError("R-003 缺少 response_marker 确定性检查配置")
    try:
        return str(response_check["format"]).format(
            source_item_id=source_item_id,
            evidence_id=evidence_id,
        )
    except (KeyError, ValueError) as exc:
        raise PipelineError("R-003 response_marker format 无效") from exc


def revise_lesson(
    lesson_draft: Path, packet: dict[str, Any], rule_pack: dict[str, Any]
) -> str:
    """Apply the four evidence-backed changes to a complete lesson document."""

    if packet.get("status") != "READY":
        raise PipelineError("E_EVIDENCE_INSUFFICIENT：Evidence Packet 非 READY")
    evidence_by_id = {
        item["evidence_id"]: item for item in packet.get("evidence_items", [])
    }
    evidence_ids = set(evidence_by_id)
    if not {"EV-001", "EV-002", "EV-003", "EV-004"}.issubset(evidence_ids):
        raise PipelineError("E_EVIDENCE_INSUFFICIENT：缺少修订所需证据")
    misconception_evidence = next(
        item for item in packet["evidence_items"] if item["evidence_id"] == "EV-003"
    )
    misconception_id = str(misconception_evidence.get("source_item_id", "")).strip()
    if not misconception_id:
        raise PipelineError("E_EVIDENCE_INSUFFICIENT：EV-003 缺少 source_item_id")
    response_marker = _response_marker(
        rule_pack, misconception_evidence["evidence_id"], misconception_id
    )

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
            f"| 环节 3 认识几分之一与误解辨析 | 17 分钟 | 折出 1/4、1/8 并涂色；完成同分母比较；增加‘1/2 与 1/8 谁大’投票与同样大圆纸叠放辨析{response_marker} |",
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

    evidence_by_id = {
        item["evidence_id"]: item for item in packet.get("evidence_items", [])
    }
    evidence_ids = set(evidence_by_id)
    rule_by_id = {rule["rule_id"]: rule for rule in rule_pack.get("rules", [])}
    if set(rule_by_id) != {"R-001", "R-002", "R-003", "R-004", "R-005"}:
        raise PipelineError(f"规则包不符合演示契约：{sorted(rule_by_id)}")

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

    process_rows: list[dict[str, str]] = []
    for line in process_section.splitlines():
        if not re.match(r"^\|\s*环节", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3:
            raise PipelineError(f"教学过程表格列数错误：{line}")
        if cells[0] == "环节":
            continue
        process_rows.append(
            {"activity": cells[0], "duration": cells[1], "content": cells[2]}
        )

    def refs_in(text: str) -> set[str]:
        return set(re.findall(r"EV-\d{3}", text))

    goal_numbers = [int(number) for number, _ in goals]
    r1_pass = bool(goals) and len(goal_numbers) == len(set(goal_numbers)) and all(
        assessment_rows.get(int(number), "") not in {"", "—", "-"}
        for number, _ in goals
    )
    rationale_refs = [refs_in(item) for item in rationale_items]
    r2_missing = not rationale_items or any(not refs for refs in rationale_refs)
    r2_invalid = any(refs - evidence_ids for refs in rationale_refs)
    r2_result = "FAIL" if r2_missing else "WARN" if r2_invalid else "PASS"

    misconception_items = [
        (evidence_id, item)
        for evidence_id, item in evidence_by_id.items()
        if item.get("evidence_kind") == "learner_misconception"
    ]
    if len(misconception_items) != 1:
        raise PipelineError("Evidence Packet 必须包含一个最高频 learner_misconception")
    misconception_evidence_id, misconception_item = misconception_items[0]
    misconception_id = str(misconception_item.get("source_item_id", "")).strip()
    if not misconception_id:
        raise PipelineError("最高频误解证据缺少 source_item_id")
    response_marker = _response_marker(
        rule_pack, misconception_evidence_id, misconception_id
    )
    r3_pass = any(response_marker in row["content"] for row in process_rows)

    goal_ref_checks: list[tuple[set[str], set[str], bool]] = []
    for _, body in goals:
        curriculum_ids = set(re.findall(r"CUR-\d{2}", body))
        referenced_evidence = refs_in(body)
        mapping_valid = bool(curriculum_ids and referenced_evidence)
        mapping_valid = mapping_valid and not (referenced_evidence - evidence_ids)
        if mapping_valid:
            mapping_valid = all(
                any(
                    curriculum_id in str(evidence_by_id[evidence_id].get("locator", ""))
                    for evidence_id in referenced_evidence
                )
                for curriculum_id in curriculum_ids
            )
        goal_ref_checks.append((curriculum_ids, referenced_evidence, mapping_valid))
    r4_missing = not goals or any(not cur or not ev for cur, ev, _ in goal_ref_checks)
    r4_invalid = any(
        bool(ev - evidence_ids) or (cur and ev and not valid)
        for cur, ev, valid in goal_ref_checks
    )
    r4_result = "FAIL" if r4_missing else "WARN" if r4_invalid else "PASS"

    durations: list[int] = []
    invalid_duration_activities: list[str] = []
    for row in process_rows:
        match = re.fullmatch(r"(\d+)\s*分钟", row["duration"])
        if not match or int(match.group(1)) <= 0:
            invalid_duration_activities.append(row["activity"])
            continue
        durations.append(int(match.group(1)))
    total_minutes = sum(durations)
    max_total_minutes = (rule_by_id["R-005"].get("parameters") or {}).get(
        "max_total_minutes"
    )
    if not isinstance(max_total_minutes, int) or max_total_minutes <= 0:
        raise PipelineError("R-005 缺少合法 max_total_minutes")
    r5_pass = (
        bool(process_rows)
        and not invalid_duration_activities
        and len(durations) == len(process_rows)
        and total_minutes <= max_total_minutes
    )

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
            "result": r2_result,
            "location": "关键设计理由",
            "evidence_ids": sorted(refs_in(rationale_section)),
            "explanation": (
                "每条关键理由均引用有效 Evidence ID。"
                if r2_result == "PASS"
                else "存在不存在于 Evidence Packet 的引用。"
                if r2_result == "WARN"
                else "存在未引用 Evidence ID 的关键理由。"
            ),
            "suggestion": "" if r2_result == "PASS" else "补充有效证据，或删除无据断言。",
        },
        {
            "rule_id": "R-003",
            "result": "PASS" if r3_pass else "FAIL",
            "location": "教学过程",
            "evidence_ids": [misconception_evidence_id] if r3_pass else [],
            "explanation": f"已显式响应最高频误解 {misconception_id}。" if r3_pass else f"未发现响应最高频误解 {misconception_id} 的显式标记。",
            "suggestion": "" if r3_pass else f"增加活动并标记 {response_marker}。",
        },
        {
            "rule_id": "R-004",
            "result": r4_result,
            "location": "教学目标",
            "evidence_ids": sorted(refs_in(goals_section)),
            "explanation": (
                "每条目标均包含可验证的 CUR 与 EV 映射。"
                if r4_result == "PASS"
                else "存在悬空或不匹配的 CUR/EV 引用。"
                if r4_result == "WARN"
                else "存在未同时映射 CUR 与 EV 的目标。"
            ),
            "suggestion": "" if r4_result == "PASS" else "补齐并校验课程标准条目和 Evidence ID。",
        },
        {
            "rule_id": "R-005",
            "result": "PASS" if r5_pass else "WARN",
            "location": "教学过程总时长",
            "evidence_ids": [],
            "explanation": (
                f"共 {total_minutes} 分钟；上限为 {max_total_minutes} 分钟。"
                if not invalid_duration_activities
                else f"以下环节缺少合法时长：{', '.join(invalid_duration_activities)}。"
            ),
            "suggestion": "" if r5_pass else "补齐所有环节时长；若总时长超限，再压缩并重新审计。",
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


def apply_approval_condition(
    revised_lesson: str,
    decision: dict[str, Any],
    initial_audit: dict[str, Any],
) -> str:
    """Validate and apply an explicit approval decision to the audited candidate."""

    if not all(
        str(decision.get(field, "")).strip()
        for field in ("decision_id", "decided_by", "applies_to_report_id")
    ):
        raise PipelineError("审批决定缺少 decision_id/decided_by/applies_to_report_id")
    if decision.get("decision") != "APPROVE_WITH_CONDITION":
        raise PipelineError("审批决定不是 APPROVE_WITH_CONDITION")
    if decision.get("applies_to_report_id") != initial_audit.get("report_id"):
        raise PipelineError("审批决定引用的审计报告不匹配")
    r5 = next(item for item in initial_audit["findings"] if item["rule_id"] == "R-005")
    if initial_audit["overall"]["has_fail"] or r5["result"] != "WARN":
        raise PipelineError("当前审计状态不允许应用时长条件")

    condition = decision.get("condition") or {}
    if condition.get("action") != "SET_ACTIVITY_DURATION":
        raise PipelineError("不支持的审批条件 action")
    activity = str(condition.get("activity", "")).strip()
    minutes = condition.get("minutes")
    if not activity or not isinstance(minutes, int) or minutes <= 0:
        raise PipelineError("审批条件缺少合法 activity/minutes")

    row_pattern = re.compile(
        rf"^\|\s*{re.escape(activity)}\s*\|\s*(\d+)\s*分钟\s*\|",
        re.MULTILINE,
    )
    match = row_pattern.search(revised_lesson)
    if not match:
        raise PipelineError(f"审批条件目标环节不存在：{activity}")
    old_minutes = int(match.group(1))
    fixed = _replace_once(
        revised_lesson,
        f"| {activity} | {old_minutes} 分钟 |",
        f"| {activity} | {minutes} 分钟 |",
        f"审批条件：设置 {activity} 时长",
    )
    fixed = _replace_once(
        fixed,
        "# 教学设计候选修订稿：分数的初步认识（第 1 课时）",
        "# 教学设计最终稿：分数的初步认识（第 1 课时）",
        "最终稿标题",
    )
    return fixed.replace(
        "> 生成说明：",
        f"> 条件落实：依据审批决定 {decision['decision_id']}，将{activity}从 {old_minutes} 分钟调整为 {minutes} 分钟。\n>\n> 生成说明：",
        1,
    )


def run_normal_case(paths: PipelinePaths, output_dir: Path) -> dict[str, Any]:
    """Run READY -> revise -> audit -> condition -> re-audit."""

    if paths.approval_decision is None:
        raise PipelineError("正常闭环缺少显式 approval_decision 输入")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-run-", dir=output_dir.parent
    ) as temp_dir:
        stage = Path(temp_dir)
        packet = build_evidence_packet(paths)
        _write_json(stage / "evidence_packet.json", packet)
        if packet["status"] != "READY":
            raise PipelineError("正常样例意外进入 BLOCKED")

        rules = _read_json(paths.rule_pack)
        revised = revise_lesson(paths.lesson_draft, packet, rules)
        (stage / "revised-lesson.md").write_text(
            revised, encoding="utf-8", newline="\n"
        )
        initial_audit = audit_lesson(
            revised, packet, rules, report_id="AR-normal-deterministic-initial"
        )
        _write_json(stage / "audit_report.initial.json", initial_audit)

        decision = _read_json(paths.approval_decision)
        _write_json(stage / "approval_decision.json", decision)
        final_lesson = apply_approval_condition(revised, decision, initial_audit)
        (stage / "final-lesson.md").write_text(
            final_lesson, encoding="utf-8", newline="\n"
        )
        final_audit = audit_lesson(
            final_lesson, packet, rules, report_id="AR-normal-deterministic-final"
        )
        _write_json(stage / "audit_report.final.json", final_audit)
        if any(item["result"] != "PASS" for item in final_audit["findings"]):
            raise PipelineError("条件修正后的重新审计未全部通过")

        summary = {
            "evidence_type": "fixture replay",
            "generator": "teachops-demo deterministic runner",
            "case": "normal-case",
            "status": "COMPLETED",
            "approval_decision_id": decision["decision_id"],
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
                "approval_decision.json",
                "final-lesson.md",
                "audit_report.final.json",
            ],
        }
        _write_json(stage / "run_summary.json", summary)
        _publish_staged(
            stage, output_dir, [*summary["artifacts"], "run_summary.json"]
        )
        return summary


def run_blocked_case(paths: PipelinePaths, output_dir: Path) -> dict[str, Any]:
    """Run the missing-evidence case and prove downstream work is not produced."""

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-run-", dir=output_dir.parent
    ) as temp_dir:
        stage = Path(temp_dir)
        packet = build_evidence_packet(paths)
        _write_json(stage / "evidence_packet.json", packet)
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
        _write_json(stage / "run_summary.json", summary)
        _publish_staged(
            stage, output_dir, [*summary["artifacts"], "run_summary.json"]
        )
        return summary
