# Skill Contract：revise-lesson-with-evidence

> 版本：1.0.0（2026-08-14）
> 挂载角色：Design Agent

## skill_id

`revise-lesson-with-evidence`

## version

1.0.0

## purpose

依据 `READY` 状态的 Evidence Packet 与规则包，对初版教学设计生成结构化修改建议（revision.md）。核心约束：每条关键建议必须引用 evidence_id；证据不足的建议只能进入"待补证"区，不得冒充有据。

## input_schema

```json
{
  "type": "object",
  "required": ["lesson_draft_ref", "evidence_packet", "rule_pack_ref"],
  "properties": {
    "lesson_draft_ref": { "type": "string", "description": "初版教学设计文件引用" },
    "evidence_packet": {
      "type": "object",
      "description": "完整的 evidence_packet.json 对象，status 必须为 READY",
      "required": ["packet_id", "status"],
      "properties": {
        "packet_id": { "type": "string" },
        "status": { "enum": ["READY"] }
      }
    },
    "rule_pack_ref": { "type": "string", "description": "规则包文件引用" }
  }
}
```

## output_schema

输出 `revision.md`（Markdown，结构契约如下）：

```json
{
  "type": "object",
  "description": "revision.md 的结构约定（YAML front matter + 建议列表）",
  "required": ["revision_id", "packet_id", "suggestions"],
  "properties": {
    "revision_id": { "type": "string" },
    "packet_id": { "type": "string", "description": "所依据的证据包，可回溯" },
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "location", "change", "rationale", "evidence_ids"],
        "properties": {
          "id": { "type": "string" },
          "location": { "type": "string", "description": "初稿中的位置，如'教学目标 3'" },
          "change": { "type": "string", "description": "具体修改内容" },
          "rationale": { "type": "string" },
          "evidence_ids": {
            "type": "array",
            "items": { "type": "string" },
            "description": "引用的证据条目；空数组表示待补证建议"
          },
          "pending_evidence": { "type": "boolean", "description": "true 时进入待补证区" }
        }
      }
    }
  }
}
```

## invocation_conditions

- 由 Design Agent 在任务进入 `DESIGNING` 时调用。
- 前置硬条件：`evidence_packet.status == READY`；否则拒绝执行（见失败契约）。
- 建议数量不做上限要求，但每条必须可定位（location 不能为空）。

## permissions

| 类别 | 范围 |
| --- | --- |
| 文件读 | lesson-draft.md、evidence_packet.json、rule-pack.json |
| 文件写 | revision.md |
| 网络 | 仅经 AgentTeams 模型网关调用 Qwen，不直连外网 |
| 模型调用 | 是（通过网关；网关持有凭据，本 Skill 不接触 API Key） |

## timeout

120 秒。允许重试 1 次；每次调用携带 `run_id` 保证幂等（同一 run_id 重复调用不产生多份 revision）。

## failure_contract

| 错误码 | 触发条件 | 返回行为 |
| --- | --- | --- |
| `E_EVIDENCE_INSUFFICIENT` | packet 为 BLOCKED、缺失或引用失效 | 拒绝执行并返回原因，不产出任何建议 |
| `E_MODEL_TIMEOUT` | 模型调用超时（含 1 次重试） | 失败，不落盘部分结果 |
| `E_MODEL_SCHEMA_INVALID` | 输出缺必填字段（如建议无 location） | 失败并返回校验错误，可重试 1 次；仍失败则整体失败 |
| `E_PENDING_EVIDENCE_OVERFLOW` | 待补证建议占比超过一半 | 输出降级标记"证据不足，建议先补证"，提示人工介入 |

约定：失败时绝不输出"看似完整的修订"；待补证建议不得编造 evidence_id。

## security_notes

- Prompt 与输出中不得出现 API Key、账号或学生个人信息。
- 模型内部知识不得作为依据写入 `evidence_ids`；引用必须能回溯到 packet。
- 输出不改动 rule-pack、evidence_packet（只读）。

## examples

### 正常样例（demo/normal-case）

输入：初稿 + READY packet（EV-001..EV-004）+ 规则包。
输出（节选）：
- S-001 目标 3 补评价任务并映射 CUR-02 → `evidence_ids: [EV-001]`
- S-002 环节 3 增加"1/2 与 1/8 谁大"辨析活动，针对 M-01 → `evidence_ids: [EV-003]`
- S-003 理由 2 补引专注时长观察记录 → `evidence_ids: [EV-004]`

### 失败样例

输入：packet.status = BLOCKED。
输出：拒绝执行，返回 `E_EVIDENCE_INSUFFICIENT`（描述缺失项引用 Manager 转给导师），revision.md 不产生。

### 可复用性

约束的是"证据引用纪律"而非学科内容，任何"文档 + 证据包 + 规则"形态的修订任务（教案、实验设计、培训方案）都可复用。
