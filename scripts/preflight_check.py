# -*- coding: utf-8 -*-
"""提交前预检：扫描 git 跟踪文本、核对材料并运行确定性闭环测试。

用法：python scripts/preflight_check.py
退出码 0 = 通过；1 = 发现敏感内容、材料缺失或测试失败。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTERNS = [
    (r"sk-[A-Za-z0-9]{16,}", "OpenAI/DashScope 风格 Key"),
    (r"LTAI[A-Za-z0-9]{12,}", "阿里云 AccessKey ID"),
    (r"(?i)(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}", "凭据赋值"),
    (r"BEGIN[A-Z ]{0,20}PRIVATE KEY", "私钥文件内容"),
    (r"\b1[3-9]\d{9}\b", "疑似手机号"),
    (r"\b\d{17}[\dXx]\b", "疑似身份证号"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "邮箱地址"),
]

SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".pptx", ".docx", ".zip"}


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [f for f in out.splitlines() if f.strip()]


def main():
    problems = []
    hits = []
    for f in tracked_files():
        ext = os.path.splitext(f)[1].lower()
        if ext in SKIP_EXT:
            continue
        path = os.path.join(ROOT, f)
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for pat, label in PATTERNS:
            for m in re.finditer(pat, text):
                hits.append((f, label, m.group(0)[:24]))
                problems.append(f"{f}: 命中 {label}: {m.group(0)[:24]}...")

    # 关键材料状态
    intro = os.path.join(ROOT, "submission", "作品简介.txt")
    if os.path.exists(intro):
        n = len(open(intro, encoding="utf-8").read().strip())
        print(f"[check] 作品简介字符数（含标点）: {n} {'OK' if n <= 500 else '超限!'}")
        if n > 500:
            problems.append(f"作品简介 {n} 字符，超过 500")
    else:
        problems.append("缺少 submission/作品简介.txt")

    for rel in [
        "submission/TeachOps_GOAI_初赛方案.pptx",
        "submission/TeachOps_GOAI_初赛方案.pdf",
        "README.md",
        "LICENSE",
        "agents/manager.md",
        "skills/build-evidence-packet/contract.md",
        "demo/normal-case/input/lesson-draft.md",
        "demo/normal-case/input/approval-decision.json",
        "demo/normal-case/deterministic-output/revised-lesson.md",
        "demo/normal-case/deterministic-output/approval_decision.json",
        "demo/normal-case/deterministic-output/audit_report.final.json",
        "demo/missing-evidence-case/deterministic-output/evidence_packet.json",
        "src/teachops_demo/pipeline.py",
        "tests/test_pipeline.py",
    ]:
        ok = os.path.exists(os.path.join(ROOT, rel))
        print(f"[check] {rel}: {'存在' if ok else '缺失!'}")
        if not ok:
            problems.append(f"缺少 {rel}")

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(f"[check] 确定性闭环自动化测试: {'通过' if tests.returncode == 0 else '失败!'}")
    if tests.returncode != 0:
        problems.append("确定性闭环自动化测试失败")
        print(tests.stdout)
        print(tests.stderr)

    if hits:
        print("\n[scan] 敏感内容命中：")
        for f, label, frag in hits:
            print(f"  - {f} <- {label}: {frag}")
    else:
        print("\n[scan] 敏感内容扫描：0 命中")

    if problems:
        print("\n[结果] 未通过：")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("\n[结果] 预检通过")


if __name__ == "__main__":
    main()
