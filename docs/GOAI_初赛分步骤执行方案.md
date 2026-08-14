# 研序 TeachOps：GOAI 初赛分步骤执行方案

> 版本：V1.0  
> 制定日期：2026-08-14  
> 截止日期：2026-08-16，准确时刻以参赛系统为准  
> 当前状态：尚未开始实施  
> 执行原则：必交材料先完成，运行演示设置停止线

## 1. 完成标准

初赛完成不以“产品功能数量”判断。满足以下条件即可提交：

- [ ] 作品简介不超过 500 字，包含标点。
- [ ] 方案 PPT/PDF 能正常打开，内容覆盖场景、Agent、Skill、异常、安全和开源计划。
- [ ] 四个 Agent 的职责、输入、产出和禁止动作清楚。
- [ ] 三个 Skill 有输入输出、失败处理和安全边界。
- [ ] 固定课例包含正常样例和缺证据样例。
- [ ] 运行材料区分 `live`、`fixture replay` 和 `design`。
- [ ] 仓库和提交材料不包含 API Key、个人数据和未授权内容。
- [ ] 用户在参赛系统中完成上传，并看到提交成功状态。

AgentTeams 真实运行属于加分项。安装或集成失败时，团队按降级方案提交，不延误两项必交材料。

## 2. 工作分工

当前由一名参赛者主导，AI 助手负责材料和工程协作。

### 用户负责

- 登录比赛系统并确认截止时刻、模板和上传字段。
- 启动 Docker Desktop。
- 在本机输入阿里云百炼 API Key，不能把 Key 发到聊天或写入仓库。
- 判断作品名称、团队信息和公开仓库名称。
- 检查最终材料并执行平台上传。

### AI 助手负责

- 整理项目简介、PPT 文案和结构。
- 准备 Agent Identity、Skill contracts 和固定样例。
- 指导并检查 AgentTeams 配置。
- 生成 README、验证清单和运行证据索引。
- 检查字数、链接、敏感信息和材料一致性。

## 3. 总时间预算

| 阶段 | 时间上限 | 截止建议 |
| --- | ---: | --- |
| 提交规则与范围冻结 | 1 小时 | 8 月 14 日开始后第 1 小时 |
| 固定样例、Agent、Skill 与材料骨架 | 6.25 小时 | 8 月 14 日 |
| AgentTeams 烟雾测试与团队配置 | 3 小时 | 8 月 14 日晚至 8 月 15 日上午 |
| 正常与异常流程 | 3 小时 | 8 月 15 日中午前 |
| PPT、README 和证据整理 | 4.5 小时 | 8 月 15 日 20:00 前 |
| 最终检查和上传 | 1.5 小时 | 8 月 16 日上午 |

所有步骤的时间上限合计 19.25 小时。AgentTeams 或 Qwen 触发降级后，预计可以压缩到 16 小时以内。某一步超时后执行对应降级，不挤占后续材料时间。

## 4. 分步骤执行

### 步骤 0：建立提交控制表

**时间上限：30 分钟**

操作：

- [ ] 登录 GOAI 参赛系统。
- [ ] 记录准确截止时刻。
- [ ] 下载初赛模板和参赛手册。
- [ ] 记录作品简介字段的计数规则。
- [ ] 记录 PPT/PDF 的格式、页数、大小和命名限制。
- [ ] 确认代码仓库链接是否有独立字段。

产出：

- `submission/提交要求核对表.md`
- 官方模板本地副本

验证：

- 截止时刻和上传格式来自登录后的官方页面，不依赖推测。

停止条件：

- 如果官网与当前方案冲突，以官网为准，先调整材料交付，不开始环境安装。

### 步骤 1：冻结一句话定位和作品名称

**时间上限：30 分钟**

暂定名称：

> 研序 TeachOps：多 Agent 教学设计预审与质量治理系统

暂定一句话定位：

> TeachOps 让 Evidence、Design 和 Audit Agent 围绕同一份教学设计协作，导师可以核对依据、处理风险并确认最终结果。

操作：

- [ ] 确认首要用户只有“师范院校或教师培训导师”。
- [ ] 确认主场景只有“教学设计预审”。
- [ ] 确认主课例只有一个小学数学课例。
- [ ] 删除“大而全教育平台”“全场景教师助手”等表述。

