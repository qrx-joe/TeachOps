# `gemma4-learning-agent` 借鉴分析

> 文档类型：外部项目源码审查与 TeachOps 决策参考
> 审查日期：2026-08-15
> 目标仓库：[qianmo123321/gemma4-learning-agent](https://github.com/qianmo123321/gemma4-learning-agent)
> 审查版本：[`60e10f4028cb15bcc127e6ac8a2924c802bf8aef`](https://github.com/qianmo123321/gemma4-learning-agent/tree/60e10f4028cb15bcc127e6ac8a2924c802bf8aef)，提交日期 2026-07-29

## 1. 审查目的与证据边界

本次审查用于判断该项目有哪些设计可供 TeachOps 借鉴，不包含功能迁移或技术栈替换。

审查依据包括目标仓库的 README、FastAPI 后端、前端、RAG、SQLite、LoRA 数据导出与部署脚本。审查过程没有启动对方的 vLLM、Web 服务或训练任务，因此本文只能确认代码结构，不能确认运行效果、模型质量或部署稳定性。

TeachOps 的比较基线为当前初赛 MVP：固定课例、Evidence → Design → Audit 流程、缺证据阻断、人工审批、确定性回放和自动化测试。TeachOps 当前没有 AgentTeams 正常流程的 live 运行证据，详见 [`README.md`](../README.md) 和 [`agentteams-可用性核验.md`](agentteams-可用性核验.md)。

## 2. 结论

TeachOps 可以学习该项目的产品闭环、运行记录和反馈数据设计。Gemma4、RAG、LoRA 与通用聊天界面不应进入当前初赛范围。

对方项目将前端、模型服务、知识检索、会话存储和反馈导出连成一条可操作链路。TeachOps 在治理契约、证据阻断、角色隔离和人工审批方面更完整。两边解决的问题不同，适合互补，不适合整体迁移。

## 3. 对方项目的代码事实

| 模块 | 已发现的实现 | 证据 |
| --- | --- | --- |
| Web 与 API | 支持会话创建、历史读取、知识上传、聊天、导出和回答反馈 | [`main.py`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/backend/app/main.py) |
| 模型调用 | 通过 OpenAI-compatible vLLM 或 Ollama 调用模型，四种模式由不同 prompt 驱动 | [`providers.py`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/backend/app/providers.py) |
| 运行记录 | SQLite 保存会话、消息、RAG 片段、模型名称、评分和训练选择 | [`conversation_store.py`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/backend/app/conversation_store.py) |
| RAG | 使用 word/char TF-IDF 混合得分检索 Markdown、TXT 和 CSV | [`rag.py`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/backend/app/rag.py) |
| 数据闭环 | 用户评分并勾选训练样本，脚本导出 messages JSONL | [`build_lora_dataset_v1.py`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/backend/build_lora_dataset_v1.py) |
| LoRA 冷启动数据 | 仓库包含 300 条覆盖问答、学习路径、出题、陪练和纠错的数据 | [`数据说明`](https://github.com/qianmo123321/gemma4-learning-agent/blob/60e10f4028cb15bcc127e6ac8a2924c802bf8aef/app/data/lora_data/lora_train_300_v1/README.md) |

## 4. TeachOps 值得学习的部分

### 4.1 保存完整运行记录

对方项目把消息、证据、模型和用户反馈保存到同一条会话记录。TeachOps 后续可以把这些字段映射到任务运行记录。

建议记录以下字段：

- `run_id`、课例与输入文件版本；
- Agent、Skill、模型和 prompt 版本；
- 各阶段开始时间、结束时间、状态和错误码；
- 产物路径、`evidence_id`、`rule_id` 和审批决定；
- `evidence_type`，取值继续限定为 `live`、`fixture replay` 或 `design`。

这份记录能回答一次审查由谁执行、依据什么、在哪一步失败、导师批准了哪个版本。它也能为复盘和评估提供稳定输入。

### 4.2 将导师反馈变成结构化数据

对方项目允许用户评分并选择训练样本。TeachOps 不适合直接采用“五星评分 + 进入 LoRA”的形式。导师需要对具体审计发现做决定。

建议按 `finding_id` 保存：

- `decision`：`APPROVE`、`REJECT` 或 `APPROVE_WITH_CONDITION`；
- 关联的 `rule_id`、`evidence_id` 和 `audit_report_id`；
- 导师理由、修改条件和最终版本；
- Agent 建议是否被采纳，以及导师修改了什么。

团队可以先用这些数据统计规则误报、漏报和导师改写情况。真实样本数量和质量达到要求后，再评估微调价值。

### 4.3 用工作台展示治理流程

对方前端证明轻量网页可以承载会话、证据和反馈操作。TeachOps 的界面应围绕教学设计预审任务设计：

```text
提交材料 → Evidence 状态 → 修订 Diff → Audit findings → 导师决定 → 最终版本
```

每个 finding 应同时展示规则、引用证据、影响位置和建议。`BLOCKED` 页面只列缺失材料和补交动作，不生成修订内容。

初赛范围已明确排除 Web 工作台。团队应在完成 live 运行证据后再建设该界面，避免用界面截图代替多 Agent 运行事实。

### 4.4 隔离模型适配层与业务状态机

对方项目把模型调用放在 provider 层。TeachOps 可以沿用这一边界，把 AgentTeams、其他模型网关和本地 fixture 放在不同适配器中。

业务层只接收结构化结果，不依赖具体模型 SDK。适配器必须回传 provider、model、请求时间、错误类型和运行来源。这样更换模型时，Evidence → Design → Audit 状态机及三个 Skill 契约无需改写。

## 5. 不建议照搬的部分

### 5.1 四种模式不构成多 Agent 协作

对方项目使用四套 prompt 实现问答、学习路径、出题和陪练。代码中没有独立 Agent 权限、输入输出契约、handoff 或失败状态机。TeachOps 应保留现有角色隔离，不应把 prompt mode 当成 Agent 数量扩展。

### 5.2 当前 RAG 不能直接承担教学证据治理

该项目按 TF-IDF 相似度返回片段，只过滤得分小于等于零的结果。代码没有最低质量阈值、检索评估集或引用正确性检查。TeachOps 若后续接入 RAG，仍需保留来源定位、原文摘录、验证状态、缺证据阻断和审计规则。

### 5.3 当前数据不足以支持 TeachOps 微调

300 条冷启动数据说明没有交代生成来源、人工复核方式、训练与验证划分或基线结果。数据导出脚本也只按评分、人工勾选和回答长度筛选，并使用固定服务器路径。

TeachOps 当前只有合成课例和 fixture，不具备模型微调所需的真实导师样本。团队应先积累经过复核的审批与改写记录，再判断提示词、规则或微调哪个方案成本更低。

### 5.4 部署脚本不能代替运行证据

目标仓库包含 vLLM、Nginx 和 systemd 脚本，但仓库代码不能证明服务已成功部署。TeachOps 应继续区分代码存在、本地测试通过、live 运行和真实用户验收。

目标仓库在该 HEAD 下没有发现自动化测试、CI、鉴权或多用户数据隔离。其 README 也将项目定义为教育原型。TeachOps 不应把这些实现作为生产基线。

## 6. TeachOps 的吸收顺序

| 阶段 | 动作 | 验证标准 |
| --- | --- | --- |
| 初赛当前阶段 | 保持范围冻结，完成一次 AgentTeams 或模型驱动的真实正常流程 | 保存 Agent 消息、模型信息、阶段状态和最终产物；全部标记为 `live` |
| Live 闭环稳定后 | 建立统一 `run_record`，把运行状态与现有产物关联 | 任一审计报告可追溯到输入、Evidence Packet、模型和审批决定 |
| 复赛产品化 | 建设导师审查工作台 | 正常流程和缺证据流程均可完成；界面结果与底层产物一致 |
| 有真实导师数据后 | 建立反馈评估集 | 能计算规则误报、导师采纳和人工改写情况，并保留样本来源 |
| 评估证明需要后 | 选择 RAG、规则增强或微调 | 先设基线，再用独立验证集比较质量、成本和失败类型 |

## 7. 最近一步

TeachOps 下一步仍是取得一次可复核的 live 多 Agent 运行。完成后再定义 `run_record` 数据结构，把消息、产物、Evidence ID、Rule ID 和人工审批串起来。

这项工作吸收了对方项目“运行过程可保存”的优点，同时保留 TeachOps 已建立的证据边界和治理契约。
