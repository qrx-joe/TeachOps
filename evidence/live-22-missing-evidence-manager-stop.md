# Manager 停止记录（live）

> 记录时间：2026-08-16（Asia/Shanghai）
> case_id：`missing-evidence-case-live-20260816b`
> 来源：AgentTeams Manager 的 Matrix 绑定会话；已脱敏

## Manager 核验结果

| 项目 | 内容 |
| --- | --- |
| 产物路径 | `shared/tasks/teachops-evidence-003/evidence-packet.json`（MinIO） |
| 状态 | `BLOCKED` |
| 原因 | `E_INPUT_MISSING`：缺少 `curriculum-source.md`，无法提取 CUR-* 课标证据 |
| 补证要求 | 将 `curriculum-source.md` 补入任务目录后重新构建 Evidence Packet |
| Design | 未调用 |
| Audit | 未调用 |
| 下游状态 | 保持停止，直至 Evidence Packet 重建为非 BLOCKED 状态 |

## Manager 房间回复（脱敏原意）

> 核验通过。课标来源文件缺失，流程按 BLOCKED 停止；需补充 curriculum-source.md 后重建 Evidence Packet。已确认未调用 teachops-design 和 teachops-audit。

该记录与 `live-17-missing-evidence-packet.json`、`live-20-missing-evidence-team-room-transcript.md` 相互核对。fixture replay 未参与本次停止决定。