产出：

- 一句话定位
- 作品名称
- 100 字问题描述

验证：

- 不需要额外解释，读者能说出用户、任务和系统作用。

### 步骤 2：准备固定 Demo 输入

**时间上限：90 分钟**

操作：

- [ ] 选定“三年级数学：分数的初步认识”或同等清晰的单一课例。
- [ ] 保存一段有公开来源的课程标准，记录 URL、标题、发布日期和访问日期。
- [ ] 编写一份团队原创的初版教学设计，故意保留两至三个可审计问题。
- [ ] 编写一份合成聚合学情，不使用学生姓名、学号或联系方式。
- [ ] 定义三至五条 Demo Rule，并标注适用范围和版本。
- [ ] 复制正常样例，删除关键课标证据，形成异常样例。

建议缺陷：

- 教学目标没有对应评价任务。
- 活动没有处理“分母越大分数越大”的合成错误模式。
- 一条关键设计理由没有 Evidence 引用。

产出：

```text
demo/
├─ normal-case/input/
│  ├─ curriculum-source.md
│  ├─ lesson-draft.md
│  ├─ learner-summary.json
│  └─ rule-pack.json
└─ missing-evidence-case/input/
   ├─ lesson-draft.md
   ├─ learner-summary.json
   └─ rule-pack.json
```

验证：

- 所有输入可以公开。
- 合成内容带有 `synthetic: true` 或醒目标记。
- 异常样例确实缺少关键课程依据。

停止条件：

- 不寻找第二个课例，不制作不同学科版本。

### 步骤 3：编写四个 Agent Identity

**时间上限：60 分钟**

操作：

- [ ] 编写 Manager Identity。
- [ ] 编写 Evidence Agent Identity。
- [ ] 编写 Design Agent Identity。
- [ ] 编写 Audit Agent Identity。

每个 Identity 使用相同结构：

```text
name
purpose
inputs
outputs
allowed_actions
forbidden_actions
handoff_to
failure_behavior
```

产出：

```text
agents/
├─ manager.md
├─ evidence-agent.md
├─ design-agent.md
└─ audit-agent.md
```

验证：

- 四个角色不能互相替代。
- Evidence Agent 不写完整教案。
- Design Agent 不自行批准。
- Audit Agent 不修改候选教案。
- Manager 不判断教学质量。

### 步骤 4：编写三个 Skill contracts

**时间上限：90 分钟**

操作：

- [ ] 编写 `build-evidence-packet`。
- [ ] 编写 `revise-lesson-with-evidence`。
- [ ] 编写 `audit-lesson-alignment`。

每个 Skill 至少写明：

```text
skill_id
version
purpose
input_schema
output_schema
invocation_conditions
permissions
timeout
failure_contract
security_notes
examples
```

产出：

```text
skills/
├─ build-evidence-packet/
├─ revise-lesson-with-evidence/
└─ audit-lesson-alignment/
```

验证：

- 每个 Skill 有正常输入输出。
- 每个 Skill 至少有一个失败样例。
- Skill 能脱离某个 Agent 单独说明和测试。

停止条件：

- 不增加第四个 Skill。
- Diff、回滚和导出保持为 PPT 中的复赛设计。

### 步骤 5：先完成作品简介 v1

**时间上限：45 分钟**

操作：

- [ ] 用 500 字以内说明场景、问题、方案、差异、开源价值和当前进展。
- [ ] 用脚本或编辑器统计包含标点的字符数。
- [ ] 删除无法证明的准确率、节省时间和用户采用数据。
- [ ] 当前进展只引用已经存在的 Agent、Skill、样例或运行证据。

产出：

- `submission/作品简介.md`
- `submission/作品简介.txt`

验证：

- 字符数符合官方字段限制。
- 文案包含 AgentTeams、三个 Skill 和缺证据阻断。
- 没有“业内首创”“显著提升”等无证据表述。

### 步骤 6：完成 10 页 PPT 文案骨架

**时间上限：90 分钟**

按以下顺序写每页标题、结论和所需证据：

1. 项目定义。
2. 教学设计预审场景。
3. 固定课例和输入。
4. 端到端闭环。
5. 四个 Agent Identity。
6. 三个 Skill。
7. AgentTeams 映射。
8. 缺证据异常分支。
9. 开放与安全边界。
10. 当前进展、限制和复赛计划。

