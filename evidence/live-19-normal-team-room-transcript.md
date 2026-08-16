# 正常链路 Team Room 协作记录（脱敏）

> 证据类型：live
> 运行日期：2026-08-16（Asia/Shanghai）
> 固定课例：小学三年级数学《分数的初步认识》
> 环境：AgentTeams v1.1.2 + qwen3.6-plus + 本机 Docker

本记录按房间截图与 MinIO 产物整理，仅保留角色名、任务路径和业务内容；未记录 API Key、密码、真实姓名、个人头像或 Matrix 凭据。

## 协作序列

1. Manager 核对四个固定输入并分派 Evidence 任务，目标路径为 `shared/tasks/teachops-evidence-001/evidence-packet.json`。截图：`live-05-normal-case-kickoff.png`。
2. 首次分派后 Worker 未看到任务文件；导师提示文件已在 MinIO，Manager 补发同步触发。这是实际运行故障，不是预设演示。截图：`live-06-task-file-blocked-report.png`。
3. Evidence Worker 同步输入，构建证据包并推送 MinIO；房间报告含 CUR-01~03、PK/M/O 学情项和 10 条 cross-map。截图：`live-07-design-worker-executing.png`。
4. Manager 继续分派 Design 与 Audit；对应真实产物为 `live-12` 至 `live-15`。
5. Audit 得到 R-001/002/004 PASS、R-003 FAIL、R-005 WARN。R-003 的准确含义是：教学内容已实质回应 M-01/M-02，但缺少规则要求的机器可验证响应标记。
6. 导师在房间作出“附条件批准”：实施前为环节三补入 M-01 响应标记；Manager 记录并分派最终修复。截图：`live-08-mentor-approval-decision.png`，审批记录：`live-16-normal-mentor-decision.md`。

## 输入一致性

2026-08-16 运行后复核确认：Manager 工作区的 `curriculum-source.md`、`lesson-draft.md`、`learner-summary.json`、`rule-pack.json` 与仓库 `demo/normal-case/input/` 对应文件 SHA-256 一致；`lesson-draft.md` 明确写明“三年级上册”。

## 证据边界

- 本记录和 `live-05` 至 `live-08` 为 AgentTeams Team Room 的 live 协作证据。
- `live-10` 至 `live-16` 为同次 live 运行的原始/脱敏产物与导师决定。
- `demo/normal-case/expected-output/`、`deterministic-output/` 和 `fixture-replay-output/` 仅作 fixture replay 对照，未作为本次 live 输入。

