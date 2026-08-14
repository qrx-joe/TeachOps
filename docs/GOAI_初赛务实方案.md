# 研序 TeachOps：GOAI 初赛务实方案

> 版本：V1.0  
> 日期：2026-08-13  
> 状态：初赛执行基线，尚未实施  
> 适用时间：2026-08-13 至 2026-08-16

## 1. 决策

初赛不建设完整 TeachOps 产品。我们提交一套清楚的方案材料，并争取跑通一条 AgentTeams 原生演示。

初赛需要证明三件事：

1. Evidence、Design 和 Audit 确实需要不同职责处理。
2. 教学修改建议能够引用公开课程依据。
3. 缺少关键证据时，系统会停止并要求人处理。

所有工作围绕这三点展开。Web 后台、数据库、完整状态机、RAG、MCP 和生产级观测移到复赛。

## 2. 官方要求

根据 [GOAI Agent Infra 赛道页面](https://goaihz.com/en/tracks?track=infra)：

- 初赛截止日期为 2026 年 8 月 16 日，准确截止时刻以登录后的提交页为准。
- 必交材料是 500 字以内作品简介和方案 PPT/PDF。
- 可执行 AgentTeams 代码包为可选材料。
- 方案需要至少 3 个职责不同的 Agent，并以 AgentTeams 作为协作设计基线。
- Skill 是必需项，需要说明输入输出、调用条件、失败处理、安全边界和复用价值。
- MCP、RAG、观测和推荐云组件不按数量评分。

初赛评审中，场景价值、多 Agent 闭环和 Skill 工程各占 25%，合计 75%。材料质量和方案完整度优先于功能数量。

## 3. 唯一场景

### 3.1 用户

首要用户是师范院校或教师培训机构的教学设计导师。

导师需要批量审阅结构相近的教学设计。他们会反复检查教学目标、活动、评价和课标依据，还要处理版本与反馈。通用大模型可以生成文本，但不会主动维护证据链、独立审计和人工确认边界。

### 3.2 固定课例

主 Demo 使用一个小学数学公开课例，例如“三年级数学：分数的初步认识”。正式制作时只选择一个课例，不并行准备多个学科。

输入材料：

- 一段有公开来源的课程标准。
- 一份存在可识别缺陷的初版教学设计。
- 一份明确标记为合成的聚合学情摘要。
- 三至五条可解释的教学设计检查规则。

输出材料：

- `evidence_packet.json`
- `revision.md`
- `audit_report.json`
- `review_decision.md`
- AgentTeams 协作记录与截图

### 3.3 正常流程

```text
用户提交课例
  -> Manager 拆解任务
  -> Evidence Agent 构建证据包
  -> Design Agent 生成带 Evidence ID 的修改建议
  -> Audit Agent 独立审计
  -> 用户批准或驳回
```

### 3.4 异常流程

异常样例删除一条关键课程依据：

1. Evidence Agent 列出缺失项并返回 `BLOCKED`。
2. Manager 不再调用 Design Agent。
3. AgentTeams 房间展示停止原因和补证要求。
4. 用户补充依据后才能重新运行。

这个分支用于证明系统能拒绝生成缺乏依据的完整答案。

## 4. Agent 分工

| 角色 | 职责 | 产出 | 禁止动作 |
| --- | --- | --- | --- |
| Manager | 接收任务、拆解步骤、传递文件引用、汇总状态、请求用户确认 | 任务计划、分派记录、最终摘要 | 编写教案、判断教学质量、自行批准 |
| Evidence Agent | 提取课标和学情中的可用证据，检查输入完整性 | `evidence_packet.json` | 生成完整教案、用模型常识补写来源 |
| Design Agent | 根据证据提出教学设计修改 | `revision.md` | 使用未引用的关键依据、发布正式版本 |
| Audit Agent | 独立检查证据覆盖和目标、活动、评价一致性 | `audit_report.json` | 修改教案、替用户批准 |

人类用户是流程中的审批者，不包装成第五个 Agent。

## 5. 三个 Skill

### 5.1 `build-evidence-packet`

用途：把课程标准和合成学情整理为可引用证据。

输入：

- 课标文件引用
- 学情摘要引用
- 课例元数据

输出：

- Evidence ID
- 来源、版本和原文位置
- 证据摘要
- 缺失项
- `READY` 或 `BLOCKED`

失败规则：缺少关键课标依据时返回 `BLOCKED`，不调用后续生成步骤。

### 5.2 `revise-lesson-with-evidence`

用途：生成带证据引用的修改建议。

输入：

- 初版教学设计
- Evidence Packet
- Rule Pack

输出：

- 问题位置
- 修改建议
- 修改理由
- 引用的 Evidence ID

失败规则：模型超时或输出结构错误时返回失败，不伪造成功结果。

### 5.3 `audit-lesson-alignment`

用途：独立检查教学设计质量和证据覆盖。

输入：

- 候选教学设计
- Evidence Packet
- Rule Pack

输出：

- `PASS`、`WARN`、`FAIL` 或 `NA`
- Rule ID
- Evidence ID
- 风险说明与处理建议

失败规则：存在无来源的关键结论或高风险失败项时，要求用户处理。

### 5.4 Skill 最低契约

每个 Skill 提供一个简短 manifest，包含：

- `skill_id` 与版本
- 用途和职责边界
- 输入输出 Schema
- 调用条件
- 文件、模型和网络权限
- 超时与错误
- 安全说明
- 一个正常样例和一个异常样例

## 6. AgentTeams 映射

AgentTeams 负责角色协作和人类可见的运行过程。TeachOps 初赛不开发第二套聊天界面。

| TeachOps 概念 | AgentTeams 映射 |
| --- | --- |
| Manager | Team Leader / Manager |
| Evidence、Design、Audit | 三个 Worker |
| 教研任务 | Team Room 中的一次固定任务 |
| 上下文传递 | 共享文件与文件引用 |
| 状态追踪 | 房间消息、Agent 状态和产物状态字段 |
| 人工审批 | 用户在 Team Room 中批准或驳回 |
| 执行证据 | 房间记录、产物文件、时间和截图 |

上下文能力选择：

1. 共享状态管理：各 Agent 读写同一组版本化产物。
2. 轨迹可观测性：保留房间记录、调用顺序、结果状态和耗时。

初赛不实现 RAG。公开课标以固定文件进入 Evidence Skill，减少检索质量和来源定位风险。

## 7. 最小仓库

```text
TeachOps/
├─ README.md
├─ LICENSE
├─ agents/
│  ├─ manager.md
│  ├─ evidence-agent.md
│  ├─ design-agent.md
│  └─ audit-agent.md
├─ skills/
│  ├─ build-evidence-packet/
│  ├─ revise-lesson-with-evidence/
│  └─ audit-lesson-alignment/
├─ demo/
│  ├─ normal-case/
│  │  ├─ input/
│  │  └─ expected-output/
│  └─ missing-evidence-case/
│     ├─ input/
│     └─ expected-output/
└─ docs/
   ├─ 作品简介.md
   └─ 初赛方案.pdf
```

如果 AgentTeams 需要专用配置文件，把配置放到 `agentteams/`。仓库不新增 Web、API 或数据库目录。

## 8. 初赛提交包

### 8.1 作品简介

控制在 500 个中文字符以内，包含：

- 教学设计预审场景和导师痛点。
- 四个 Agent 的闭环。
- 带 Evidence 引用的修改建议。
- 缺少依据时主动停止。
- 三个 Skill 和开源复用价值。
- 截止提交时已经完成的真实进展。

不写尚未取得的准确率、节省时间和真实用户效果。

### 8.2 10 页方案 PPT/PDF

| 页码 | 内容 | 评委需要看到的证据 |
| ---: | --- | --- |
| 1 | 项目定义 | 谁在什么任务中遇到什么问题 |
| 2 | 现有工作流 | 导师重复预审、证据与版本问题 |
| 3 | 固定课例 | 公开课标、初版教案、合成学情 |
| 4 | 端到端闭环 | 正常流程与人工确认 |
| 5 | Agent Identity | 职责、产出和禁止动作 |
| 6 | 三个 Skill | 输入输出、失败和复用 |
| 7 | AgentTeams 映射 | 角色、共享文件和状态追踪 |
| 8 | 异常分支 | 缺证据时停止的过程 |
| 9 | 开放与安全 | MIT、样例、凭据和数据边界 |
| 10 | 当前进展与复赛计划 | 已验证事实、限制、下一阶段 |

PPT 中的证据标记为：

- `live`：本次真实运行。
- `fixture replay`：固定输出回放。
- `design`：方案设计，尚未实现。

## 9. 三天安排

### 8 月 13 日：材料与契约

- 登录比赛系统，确认截止时刻和模板。
- 锁定一个课例和公开课标来源。
- 完成 500 字简介初稿和 10 页 PPT 文案。
- 写四个 Agent Identity 和三个 Skill contracts。
- 准备正常与缺证据两套输入、期望输出。

验收：即使代码未完成，也有一套可以提交的材料初稿。

### 8 月 14 日：AgentTeams 主流程

- 启动 Docker Desktop。
- 安装并验证 AgentTeams stable v1.1.2。
- 配置 Qwen API，但不把 Key 写入仓库。
- 创建 Manager 和三个 Workers。
- 跑通固定课例正常流程。

验收：Team Room 中能看到任务拆解、文件传递和三个不同产物。

### 8 月 15 日：异常与定稿

- 跑通缺证据异常流程。
- 整理 AgentTeams 截图和产物。
- 完成 README 和 MIT License。
- 把运行事实写入 PPT，删除无法证明的表述。
- 导出并检查 PDF。

验收：两项必交材料可以上传；仓库材料无凭据和未授权内容。

### 8 月 16 日：提交缓冲

- 从头复查简介、PDF、链接和文件大小。
- 上传材料并检查平台状态。
- 只处理提交阻塞问题，不增加功能。

## 10. 停止线与降级

### 10.1 AgentTeams 安装失败

AgentTeams 烟雾测试最多占用 90 分钟。超时后停止排障：

- 保留 AgentTeams 映射和 Agent Identity。
- 使用固定产物演示正常与异常流程。
- 所有截图标记为 `fixture replay` 或 `design`。
- 初赛材料按时提交，复赛再完成运行时接入。

### 10.2 Qwen 调用失败

- Evidence 和 Audit 使用可检查的固定规则与样例。
- Design 使用事先准备的 fixture。
- PPT 写明模型接入状态和失败原因。
- 不临时增加第二个模型平台。

### 10.3 时间不足

任务优先级固定为：

1. 作品简介和 PPT/PDF。
2. Agent Identity、Skill contracts 和样例。
3. 正常流程。
4. 缺证据异常流程。
5. README 和公开仓库。

任何可选工程工作都不能延误前两项。

## 11. 初赛验收

| 项目 | 通过标准 |
| --- | --- |
| 场景 | 只讲一个用户和一个课例 |
| Agent | 四个角色的输入、产出和禁止动作不同 |
| Skill | 三个 Skill 有契约、正常样例和异常样例 |
| 证据链 | 关键修改建议引用 Evidence ID |
| 异常 | 缺少关键证据时流程停止 |
| 人工控制 | 用户批准或驳回，Agent 不能自行结束正式流程 |
| AgentTeams | 有真实运行证据；没有则标记为设计或回放 |
| 安全 | API Key、个人数据和未授权内容不进入仓库或材料 |
| 提交 | 简介少于 500 字，PPT/PDF 可打开且链接有效 |

## 12. 复赛再做

进入复赛后，再根据官方反馈建设：

- 教研任务 Web 工作台。
- FastAPI 和 PostgreSQL。
- 正式任务状态机、Diff 与版本回滚。
- 权限、审计和 OpenTelemetry。
- MCP Adapter 或知识库 RAG。
- Playwright E2E 和固定评测集。
- 1 至 3 名导师或师范生的真实反馈。

这些能力属于复赛工程验证，不进入本次初赛完成标准。