操作：

- [ ] 每页只回答一个问题。
- [ ] 每页先写一句结论，再补图或证据。
- [ ] 为运行截图预留位置，但不提前放模拟终端图。
- [ ] 把 Web、数据库、RAG 和 MCP 放入复赛计划页。

产出：

- `submission/PPT逐页文案.md`

验证：

- 即使 AgentTeams 尚未运行，PPT 文案也能完成初赛方案说明。

### 步骤 7：执行 AgentTeams 烟雾测试

**时间上限：90 分钟**

开始条件：

- 步骤 0 至步骤 6 已完成。
- 作品简介和 PPT 骨架已经可提交。

用户操作：

- [ ] 启动 Docker Desktop。
- [ ] 确认 Docker Server 正常。
- [ ] 在安装流程中输入 Qwen API Key。

技术检查：

- [ ] 安装 AgentTeams stable v1.1.2。
- [ ] 打开本地 Element Web。
- [ ] 确认 Manager 能回复一条最小消息。
- [ ] 创建一个测试 Worker。
- [ ] 确认 Worker 能接收任务并返回结果。

产出：

- 环境检查记录
- AgentTeams 版本和启动截图
- 一次最小 Manager/Worker 消息记录

通过标准：

- Docker、AgentTeams、Manager、一个 Worker 和 Qwen 调用全部成功。

降级触发：

- 90 分钟后仍无法完成上述最小链路，停止 AgentTeams 排障，跳到步骤 10，使用 fixture 完成材料。

### 步骤 8：配置正式四角色团队

**时间上限：90 分钟**

开始条件：步骤 7 通过。

操作：

- [ ] 创建 Evidence、Design 和 Audit Workers。
- [ ] 把四个 Agent Identity 应用到对应角色。
- [ ] 为每个 Worker 配置允许使用的 Skill。
- [ ] 创建 TeachOps Demo Team Room。
- [ ] 规定上下文只传文件引用和短状态，不在消息中复制长文。

产出：

- AgentTeams 团队配置
- Team Room 成员截图
- 角色与 Skill 映射表

验证：

- Manager 能分别点名三个 Workers。
- 每个 Worker 能读取自己的 Identity 和 Skill 说明。

### 步骤 9：运行正常流程

**时间上限：2 小时**

操作：

- [ ] 用户把正常课例交给 Manager。
- [ ] Manager 把证据任务分给 Evidence Agent。
- [ ] Evidence Agent 输出 `evidence_packet.json`，状态为 `READY`。
- [ ] Manager 将 Evidence Packet 和初稿交给 Design Agent。
- [ ] Design Agent 输出 `revision.md`，关键建议引用 Evidence ID。
- [ ] Manager 将候选设计交给 Audit Agent。
- [ ] Audit Agent 输出 `audit_report.json`。
- [ ] 用户输入批准或驳回决定。

产出：

- 三个真实 Agent 产物
- Team Room 协作记录
- 用户确认记录
- 正常流程截图

验证：

- 三个 Agent 真实参与，不使用单 Agent 结果改名伪装。
- 至少一条修改建议能回溯到 Evidence ID。
- Audit Agent 的产出与 Design Agent 不相同。

停止条件：

- 不为了追求更好文案反复运行模型。流程和边界正确后即停止。

### 步骤 10：运行或制作缺证据异常流程

**时间上限：60 分钟**

如果 AgentTeams 正常：

- [ ] 提交 `missing-evidence-case`。
- [ ] Evidence Agent 返回 `BLOCKED` 和缺失项。
- [ ] Manager 停止调用 Design Agent。
- [ ] 用户看到补证要求。

如果 AgentTeams 未通过烟雾测试：

- [ ] 使用预先定义的 expected output 制作 fixture replay。
- [ ] 输出文件和 PPT 标注 `fixture replay`。
- [ ] 不制作仿真的 AgentTeams 聊天截图。

产出：

- 异常流程记录或 fixture
- `BLOCKED` 产物
- 证据类型标记

验证：

- 缺少关键依据时不会进入 Design 步骤。

### 步骤 11：整理运行证据和 README

**时间上限：90 分钟**

操作：

