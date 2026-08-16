# 异常流程 live 记录（missing-evidence-case）

> 运行时间：2026-08-16（Asia/Shanghai）
> 环境：AgentTeams v1.1.2，teachops-manager + teachops-evidence（teachops-design / teachops-audit 在线但未被调用）
> 任务目录：`shared/tasks/teachops-evidence-002/`（刻意不含 curriculum-source.md，task-spec 明确禁止编造课标证据）
> 截图证据：`evidence/live-09-missing-evidence-blocked.png`

## 触发消息（Admin 发送）

> @teachops-evidence 异常流程任务已就位:shared/tasks/teachops-evidence-002/ 下有 task-spec.md 和三个输入文件,注意该目录刻意缺少 curriculum-source.md。请按 task-spec.md 核对必需输入,产出对应状态的 evidence-packet.json 并汇报。

## teachops-evidence 的回复（原文要点）

```
先执行文件同步，拉取最新任务文件。同步完成。现在检查任务文件。
任务目录 shared/tasks/teachops-evidence-002/ 存在，检查必需输入文件。
必需输入 curriculum-source.md（课程标准）缺失。
BLOCKED: E_INPUT_MISSING
缺失清单: curriculum-source.md（关键课标证据缺失）——初稿引用的
          CUR-01/CUR-02/CUR-03 均无来源支撑，无法验证。
补证要求: 补交课程标准来源文件后重新构建证据包。在此期间，保持
          BLOCKED 状态，Design/Audit 不被调用，不产出任何修订。
```

## Manager 确认

Manager 收到 BLOCKED 汇报后确认停止，未分派 teachops-design / teachops-audit，房间等待用户补证。

## 与 fixture 期望的对照

| 预期（`expected-output/evidence_packet.json`） | live 实际 | 一致性 |
| --- | --- | --- |
| status=BLOCKED | BLOCKED | ✅ |
| blocked_reason=E_INPUT_MISSING | E_INPUT_MISSING | ✅ |
| missing_items 含 curriculum-source.md 及 CUR-* 无法验证说明 | 同内容 | ✅ |
| next_action：补交后重建；期间 Design 不被调用 | 同语义 | ✅ |
| Manager 停止、不 @ Design Agent | Manager 确认停止，design/audit 未被调用 | ✅ |

## 完整性说明（如实标注）

- Worker 在房间中给出完整 BLOCKED 报告，但**未将 evidence-packet.json 写入共享存储**（后续要求补写也未落盘）；本记录由房间汇报原文整理，截图为原始证据。
- fixture 的 `expected-output/evidence_packet.json` 保留为该场景的结构化参考基线。

## 证据边界（评审提示）

- 本场景的 live 运行**未产出机器可读的 BLOCKED evidence-packet.json**（Worker 汇报后未写 MinIO）。因此本目录只有 `BLOCKED-record.md`，没有落盘的 live 包。
- 可核实的 live 依据：`evidence/live-09-missing-evidence-blocked.png`（截图）+ 本记录的房间汇报原文。
- 结构化基线（**非本次 live 落盘产物**，供对照与机器校验）：`demo/missing-evidence-case/expected-output/evidence_packet.json`（fixture）与 `demo/missing-evidence-case/deterministic-output/evidence_packet.json`（确定性实现，`status=BLOCKED` + `missing_items`）。
- 评审如需机器可读证据，应使用上述 fixture/确定性基线，并知悉其来自本地确定性实现而非本次 live 落盘。
