# AgentTeams live 执行指引（LIVE-001 / LIVE-002）

> 状态：2026-08-16 环境已就绪；契约化 task-spec 已写入 manager 工作区
> `C:\Users\14536\agentteams-manager\agentteams\agentteams-storage\shared\`（仓库外，不入 Git）。
> 本文件是 live 运行的仓库侧执行卡：正式契约以 `skills/*/contract.md` 为准，本页只提供可复现的操作步骤与消息模板。

## 0. 前置核对（已完成，只读核验 2026-08-16）

- Docker/AgentTeams 五容器全部 Up；Element Web `http://127.0.0.1:18088` 返回 200。
- manager 工作区输入与仓库字节一致（SHA256 全匹配）：
  - `C:\Users\14536\agentteams-manager\teachops-demo\normal-case\`（含 curriculum-source.md）
  - `C:\Users\14536\agentteams-manager\teachops-demo\missing-evidence-case\`（**刻意无 curriculum-source.md**）
- 已重写/新增契约化 task-spec：`shared/tasks/teachops-evidence-001/task-spec.md`、`teachops-design-001/task-spec.md`、`teachops-audit-001/task-spec.md`，及项目计划 `shared/projects/proj-teachops-normal-case/plan.md`。

## 1. LIVE-001 正常流程（AgentTeams 运行手册步骤 9）

在 Element Web Team Room 中把下面消息发给 Manager（文件路径用容器内形式 `/root/manager-workspace/...`）：

```text
请预审教学设计课例 normal-case，并严格遵循已分发的契约化 task-spec 与仓库 Skill Contract 产出契约化产物：
- 课标来源：/root/manager-workspace/teachops-demo/normal-case/curriculum-source.md
- 教学设计初稿：/root/manager-workspace/teachops-demo/normal-case/lesson-draft.md
- 学情摘要：/root/manager-workspace/teachops-demo/normal-case/learner-summary.json
- 规则包：/root/manager-workspace/teachops-demo/normal-case/rule-pack.json
请按 Evidence → Design → Audit 流程处理；每步完成后汇报产物文件路径与状态。
产物必须为：evidence_packet.json（status=READY，EV-001..EV-004）、revision.md（每条建议带 evidence_id）、audit_report.json（每条判定带 rule_id + evidence_id）。
Audit 完成后，把 WARN/FAIL 与产物引用转交给我（导师），由我作出决定，不要自行批准。
```

## 2. LIVE-002 缺证据异常流程（步骤 10）

同一 Team Room，换课例并只跑 Evidence 阶段：

```text
请用缺证据课例 missing-evidence-case 运行一次证据阶段（只跑 Evidence，不调用 Design/Audit）：
- 课标来源：/root/manager-workspace/teachops-demo/missing-evidence-case/curriculum-source.md（注意：该文件缺失）
- 教学设计初稿：/root/manager-workspace/teachops-demo/missing-evidence-case/lesson-draft.md
- 学情摘要：/root/manager-workspace/teachops-demo/missing-evidence-case/learner-summary.json
- 规则包：/root/manager-workspace/teachops-demo/missing-evidence-case/rule-pack.json
课标缺失时：输出 status=BLOCKED 的 evidence_packet.json + missing_items，然后停止，不得产出修订稿或审计报告。
请汇报：缺什么、为什么停止、补证后如何重跑。
```

## 3. 证据留存与归档清单（live 产物产生后执行）

| 项 | 位置 | 状态 |
| --- | --- | --- |
| Team Room 四 Agent 成员/角色配置截图 | `evidence/private/`（脱敏后移入 `evidence/`） | 待截图 |
| Manager 任务拆解与分派记录 | 截图 或 房间消息记录 | 待运行 |
| Evidence/Design/Audit 消息轨迹 | 截图（脱敏） | 待运行 |
| `evidence_packet.json` / `revision.md` / `audit_report.json`（live 产物） | 复制到 `evidence/live-XX-*` | 待运行 |
| 人工审批决定 + 绑定 `report_id` | `evidence/` | 待运行 |
| 运行时间、模型别名、结果状态、失败/重试说明 | 写入 `docs/运行证据索引.md` L4/L5 | 待运行 |

## 4. 停止线（live 证据不得伪造）

- Evidence Packet 为 BLOCKED 时不得继续调用 Design。
- Evidence ID 不可验证时不得把审计标为全 PASS。
- AgentTeams 或模型失败时保留已完成步骤并标记失败，不用 fixture 补齐 live 产物。
- 不在消息、截图、产物或 Git 中保存 API Key、Cookie、账号信息或真实学生数据。
