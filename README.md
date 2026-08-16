# 研序 TeachOps：多 Agent 教学设计预审与质量治理系统

> TeachOps 让 Evidence、Design 和 Audit Agent 围绕同一份教学设计协作，导师可以核对依据、处理风险并确认最终结果。
> GOAI 2026 Agent Infra 赛道初赛作品 · MIT License

## 1. 这是什么

面向**师范院校与教师培训导师**的教学设计预审系统。导师提交一份教学设计初稿和配套材料，多 Agent 团队完成"取证 → 修订 → 稽核"，每条修改建议都可回溯到证据条目；**关键证据缺失时流程主动阻断**，不生成"看似完整、实则无据"的结果。

初赛聚焦**单一场景**（教学设计预审）与**单一课例**（小学三年级数学《分数的初步认识》），演示两条链路：正常流程与缺证据异常流程。

## 2. 四个 Agent（`agents/`）

| 角色 | 职责 | 产出 | 关键禁止 |
| --- | --- | --- | --- |
| Manager | 拆解任务、调度、传递文件引用 | 任务计划、状态摘要 | 不判断教学质量、不自行批准 |
| Evidence Agent | 从课标与学情建证据包 | `evidence_packet.json` | 不写教案、不用模型记忆补写来源 |
| Design Agent | 依据证据修订设计 | `revision.md` | 不引用证据包之外的依据、不发布版本 |
| Audit Agent | 独立逐规则稽核 | `audit_report.json` | 不修改教案、不代用户批准 |

每个 Identity 含 purpose / inputs / outputs / allowed_actions / forbidden_actions / handoff_to / failure_behavior，见 `agents/*.md`。人类导师是审批者，不是第五个 Agent。

## 3. 三个 Skill（`skills/`）

| skill_id | 用途 | 失败契约要点 |
| --- | --- | --- |
| `build-evidence-packet` | 课标+学情 → 可引用证据包 | 关键证据缺失即 `BLOCKED`，阻断下游 |
| `revise-lesson-with-evidence` | 初稿+证据包+规则 → 修订建议 | 包非 READY 拒绝执行；无据建议进"待补证"区 |
| `audit-lesson-alignment` | 候选设计+证据包+规则 → 审计报告 | 判定绑定 rule_id+evidence_id；输入不全不给结论 |

每个契约含输入输出 JSON Schema、调用条件、权限、超时、错误码、安全说明与正反样例，见 `skills/*/contract.md`。Skill 与 Agent 解耦，可单独测试、跨学科复用。

## 4. Demo 样例（`demo/`）

```text
demo/
├─ 样例说明.md                     # 植入缺陷、合成标记、预期行为对照
├─ normal-case/
│  ├─ input/                       # 课标 + 初稿 + 学情 + 规则包 + 审批条件
│  └─ expected-output/             # fixture replay：两步产物 + 审批样例
└─ missing-evidence-case/
   ├─ input/                       # 仅缺 curriculum-source.md
   └─ expected-output/             # fixture replay：BLOCKED 证据包
```

- 正常样例：初稿含 3 个植入缺陷（目标缺评价任务、高频误解未处理、设计理由无引用），期望链路 READY → 修订（引用 EV 编号）→ 审计（R-005 时长 WARN 转导师裁量）→ 附条件批准。
- 异常样例：缺关键课标证据 → `BLOCKED` + 缺失清单，Design Agent 不被调用。
- 合规：学情为合成数据（`synthetic: true`）；课标仅短引用并附教育部官方链接（教材〔2022〕2 号），不分发全文。

## 5. 运行方式与证据类型

### 当前结论（2026-08-16 更新）

- `live` 环境核验：Docker Desktop 4.71.0、Engine 29.4.1 可用。
- AgentTeams 烟雾测试：**已通过（live，2026-08-15）**。AgentTeams stable v1.1.2 完成本机安装（含 main 安装器与 v1.1.2 镜像之间五处版本错位的修复，见核验文档），烟雾测试六项——Docker、容器健康、Element Web 登录、Manager 回复、Worker 收发、Qwen 调用——全部真实通过；正式团队（manager/evidence/design/audit 四 Agent）在线。
- **正常流程已 live 完成（2026-08-16）**：四 Agent 在 Element Web 房间真实协作，产出证据包 → 修订稿+修订说明 → 审计报告（R-003 FAIL/R-005 WARN 的真实发现）→ 导师附条件批准（真人决定），四产物存 `demo/normal-case/live-output/`（登记于运行证据索引第 14 项）。
- **异常流程已 live 完成并补齐机器可读产物（2026-08-16）**：缺课标输入下 teachops-evidence 返回 `BLOCKED / E_INPUT_MISSING`，真实落盘 `evidence/live-17-missing-evidence-packet.json`；Manager 核验后停止并确认 design/audit 未调用。原始房间截图见 `evidence/live-09-missing-evidence-blocked.png`，脱敏协作与重试记录见 `evidence/live-20-missing-evidence-team-room-transcript.md`。
- 证据边界：`evidence/live-*` 与 `demo/*/live-output/` 是已登记 live 证据；`expected-output/`、`deterministic-output/`、`fixture-replay-output/` 仅为 fixture replay/确定性对照。全部状态以 [`docs/运行证据索引.md`](docs/运行证据索引.md) 为唯一事实源，不因历史成功记录而声称当前外部模型服务持续在线。

