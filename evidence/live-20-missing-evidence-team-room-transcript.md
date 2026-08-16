# 缺证据 BLOCKED 链路 Team Room 协作记录（脱敏）

> 证据类型：live
> 原始运行：2026-08-16；结构化补跑：2026-08-16 17:13（Asia/Shanghai）
> 固定课例：小学三年级数学《分数的初步认识》
> case_id：`missing-evidence-case-live-20260816b`

本记录仅保留角色名、任务路径、状态字段和业务内容；未记录 API Key、密码、真实姓名、个人头像、房间 ID 或 Matrix 凭据。

## 原始房间运行

- 导师提交刻意缺少 `curriculum-source.md` 的任务。
- Evidence Worker 返回 `BLOCKED / E_INPUT_MISSING`、缺失清单和补证要求。
- Manager 停止，不调用 Design/Audit。
- 截图：`live-09-missing-evidence-blocked.png`；原始整理记录：`live-18-missing-evidence-original-room-record.md`。
- 当时 Worker 只在房间汇报，未落盘 JSON；这一缺口在原记录中已如实说明。

## 结构化补跑

1. Manager 分派 `teachops-evidence-003`。首次 Worker 通知失败；人工仅执行运行时同步补救，把 task-spec 和固定三个输入放入 `shared/tasks/teachops-evidence-003/`。
2. 第一次直接触发 Worker 时百炼返回 `403 Access to model denied`，未生成产物；该失败未标作成功。
3. 重试恢复后，Evidence Worker 同步 4 个文件（task-spec + 三个输入），确认 `curriculum-source.md` 缺失，生成并推送 `shared/tasks/teachops-evidence-003/evidence-packet.json`。
4. Manager 只读核验 JSON 后在 Matrix 房间记录停止：`status=BLOCKED`、`blocked_reason=E_INPUT_MISSING`；补交课标来源前不调用 teachops-design / teachops-audit。

独立停止记录：`live-22-missing-evidence-manager-stop.md`。

## 真实结构化产物

- `live-17-missing-evidence-packet.json`
- MinIO SHA-256：`c4a4c57597dc88e96826b8a3d5681a5c5e90679248bc52a3706c282a29a893a2`

## 证据边界

- `live-17` 是本次 AgentTeams live 补跑落盘的机器可读 BLOCKED 产物。
- `demo/missing-evidence-case/expected-output/` 与 `deterministic-output/` 是 fixture replay/确定性基线，不是本次 live 产物。
- 原始房间截图与结构化补跑共同证明：缺关键课标证据时流程被阻断，下游没有被调用。
