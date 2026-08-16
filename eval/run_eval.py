"""首批评测集：对合成教学设计样例运行确定性审计并断言规则命中。

用法：uv run python eval/run_eval.py
退出码 0 = 全部样例符合预期；1 = 存在未达预期的样例。

说明：本评测集是验证材料（synthetic），不是 live 产物。证据包与规则包
复用 demo/normal-case/input/，样例只改变教学设计初稿内容。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teachops_demo.pipeline import PipelineError, PipelinePaths, audit_lesson, build_evidence_packet


BASE = """# 教学设计样例：分数的初步认识（第 1 课时）

- 学科/年级：小学数学，三年级上册
- 课题：分数的初步认识——认识几分之一
- 课时：1 课时（38 分钟）
- 设计者：TeachOps 评测集合成样例（synthetic）

## 一、教学目标

1. 结合分物情境初步认识几分之一，会读、写简单分数，知道分数各部分的名称（课标条目：CUR-02；证据：EV-001）。
2. 通过折纸、涂色等操作活动，直观理解几分之一的含义，能比较两个同分母分数的大小（课标条目：CUR-02；证据：EV-001）。
3. 能在小组内用分数的语言描述折纸结果，说清平均分与几分之一的含义（课标条目：CUR-02；证据：EV-001、EV-002）。

## 二、评价任务（目标—评价对应表）

| 教学目标 | 评价任务 |
| --- | --- |
| 目标 1 | 任务 A：课堂练习“看图写分数并读出来”（5 小题） |
| 目标 2 | 任务 B：折纸展示——折出一张纸的 1/2、1/4 并涂色，口头说明含义；比较 1/4 与 3/4 的大小 |
| 目标 3 | 任务 C：小组折纸汇报；按“说清平均分、说清几分之一”两条标准互评 |

## 三、教学过程

| 环节 | 时长 | 活动内容 |
| --- | --- | --- |
| 环节 1 情境导入 | 8 分钟 | 分月饼情境：4 块月饼平均分给 2 人、2 块平均分给 2 人、1 块平均分给 2 人，引出“一半”如何用数表示 |
| 环节 2 认识 1/2 | 12 分钟 | 折一张长方形纸表示它的 1/2 并涂色，交流不同折法；结合课标 CUR-02 介绍分数各部分名称与读写方法 |
| 环节 3 认识几分之一与误解辨析 | 15 分钟 | 折出 1/4、1/8 并涂色；完成同分母比较；增加“1/2 与 1/8 谁大”投票与同样大圆纸叠放辨析【响应学情 M-01；证据 EV-003】 |
| 环节 4 课堂小结 | 3 分钟 | 回顾分数的读写与各部分名称，布置课后练习 |

## 四、关键设计理由

1. 采用“分月饼”情境导入：平均分物是学生的已有经验，从认知冲突引出分数（课标条目：CUR-02；证据：EV-001）。
2. 环节 2 采用小组合作折纸：合成观察显示连续专注约 15-20 分钟，因此在第 12 分钟后安排动手操作维持参与（证据：EV-004；仅限本演示学情）。

## 五、说明

