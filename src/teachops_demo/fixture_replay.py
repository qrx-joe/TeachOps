"""Replay and validate the fixed AgentTeams normal-case fixture.

This module never calls AgentTeams or an LLM. Its outputs must therefore remain
labelled ``fixture replay`` and must not be presented as live evidence.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


ARTIFACT_NAMES = (
    "evidence_packet.json",
    "revision.md",
    "audit_report.json",
    "review_decision.md",
)


class FixtureReplayError(ValueError):
    """Raised when a fixture cannot prove its provenance or cross-references."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureReplayError(f"无法读取有效 JSON：{path}") from exc
    if not isinstance(value, dict):
        raise FixtureReplayError(f"JSON 顶层必须是对象：{path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureReplayError(message)


def validate_normal_fixture(source_dir: Path) -> dict[str, Any]:
    """Validate provenance and references for the four normal-case artifacts."""

    missing = [name for name in ARTIFACT_NAMES if not (source_dir / name).is_file()]
    _require(not missing, f"fixture 缺少产物：{', '.join(missing)}")

    packet = _read_json(source_dir / "evidence_packet.json")
    revision = (source_dir / "revision.md").read_text(encoding="utf-8")
    audit = _read_json(source_dir / "audit_report.json")
    decision = (source_dir / "review_decision.md").read_text(encoding="utf-8")

    _require(packet.get("evidence_type") == "fixture replay", "证据包来源标记错误")
    _require(packet.get("status") == "READY", "正常样例证据包必须为 READY")
    evidence_ids = {
        item.get("evidence_id")
        for item in packet.get("evidence_items", [])
        if isinstance(item, dict) and item.get("evidence_id")
    }
    _require(bool(evidence_ids), "证据包必须包含 evidence_id")

    _require("evidence_type: fixture replay" in revision, "revision.md 来源标记错误")
    revision_refs = set(re.findall(r"EV-\d{3}", revision))
    _require(bool(revision_refs), "revision.md 必须引用 evidence_id")
    _require(revision_refs <= evidence_ids, "revision.md 引用了证据包外的 evidence_id")

    _require(audit.get("evidence_type") == "fixture replay", "审计报告来源标记错误")
    _require(audit.get("complete") is True, "正常样例审计报告必须完整")
    findings = audit.get("findings")
    _require(isinstance(findings, list) and bool(findings), "审计报告必须包含 findings")
    audit_refs = {
        evidence_id
        for finding in findings
        if isinstance(finding, dict)
        for evidence_id in finding.get("evidence_ids", [])
    }
    _require(audit_refs <= evidence_ids, "审计报告引用了证据包外的 evidence_id")
    _require(
        audit.get("overall", {}).get("needs_human_decision") is True,
        "正常样例必须保留人工审批边界",
    )

    _require("evidence_type: fixture replay" in decision, "审批记录来源标记错误")
    report_match = re.search(r"(?m)^report_id:\s*(\S+)\s*$", decision)
    _require(bool(report_match), "review_decision.md 缺少 report_id")
    _require(report_match.group(1) == audit.get("report_id"), "审批记录与审计报告不匹配")

    return {
        "evidence_type": "fixture replay",
        "case": packet.get("case"),
        "status": "REPLAY_VALIDATED",
        "artifacts": list(ARTIFACT_NAMES),
    }


def replay_normal_fixture(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Copy a validated fixture atomically without deleting unrelated files."""

    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    summary = validate_normal_fixture(source_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-fixture-", dir=output_dir.parent
    ) as temp_dir:
        stage = Path(temp_dir)
        for name in ARTIFACT_NAMES:
            shutil.copy2(source_dir / name, stage / name)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in ARTIFACT_NAMES:
            target = output_dir / name
            if target.exists() and not target.is_file():
                raise FixtureReplayError(f"目标不是普通文件，拒绝覆盖：{target}")
            os.replace(stage / name, target)

    summary.update(
        {
            "source_dir": str(source_dir),
            "output_dir": str(output_dir),
            "live_agentteams_run": False,
        }
    )
    return summary
