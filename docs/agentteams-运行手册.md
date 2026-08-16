# AgentTeams 运行手册（步骤 7-10）

> 状态：2026-08-15 **步骤 7 烟雾测试已全部通过（live），步骤 8 团队配置已完成（四 Agent 在线）**；步骤 9/10 待运行，当前正常流程产物仍为 fixture replay。以下各节既是已执行记录，也是后续复现手册。
> 前置依赖（均为用户操作）：启动 Docker Desktop；安装 AgentTeams stable **v1.1.2**（官方仓库 github.com/agentscope-ai/AgentTeams）；在本机安装界面输入阿里云百炼 API Key。
> 安全红线：API Key 只在本机输入，不发聊天、不写仓库、不进截图（截图前遮挡 Key 与个人头像/用户名）。
> 安装注意：main 分支安装器与 v1.1.2 镜像存在环境变量前缀等版本错位，共五处修复，详见 `docs/agentteams-可用性核验.md` 第 3 节。

## 步骤 7 烟雾测试（时间盒 90 分钟）✅ 已通过（2026-08-15）

通过标准：Docker Server 正常 + AgentTeams 启动 + 本地 Element Web 打开 + Manager 回复一条最小消息 + 一个测试 Worker 收发任务成功 + Qwen 调用成功。

记录表（截图先存 `evidence/private/`，脱敏后移入 `evidence/` 并登记索引）：

| 检查项 | 结果 | 版本/说明 | 截图文件名 |
| --- | --- | --- | --- |
| Docker Server | ✅ | Docker Desktop 4.71.0，Engine 29.4.1 | 待归档 |
| AgentTeams 安装 | ✅ | v1.1.2 embedded（digest a3654ff6） | 待归档 |
| Element Web 打开 | ✅ | http://127.0.0.1:18088 | 待归档 |
| Manager 最小回复 | ✅ | 2026-08-15，"ready! 我已经准备就绪…" | 待归档 |
| 测试 Worker 收发 | ✅ | teachops-evidence（教学证据收集专员） | 待归档 |
| Qwen 最小调用 | ✅ | qwen3.6-plus @ 百炼接入点 | 待归档 |

**降级触发**：90 分钟未完成最小链路 → 停止排障，直接使用 `demo/*/expected-output/`（fixture replay）完成步骤 10 与 PPT，PPT 第 7/10 页标注"AgentTeams 集成未完成"。

~~本次已触发降级~~ **2026-08-15 更新：降级已解除**——补充安装与凭据后完成安装（含五处版本错位修复，见 `docs/agentteams-可用性核验.md`），烟雾测试六项全部通过。步骤 9/10 完成前，正常流程产物保持 fixture replay 标注。

## 步骤 8 正式团队配置（时间盒 90 分钟）✅ 已完成（2026-08-15）

创建 4 个角色并绑定 Identity 与 Skill：

| AgentTeams 角色 | 名称建议 | Identity 文件 | 挂载 Skill |
| --- | --- | --- | --- |
| Team Leader / Manager | teachops-manager | `agents/manager.md` | 无（只调度） |
| Worker #1 | teachops-evidence | `agents/evidence-agent.md` | build-evidence-packet |
| Worker #2 | teachops-design | `agents/design-agent.md` | revise-lesson-with-evidence |
| Worker #3 | teachops-audit | `agents/audit-agent.md` | audit-lesson-alignment |

- Team Room 名称：`TeachOps Demo Team`
- 上下文约定：消息只传**文件引用**（路径/链接）+ 不超过三行的状态；不在消息里粘贴长文。
- 验证：Manager 能分别 @ 三个 Worker；每个 Worker 能读到自己的 Identity 与 Skill 契约。
- 产出记录：团队配置截图、成员截图、角色-Skill 映射确认。

## 步骤 9 正常流程（时间盒 2 小时，**最多 2 轮**）✅ 已完成（2026-08-16，live）

给 Manager 的首条消息模板（引用文件而非粘贴正文）：

```text
请预审教学设计课例 normal-case：
- 课标来源：demo/normal-case/input/curriculum-source.md
- 教学设计初稿：demo/normal-case/input/lesson-draft.md
- 学情摘要：demo/normal-case/input/learner-summary.json
- 规则包：demo/normal-case/input/rule-pack.json
请按 Evidence → Design → Audit 流程处理，每步完成后汇报产物文件与状态。
```

> live 实测路径（2026-08-15 已验证）：课例输入已复制到 manager 工作区（宿主机 `C:\Users\<user>\agentteams-manager\teachops-demo\normal-case\`），消息中的文件路径使用容器内形式 `/root/manager-workspace/teachops-demo/normal-case/<文件名>`。`approval-decision.json` 为 fixture 预存决定，live 流程不喂给 Manager，审批由导师真实作出。

预期链路与核对点：

1. Manager 分派 Evidence → 产出 `evidence_packet.json`，status=READY（4 条 EV 证据）
2. Manager 转 Design → 产出 `revision.md`，关键建议带 evidence_id（对照 fixture：S-001..S-004）
3. Manager 转 Audit → 产出 `audit_report.json`，逐 rule_id 判定
4. Manager 请导师决定 → 用户回复批准/驳回（记录 review_decision）

**停止条件**：流程与边界正确即停止，不追求更好文案。第 2 轮结束仍不完整 → 冻结已获得的部分产物，其余用 fixture 补齐并如实标注。

**2026-08-16 执行结果（live，第 1 轮完成）**：四产物齐备并存于 `demo/normal-case/live-output/`——evidence-packet.json（CUR-01~03 + 10 条交叉映射）、lesson-revised.md + design-review-notes.md（四类问题修订清单）、audit-report.json（R-001/002/004 PASS，R-003 FAIL：M-01 错误模式未显式处理，R-005 WARN：40 分钟贴上限）、review-decision.md（导师附条件批准：M-01 处理环节实施前补入环节三）。live 审计比 fixture 判定更严格（R-003 FAIL），证明审计环节真实独立。执行过程中修复的协作链路问题（Worker 侧任务文件分发依赖 shared/tasks/ 目录与人工同步触发）记录于任务协作记录。

## 步骤 10 缺证据异常流程（时间盒 60 分钟）

AgentTeams 可用时，把消息模板中的目录换为 `demo/missing-evidence-case/input/`（其中没有 curriculum-source.md），预期：

1. Evidence Agent 返回 `status: BLOCKED` + missing_items
2. Manager 停止，不 @ Design Agent
3. 房间展示补证要求，等待用户补交

AgentTeams 不可用时：直接引用 `demo/missing-evidence-case/expected-output/evidence_packet.json`，PPT 与 README 标注 `fixture replay`，**不制作仿真的聊天截图**。

## 证据归档规则

- 真实运行产物/截图 → `evidence/live-XX-描述.{png,json,md}`，并在 `docs/运行证据索引.md` 登记（类型 live）
- 原始截图先入 `evidence/private/`（不入库），脱敏（遮挡用户名、头像、Key）后再移入 `evidence/`
- fixture 产物只引用 `demo/*/expected-output/`，不复制到 evidence 冒充 live