本样例为 TeachOps 首批评测集合成样例，用于验证规则命中率，不作为实际教学使用。
"""

ALL_PASS = {"R-001": "PASS", "R-002": "PASS", "R-003": "PASS", "R-004": "PASS", "R-005": "PASS"}


def s01(_): return BASE
def s02(t): return t.replace("任务 C：小组折纸汇报；按“说清平均分、说清几分之一”两条标准互评", "—")
def s03(t): return t.replace("从认知冲突引出分数（课标条目：CUR-02；证据：EV-001）", "从认知冲突引出分数（课标条目：CUR-02）")
def s04(t): return t.replace("【响应学情 M-01；证据 EV-003】", "")
def s05(t): return t.replace("知道分数各部分的名称（课标条目：CUR-02；证据：EV-001）", "知道分数各部分的名称")
def s06(t): return t.replace("| 环节 3 认识几分之一与误解辨析 | 15 分钟 |", "| 环节 3 认识几分之一与误解辨析 | 22 分钟 |")
def s07(t): return t.replace("| 环节 3 认识几分之一与误解辨析 | 15 分钟 |", "| 环节 3 认识几分之一与误解辨析 | 17 分钟 |")
def s08(t): return t.replace("任务 C：小组折纸汇报；按“说清平均分、说清几分之一”两条标准互评", "—").replace("（课标条目：CUR-02；证据：EV-001、EV-002）", "")
def s12(t): return t.replace("从认知冲突引出分数（课标条目：CUR-02；证据：EV-001）", "从认知冲突引出分数（课标条目：CUR-02；证据：EV-999）")
def s13(t): return t.replace("任务 B：折纸展示——折出一张纸的 1/2、1/4 并涂色，口头说明含义；比较 1/4 与 3/4 的大小", "—")
def s14(t): return t.replace("（证据：EV-004；仅限本演示学情）", "")
def s15(t): return t.replace("【响应学情 M-01；证据 EV-003】", "【响应学情 M-02；证据 EV-003】")
def s16(t): return t.replace("【响应学情 M-01；证据 EV-003】", "【响应学情 M-01；证据 EV-004】")
def s17(t): return t.replace("直观理解几分之一的含义，能比较两个同分母分数的大小（课标条目：CUR-02；证据：EV-001）", "直观理解几分之一的含义，能比较两个同分母分数的大小")
def s18(t): return t.replace("| 环节 3 认识几分之一与误解辨析 | 15 分钟 |", "| 环节 3 认识几分之一与误解辨析 | 18 分钟 |")
def s19(t): return t.replace("| 环节 3 认识几分之一与误解辨析 | 15 分钟 |", "| 环节 3 认识几分之一与误解辨析 | 27 分钟 |")

# kind=audit：用共享 READY 证据包审计教学设计；kind=evidence：验证证据阶段行为。
SAMPLES = [
    {"id": "S-01", "kind": "audit", "desc": "正常全通过（总时长 38 分钟）",
     "build": s01, "expected": ALL_PASS},
    {"id": "S-02", "kind": "audit", "desc": "目标 3 无评价任务 → R-001 FAIL",
     "build": s02, "expected": {**ALL_PASS, "R-001": "FAIL"}},
    {"id": "S-03", "kind": "audit", "desc": "关键理由 1 无证据引用 → R-002 FAIL",
     "build": s03, "expected": {**ALL_PASS, "R-002": "FAIL"}},
    {"id": "S-04", "kind": "audit", "desc": "未响应最高频误解 M-01 → R-003 FAIL",
     "build": s04, "expected": {**ALL_PASS, "R-003": "FAIL"}},
    {"id": "S-05", "kind": "audit", "desc": "目标 1 未映射课标条目 → R-004 FAIL",
     "build": s05, "expected": {**ALL_PASS, "R-004": "FAIL"}},
    {"id": "S-06", "kind": "audit", "desc": "总时长 45 分钟 → R-005 WARN",
     "build": s06, "expected": {**ALL_PASS, "R-005": "WARN"}},
    {"id": "S-07", "kind": "audit", "desc": "总时长恰 40 分钟 → R-005 PASS（边界）",
     "build": s07, "expected": ALL_PASS},
    {"id": "S-08", "kind": "audit", "desc": "目标 3 无任务且无课标映射 → R-001/R-004 FAIL",
     "build": s08, "expected": {**ALL_PASS, "R-001": "FAIL", "R-004": "FAIL"}},
    {"id": "S-12", "kind": "audit", "desc": "理由引用不存在的 EV-999 → R-002 WARN",
     "build": s12, "expected": {**ALL_PASS, "R-002": "WARN"}},
    {"id": "S-13", "kind": "audit", "desc": "目标 2 无评价任务 → R-001 FAIL（变体）",
     "build": s13, "expected": {**ALL_PASS, "R-001": "FAIL"}},
    {"id": "S-14", "kind": "audit", "desc": "关键理由 2 无证据引用 → R-002 FAIL（变体）",
     "build": s14, "expected": {**ALL_PASS, "R-002": "FAIL"}},
    {"id": "S-15", "kind": "audit", "desc": "响应标记误解 ID 错误 → R-003 FAIL（变体）",
     "build": s15, "expected": {**ALL_PASS, "R-003": "FAIL"}},
    {"id": "S-16", "kind": "audit", "desc": "响应标记证据 ID 错误 → R-003 FAIL（变体）",
     "build": s16, "expected": {**ALL_PASS, "R-003": "FAIL"}},
    {"id": "S-17", "kind": "audit", "desc": "目标 2 未映射课标条目 → R-004 FAIL（变体）",
     "build": s17, "expected": {**ALL_PASS, "R-004": "FAIL"}},
    {"id": "S-18", "kind": "audit", "desc": "总时长 41 分钟 → R-005 WARN（边界超）",
     "build": s18, "expected": {**ALL_PASS, "R-005": "WARN"}},
    {"id": "S-19", "kind": "audit", "desc": "总时长 50 分钟 → R-005 WARN（明显超）",
     "build": s19, "expected": {**ALL_PASS, "R-005": "WARN"}},
    {"id": "S-09", "kind": "evidence", "desc": "缺 curriculum-source.md → BLOCKED(E_INPUT_MISSING)",
     "expected_status": "BLOCKED"},
    {"id": "S-10", "kind": "evidence", "desc": "学情缺 synthetic 标记 → E_DATA_QUALITY",
     "expected_status": "E_DATA_QUALITY"},
]


def normal_paths() -> PipelinePaths:
    inp = ROOT / "demo" / "normal-case" / "input"
    return PipelinePaths(
        lesson_draft=inp / "lesson-draft.md",
        learner_summary=inp / "learner-summary.json",
        rule_pack=inp / "rule-pack.json",
        curriculum_source=inp / "curriculum-source.md",
    )


def run_audit(text: str, packet, rules, report_id: str) -> dict[str, str]:
    return {f["rule_id"]: f["result"] for f in audit_lesson(text, packet, rules, report_id=report_id)["findings"]}


def main() -> int:
    paths = normal_paths()
    rules = json.loads(paths.rule_pack.read_text(encoding="utf-8"))
    packet = build_evidence_packet(paths)
    if packet["status"] != "READY":
        print("S-00 基础证据包未就绪，不能作为审计基线"); return 1

    failures: list[str] = []
    for sample in SAMPLES:
        sid = sample["id"]
        if sample["kind"] == "audit":
            actual = run_audit(sample["build"](BASE), packet, rules, f"EVAL-{sid}")
            mismatch = {r: (actual.get(r), sample["expected"][r])
                        for r in sample["expected"] if actual.get(r) != sample["expected"][r]}
            if mismatch:
                failures.append(f"{sid} {sample['desc']}: {mismatch}")
                print(f"[FAIL] {sid}: {sample['desc']} {mismatch}")
            else:
                print(f"[PASS] {sid}: {sample['desc']}")
        elif sample["kind"] == "evidence":
            if sid == "S-09":
                p = PipelinePaths(lesson_draft=paths.lesson_draft, learner_summary=paths.learner_summary,
                                  rule_pack=paths.rule_pack, curriculum_source=ROOT / "eval" / "no-curriculum.md")
                pkt = build_evidence_packet(p)
                ok = pkt["status"] == "BLOCKED" and pkt.get("blocked_reason") == "E_INPUT_MISSING"
                print(f"[{'PASS' if ok else 'FAIL'}] {sid}: {sample['desc']} -> {pkt['status']}/{pkt.get('blocked_reason')}")
                if not ok: failures.append(sid)
            elif sid == "S-10":
                inp = ROOT / "demo" / "normal-case" / "input"
                import tempfile, dataclasses
                learner = json.loads(inp.joinpath("learner-summary.json").read_text(encoding="utf-8"))
                del learner["synthetic"]
                with tempfile.TemporaryDirectory() as td:
                    bad = Path(td) / "learner-summary.json"
                    bad.write_text(json.dumps(learner, ensure_ascii=False), encoding="utf-8")
                    p = PipelinePaths(lesson_draft=paths.lesson_draft, learner_summary=bad,
                                      rule_pack=paths.rule_pack, curriculum_source=paths.curriculum_source)
                    try:
                        build_evidence_packet(p)
                        ok = False
                    except PipelineError as exc:
                        ok = "E_DATA_QUALITY" in str(exc)
                    print(f"[{'PASS' if ok else 'FAIL'}] {sid}: {sample['desc']}")
                    if not ok: failures.append(sid)

    if failures:
        print("\n未通过：" + "; ".join(failures))
        return 1
    print("\n评测集全部通过（{} 条样例）".format(len(SAMPLES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