详细命令与证据边界见 [`docs/agentteams-可用性核验.md`](docs/agentteams-可用性核验.md) 与 [`docs/运行证据索引.md`](docs/运行证据索引.md)。

### 最小正常流程：fixture replay

以下命令校验四个 fixture 的来源标记、Evidence ID 引用、审计与人工审批关联，然后只产出四个指定文件：

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python scripts/replay_fixture.py
```

默认输出目录：`demo/normal-case/fixture-replay-output/`

- `evidence_packet.json`
- `revision.md`
- `audit_report.json`
- `review_decision.md`

命令输出中的 `evidence_type` 必须为 `fixture replay`，`live_agentteams_run` 必须为 `false`。若任何 fixture 被误标为 `live`、引用不存在的 Evidence ID，或审批记录未绑定本次审计报告，命令会失败。

### 本地确定性闭环

仓库包含一个不依赖模型、仅使用 Python 标准库的最小可运行闭环。它读取固定课例输入并执行：

`Evidence → revised-lesson.md → 首轮审计 → 读取显式 approval-decision.json → final-lesson.md → 重新审计`

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python scripts/run_demo.py normal
uv run python scripts/run_demo.py missing-evidence
uv run python -m unittest discover -s tests -v
```

- 正常路径输入另含 `approval-decision.json`；产物位于 `demo/normal-case/deterministic-output/`。首轮总时长 45 分钟，R-005 为 WARN；只有审批决定与首轮报告匹配时才应用“环节 4 调整为 3 分钟”，重新审计为 40 分钟且五条规则全部 PASS。
- 缺证据路径产物：`demo/missing-evidence-case/deterministic-output/`；流程在 Evidence 阶段返回 BLOCKED，不生成修订稿或审计报告。
- 这些结果属于可复现的 `fixture replay`，证明本地确定性逻辑可运行；不等同于 AgentTeams、模型网关或真实用户环境的 `live` 证据。
- 审计器验证结构化约束、有效 EV/CUR 引用、显式学情响应标记和时长字段，不代替导师对教学内容质量的语义判断。

### AgentTeams 协作运行

初赛协作运行时使用 [AgentTeams](https://github.com/agentscope-ai/AgentTeams) stable v1.1.2（Docker Desktop 环境）：

1. 启动 Docker Desktop，安装 AgentTeams v1.1.2，打开本地 Element Web
2. 在本机安装界面配置阿里云百炼（Qwen）API Key
3. 按 `docs/agentteams-运行手册.md` 步骤 8 创建 Manager + 三个 Worker，绑定 `agents/` Identity 与 `skills/` 契约
4. 按手册步骤 9/10 的消息模板运行两条流程

**所有材料区分三类证据类型**（见 `docs/运行证据索引.md`）：

- `live`：本次真实运行
- `fixture replay`：`demo/*/expected-output/` 中的固定期望输出回放
- `design`：方案设计，尚未实现

当前仓库中 Agent Identity、Skill 契约与输入样例属于 design，`expected-output/`、`deterministic-output/`、`fixture-replay-output/` 属于 fixture replay/确定性对照；烟雾测试、团队配置、正常流程（真实产物 + 导师审批）与异常流程（机器可读 BLOCKED + Manager 停止）均已 live 完成并登记于[运行证据索引](docs/运行证据索引.md)（2026-08-15/16）。

### API Key 安全

- Key 只存本机（`.env` 或 AgentTeams 网关配置），`.env` 已被 `.gitignore` 排除
- Key 不进入聊天记录、Git、日志、截图与 PPT

## 6. 仓库结构

```text
├─ agents/          # 四个 Agent Identity
├─ skills/          # 三个 Skill contracts（含 JSON Schema 与正反样例）
├─ demo/            # 正常 + 缺证据两套输入与期望输出
├─ eval/            # 评测集与可复现评测 harness（18 条合成样例，见 eval/README.md）
├─ src/             # 本地确定性 Evidence / 修订 / 审计流水线
├─ tests/           # 正常与 BLOCKED 路径自动化测试
├─ scripts/         # CLI、PPT/PDF 与提交预检脚本
├─ evidence/        # live 运行证据（运行后生成，见索引）
├─ submission/      # 作品简介、PPT 文案与提交核对材料
└─ docs/            # 定位、方案、运行手册、证据索引
```

截图与产物如何命名、脱敏和留存，见 [`docs/截图与产物留存清单.md`](docs/截图与产物留存清单.md)。

持续协作与工程规范入口：

- [`docs/任务与协作记录.md`](docs/任务与协作记录.md)：Question、To do、Next to do、人与 AI 的关键协作决定、建议、不确定性与遗漏项。
- [`docs/技术选型与工程规范.md`](docs/技术选型与工程规范.md)：当前实现与目标架构边界、同类框架参考、行业规范、扩展维护、测试和详细注释规则。
- 研序 TeachOps 技术实施与工程规范 V1.1（内部 docx，未随公开仓库分发）：完整目标架构与工程规范正文；其中未落地部分仍属于 `design`。

## 7. 初赛不做（复赛计划）

Web 工作台、FastAPI + PostgreSQL、用户与权限体系、RAG / 向量库 / MCP Server、版本 Diff 与正式回滚、多课例批量任务。这些在方案文档中均为复赛设计，初赛材料不以"已实现"表述。

## 8. License

[MIT](LICENSE)。开放 Agent Identity、Skill 契约、固定样例与文档；不包含任何 API Key、个人数据或未授权第三方内容。