- [ ] 编写项目简介和单场景说明。
- [ ] 说明四个 Agent 与三个 Skill。
- [ ] 给出正常和异常输入输出目录。
- [ ] 写清启动条件、版本、模型配置和 Key 安全方式。
- [ ] 建立证据索引，列出每张截图和输出文件的来源。
- [ ] 添加 MIT License。

产出：

- `README.md`
- `LICENSE`
- `docs/运行证据索引.md`

验证：

- 读者能够区分真实运行、fixture 和设计。
- README 不承诺尚未实现的 Web、数据库或 RAG。

### 步骤 12：制作并检查 PPT/PDF

**时间上限：3 小时**

操作：

- [ ] 将步骤 6 的文案制作成 10 页 PPT。
- [ ] 只放已经取得的截图和产物。
- [ ] 在截图下标注 `live`、`fixture replay` 或 `design`。
- [ ] 导出 PDF。
- [ ] 逐页检查标题、字体、裁切、链接和图片清晰度。
- [ ] 检查作品简介与 PPT 对当前进展的描述一致。

产出：

- `submission/TeachOps_GOAI_初赛方案.pptx`
- `submission/TeachOps_GOAI_初赛方案.pdf`

验证：

- PDF 在另一台设备或另一个阅读器中可以打开。
- 页数和文件大小符合提交要求。
- 没有占位符、演讲者备注泄露或 API Key。

### 步骤 13：执行提交前检查

**时间上限：45 分钟**

- [ ] 简介字符数符合限制。
- [ ] 项目名称在简介、PPT 和仓库中一致。
- [ ] PPT/PDF 文件名符合要求。
- [ ] 所有 URL 可以打开。
- [ ] 所有截图有证据类型。
- [ ] 仓库无 `.env`、Key、Token、Cookie 和个人信息。
- [ ] 第三方资料有来源和许可证说明。
- [ ] 初赛材料没有把复赛设计写成当前实现。

通过后冻结材料，不再修改功能。

### 步骤 14：上传并留存回执

**时间上限：45 分钟**

用户操作：

- [ ] 粘贴最终作品简介。
- [ ] 上传 PPT 或 PDF。
- [ ] 按平台要求填写可选仓库链接。
- [ ] 提交后重新进入作品页，检查状态。
- [ ] 保存提交成功截图和时间。

产出：

- 提交成功回执
- 最终材料归档

完成标准：

- 平台显示提交成功，而不是只完成本地文件准备。

## 5. 绝对不做清单

初赛提交前不开展以下工作：

- 自研 Web 工作台。
- FastAPI 或数据库。
- 用户、组织、权限和登录。
- RAG、向量库和 MCP Server。
- Diff、正式回滚和 Pattern Candidate。
- 多学科、多课例和批量任务。
- 性能压测和生产部署。
- 更换多个模型平台进行兼容测试。

这些任务不能帮助当前初赛按时提交。

## 6. 关键风险

| 风险 | 触发信号 | 处理 |
| --- | --- | --- |
| 不知道准确截止时刻 | 登录后仍未核对 | 步骤 0 未完成前不启动技术工作 |
| AgentTeams 安装卡住 | 90 分钟未跑通最小链路 | 停止排障，使用设计和 fixture |
| Qwen Key 或配额失败 | 最小调用失败 | 记录原因，使用 fixture，不换平台 |
| 课标授权不清 | 无官方来源或无法说明引用 | 只保留短引用和来源链接，不分发全文 |
| PPT 没有运行截图 | AgentTeams 未跑通 | 使用结构图和真实文件，不伪造聊天截图 |
| 时间被工程工作吃完 | 8 月 15 日仍无可提交 PDF | 立即停止工程，只完成材料 |
| 结果写得像营销文案 | 出现无证据指标 | 删除指标，改写为待验证假设 |

## 7. 最终交付清单

### 必交

- [ ] 500 字以内作品简介
- [ ] 初赛方案 PPT/PDF

### 可选

- [ ] 公开 MIT 仓库
- [ ] AgentTeams 配置和运行记录
- [ ] 正常与异常样例
- [ ] Agent Identity 和 Skill contracts

### 内部留存

- [ ] 官方提交要求核对表
- [ ] 运行证据索引
- [ ] 提交成功回执
- [ ] 未完成项和复赛清单
