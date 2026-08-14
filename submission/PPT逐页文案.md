# 初赛方案 PPT 逐页文案（10 页）

> 步骤 6 产出。制作 PPT 时逐页照搬结论句作为页面主标题下方的"结论行"。
> 证据类型标注规则：`live`（本次真实运行）/ `fixture replay`（固定输出回放）/ `design`（方案设计，尚未实现）。截图占位处不得放模拟终端图。
> 页眉：研序 TeachOps；页脚：GOAI 2026 · Agent Infra。
> 若官方页数限制少于 10 页的压缩顺序：P2 并入 P1（留结论），P9 并入 P10；其余页保留。

## P1 项目定义

**结论行：教学设计预审从"凭经验改"变成"证据可回溯、缺据即阻断"的多 Agent 流程。**

- 全称：研序 TeachOps：多 Agent 教学设计预审与质量治理系统
- 一句话定位：TeachOps 让 Evidence、Design 和 Audit Agent 围绕同一份教学设计协作，导师可以核对依据、处理风险并确认最终结果
- 用户：师范院校 / 教师培训导师；任务：教学设计预审
- 100 字问题：初稿常缺课标依据、目标与评价脱节、学情回应不足，人工预审重复且口径不一

证据：`docs/项目定位.md`（design）。视觉：定位句大字 + "用户 / 任务 / 作用"三行卡。

## P2 教学设计预审场景

**结论行：导师在 Word、聊天和通用大模型之间来回，四类问题反复出现。**

- 痛点 1：导师反复检查相同的基础缺陷
- 痛点 2：AI 建议没有可核对的课程依据
- 痛点 3：修改前后差异与责任记录难以追踪
- 痛点 4：证据不足时，通用工具仍生成"看似完整"的答案
- 缺口：通用大模型不维护证据链、不做独立审计、无人工确认边界

证据：预审流程对比图（design）。

## P3 固定课例和输入

**结论行：一个三年级数学课例、四件套输入，全部材料可公开。**

- 课例：小学三年级数学《分数的初步认识》（第 1 课时）
- 输入 1：课程标准来源——教育部 2022 年版课标短引用 + 官方链接（教材〔2022〕2 号）
- 输入 2：初版教学设计（团队原创，含 3 个植入的可审计缺陷）
- 输入 3：聚合学情摘要（`synthetic: true`，无任何学生个人信息）
- 输入 4：规则包（5 条检查规则，独立于课标）

证据：`demo/` 目录与文件截图（design）。

## P4 端到端闭环

**结论行：证据 → 修订 → 稽核 → 人工批准，一条流水线四道关卡。**

- 流程：提交 → Manager 拆解 → Evidence 建包（READY）→ Design 修订（引用 evidence_id）→ Audit 稽核（逐规则判定）→ 导师批准 / 驳回
- 三个产物：`evidence_packet.json`、`revision.md`、`audit_report.json` + 导师 `review_decision.md`
- 人工边界：正式通过只能由导师点击，Agent 无发布权

证据：状态流程图（design）。
截图占位：【live：AgentTeams Team Room 协作记录——步骤 9 运行后补】

## P5 四个 Agent Identity

**结论行：四个角色职责互斥，禁止动作写进 Identity，可逐条检查。**

| 角色 | 职责 | 产出 | 关键禁止 |
| --- | --- | --- | --- |
| Manager | 拆解、调度、传引用 | 任务计划、状态摘要 | 不判断教学质量、不自行批准 |
| Evidence | 建证据包、列缺失项 | evidence_packet.json | 不写教案、不补写来源 |
| Design | 依据证据修订 | revision.md | 不引用包外依据、不发布版本 |
| Audit | 独立逐规则稽核 | audit_report.json | 不修改教案、不代用户批准 |

证据：`agents/*.md` 四份 Identity（design；接入 AgentTeams 后配置为 live）。

## P6 三个 Skill

**结论行：每个 Skill 有契约、有失败样例、可脱离 Agent 单独测试。**

| skill_id | 输入 → 输出 | 失败契约要点 |
| --- | --- | --- |
| build-evidence-packet | 课标来源 + 学情 → evidence_packet.json | 关键证据缺失即 BLOCKED，不建 READY 包 |
| revise-lesson-with-evidence | 初稿 + READY 包 + 规则 → revision.md | 包 BLOCKED 拒绝执行；建议无据入"待补证"区 |
| audit-lesson-alignment | 候选设计 + 包 + 规则 → audit_report.json | 判定绑定 rule_id + evidence_id；输入不全不给结论 |

证据：`skills/*/contract.md`（design）。

## P7 AgentTeams 映射

**结论行：Manager + 三个 Worker 落在 AgentTeams Team Room，上下文只传文件引用和短状态。**

| TeachOps 概念 | AgentTeams 映射 |
| --- | --- |
| Manager | Team Leader / Manager |
| Evidence / Design / Audit | 三个 Worker（各挂载对应 Skill） |
| 教研任务 | Team Room 中的固定任务 |
| 上下文传递 | 共享文件 + 文件引用（不复制长文） |
| 状态追踪 | 房间消息、Agent 状态、产物状态字段 |
| 人工审批 | 用户在 Team Room 中批准 / 驳回 |

证据：映射表（design）。
截图占位：【live：团队配置与房间成员——步骤 8 完成后补】

## P8 缺证据异常分支

**结论行：缺关键课标证据 → BLOCKED → 不生成修订 → 导师收到补证清单。**

- 样例：missing-evidence-case（仅删除 curriculum-source.md）
- Evidence Agent 返回 `status: BLOCKED` + `missing_items`
- Manager 停止调用 Design Agent，房间展示停止原因
- 不用模型记忆补写来源，不把部分执行显示成成功

证据：
截图占位：【live：BLOCKED 运行记录——步骤 10 运行后补；未跑通时用 `demo/missing-evidence-case/expected-output/evidence_packet.json` 并标注 fixture replay】

## P9 开放与安全边界

**结论行：MIT 开源四类资产，四条安全边界贯穿全部材料。**

- 开源范围：Agent Identity、Skill 契约（含 JSON Schema）、固定课例样例、README 与运行证据索引
- 边界 1：API Key 只存本机，不进聊天、仓库、截图和 PPT
- 边界 2：学情为合成聚合数据，无学生个人信息
- 边界 3：课标仅短引用 + 官方链接，不分发全文
- 边界 4：批准 / 驳回权在人类导师，Agent 不能自行结束流程

证据：`LICENSE`、`README.md`、`.gitignore`（design）。

## P10 当前进展、限制和复赛计划

**结论行：初赛交付材料齐备，未做的事项明确列出，复赛路线可检验。**

- 已完成：四个 Agent Identity、三个 Skill 契约、两套固定样例、500 字简介、本 PPT（制作时按当时实际状态更新）
- AgentTeams 运行状态：制作时按实际填写（live 已跑通两条链路 / 未跑通则写"集成未完成，材料以 fixture 与 design 呈现"）
- 限制：无真实导师 / 学生数据；单一课例；AgentTeams 未在本机长期验证
- 复赛计划：Web 工作台、FastAPI + PostgreSQL、版本 Diff 与回滚、知识库 RAG / MCP Adapter、真实导师反馈（1-3 人）

证据：仓库目录树（design）+ 运行证据索引（live/fixture 混合，制作时以索引为准）。
