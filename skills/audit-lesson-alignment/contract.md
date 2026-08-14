# Skill Contract：audit-lesson-alignment

> 版本：1.0.0（2026-08-14）
> 挂载角色：Audit Agent

## skill_id

`audit-lesson-alignment`

## version

1.0.0

## purpose

独立按规则包对候选教学设计逐条稽核目标、活动、评价、学情响应与证据覆盖的一致性，产出 `audit_report.json`。每条判定必须同时落到 `rule_id`（依据哪条规则）与 `evidence_id`（依据哪条证据），使审计结论可复核。

## input_schema

```json
{
  "type": "object",
  "required": ["candidate_lesson_ref", "evidence_packet_ref", "rule_pack_ref"],
  "properties": {
    "candidate_lesson_ref": {
      "type": "string",
      "description": "候选教学设计（初稿或修订稿）文件引用"
    },
    "evidence_packet_ref": { "type": "string" },
    "rule_pack_ref": { "type": "string" }
  }
}
```

## output_schema

输出 `audit_report.json`：

```json
{
  "type": "object",
  "required": ["report_id", "complete", "findings"],
  "properties": {
    "report_id": { "type": "string" },
    "complete": {
      "type": "boolean",
      "description": "false 表示输入不全，此时不得给出总体结论"
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule_id", "result", "location", "explanation"],
        "properties": {
          "rule_id": { "type": "string" },
          "result": { "enum": ["PASS", "WARN", "FAIL", "NA"] },
          "location": { "type": "string", "description": "候选设计中的位置" },
          "evidence_ids": {
            "type": "array",
            "items": { "type": "string" },
            "description": "佐证判定的证据条目；NA/引用不可验证时可为空并说明"
          },
          "explanation": { "type": "string" },
          "suggestion": { "type": "string", "description": "处理建议，只描述不代改" }
        }
      }
    },
    "overall": {
      "type": "object",
      "description": "仅 complete=true 时出现",
      "properties": {
        "has_fail": { "type": "boolean" },
        "needs_human_decision": { "type": "boolean" }
      }
    }
  }
}
```

## invocation_conditions

- 由 Audit Agent 在任务进入 `AUDITING` 时调用；对初稿或修订稿均可运行（修订稿为正常流程对象）。
- 三份输入齐全才产生完整报告；否则输出 `INCOMPLETE`。
- `NA` 判定必须写明规则不适用的原因。

## permissions

| 类别 | 范围 |
| --- | --- |
| 文件读 | 候选教学设计、evidence_packet.json、rule-pack.json |
| 文件写 | audit_report.json |
| 网络 | 仅可选的模型网关调用（解释性文字） |
| 模型调用 | 可选：规则判定本身为确定性逻辑，模型关闭时仍可完整运行（降级不降标准） |

## timeout

确定性判定 60 秒；含模型解释 120 秒。超时输出确定性部分，模型解释标记省略。

## failure_contract

| 错误码 | 触发条件 | 返回行为 |
| --- | --- | --- |
| `E_INPUT_MISSING` | 任一输入缺失 | `complete: false` + 所缺输入清单，不给总体结论 |
| `E_RULE_CONFLICT` | 规则互相冲突 | 标记冲突规则并置 `needs_human_decision: true`，不自动选边 |
| `E_UNVERIFIED_REF` | 候选设计引用了 packet 中不存在的 evidence_id | 相关判定降为 `WARN` 并注明"引用不可验证" |
| `E_SKILL_TIMEOUT` | 超时 | 输出已完成的确定性 findings，未完成项标记 `NA(超时未检)` |

## security_notes

- 只读输入：本 Skill 在任何失败情形下都不改写候选设计或证据包。
- 存在 `FAIL` 时报告不得包含"可发布/可采纳"类总体结论（审批权在人）。
- 判定链条 rule_id + evidence_id 必须完整，禁止无依据结论。

## examples

### 正常样例（对 demo/normal-case 初稿的首次审计）

输出（节选）：
- R-001 → `FAIL`：目标 3 无评价任务（位置：评价任务表第 3 行）
- R-002 → `FAIL`：设计理由 2 无 evidence_id（EV-004 存在而未被引用）
- R-003 → `FAIL`：最高频误解 M-01（17/42）无显式处理环节（EV-003）
- R-004 → `FAIL`：目标 3 未映射课标条目
- R-005 → `PASS`：四环节均有时长，总计 40 分钟
- `overall.has_fail: true`，转导师决策

### 失败样例

输入：evidence_packet_ref 文件缺失。
输出：`complete: false`，`missing: ["evidence_packet.json"]`，无总体结论。

### 可复用性

"规则包 + 证据包 + 候选文档"三元结构同样与学科无关；审计逻辑（逐规则、可追溯、失败阻断发布结论）可复用于任何需要独立稽核的文档流水线。
