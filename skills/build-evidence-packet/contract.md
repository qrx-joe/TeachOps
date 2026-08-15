# Skill Contract：build-evidence-packet

> 版本：1.0.0（2026-08-14）
> 挂载角色：Evidence Agent

## skill_id

`build-evidence-packet`

## version

1.0.0

## purpose

把课程标准来源与合成聚合学情整理为可引用的证据包（Evidence Packet），是全流程唯一的证据生产入口。关键课标证据缺失时返回 `BLOCKED` 并给出缺失项清单，从源头阻断"无依据生成"。

## input_schema

```json
{
  "type": "object",
  "required": ["curriculum_source_ref", "learner_summary_ref", "case_metadata"],
  "properties": {
    "curriculum_source_ref": {
      "type": "string",
      "description": "课标来源文件引用（路径或 URL），如 demo/normal-case/input/curriculum-source.md"
    },
    "learner_summary_ref": {
      "type": "string",
      "description": "聚合学情摘要文件引用，必须含 synthetic: true"
    },
    "case_metadata": {
      "type": "object",
      "required": ["subject", "grade", "topic"],
      "properties": {
        "subject": { "type": "string" },
        "grade": { "type": "string" },
        "topic": { "type": "string" }
      }
    }
  }
}
```

## output_schema

输出 `evidence_packet.json`：

```json
{
  "type": "object",
  "required": ["packet_id", "status", "evidence_items", "generated_at"],
  "properties": {
    "packet_id": { "type": "string" },
    "status": { "enum": ["READY", "BLOCKED"] },
    "evidence_items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["evidence_id", "source", "locator", "summary", "quote_type"],
        "properties": {
          "evidence_id": { "type": "string", "pattern": "^EV-[0-9]{3}$" },
          "source": { "type": "string", "description": "来源文件与官方出处" },
          "locator": { "type": "string", "description": "来源内定位：条目号、章节或字段路径" },
          "summary": { "type": "string" },
          "quote_type": { "enum": ["原文摘录", "转述"] },
          "verify_status": { "enum": ["VERIFIED", "UNVERIFIED"] },
          "evidence_kind": { "enum": ["curriculum", "learner_misconception", "learner_observation"] },
          "source_item_id": { "type": "string", "description": "学情条目的真实 ID，如 M-01" },
          "observed_frequency": { "type": "string", "pattern": "^[0-9]+/[1-9][0-9]*$" }
        }
      }
    },
    "missing_items": {
      "type": "array",
      "items": { "type": "string" },
      "description": "BLOCKED 时的缺失项清单"
    }
  }
}
```

## invocation_conditions

- 由 Evidence Agent 在任务进入 `EVIDENCE_BUILDING` 时调用，每案例一次，重跑需新 packet_id。
- `curriculum_source_ref` 与 `learner_summary_ref` 指向的文件必须存在且可读。
- 学情摘要缺少 `synthetic: true` 标记时拒绝建包（数据质量检查）。
- 误解条目按 `observed_frequency` 比率选择最高频项，不依赖数组顺序；locator 必须使用该条目的真实 `id`。

## permissions

| 类别 | 范围 |
| --- | --- |
| 文件读 | curriculum-source.md、learner-summary.json |
| 文件写 | evidence_packet.json |
| 网络 | 无 |
| 模型调用 | 无（确定性整理，不经过大模型） |

## timeout

30 秒。超时即失败，不输出半成品包。

## failure_contract

| 错误码 | 触发条件 | 返回行为 |
| --- | --- | --- |
| `E_INPUT_MISSING` | 课标或学情文件缺失/不可读 | `status=BLOCKED` + `missing_items` 列出缺失文件；不产出 READY |
| `E_DATA_QUALITY` | 学情摘要无 synthetic 标记 | 整体失败并说明原因，不建包（防止真实学生数据进入演示链路） |
| `E_SKILL_TIMEOUT` | 超过 30 秒 | 失败，不落盘部分结果 |

约定：BLOCKED 时已能整理的条目仍保留在 `evidence_items` 中备查，但 `status` 必须为 `BLOCKED`，下游 Skill 一律不得引用。

## security_notes

- 只提取短引用并保留来源定位，不复制、不分发课程标准全文（版权边界）。
- 证据只能来自两个输入文件，禁止用模型内部知识补写来源或原文。
- 转述类条目必须标注 `quote_type: "转述"`，防止被当作原文引用。

## examples

### 正常样例（demo/normal-case）

输入：curriculum-source.md（含 CUR-01/02/03 条目）+ learner-summary.json（synthetic: true）。
输出（节选）：`status: READY`，证据条目含 EV-001（CUR-02 原文摘录：初步认识分数与同分母比较）、EV-002（CUR-01 原文摘录：三会）、EV-003（学情 M-01"分母越大分数越大"，频率 17/42）、EV-004（学情观察：专注时长 15-20 分钟）。

### 失败样例（demo/missing-evidence-case）

输入：curriculum_source_ref 指向的文件不存在。
输出：`status: BLOCKED`，`missing_items: ["curriculum-source.md（关键课标证据，课例所有 CUR 引用均悬空）"]`，`evidence_items` 仅剩学情侧条目。下游 `revise-lesson-with-evidence` 拒绝执行，流程停止等待补证。

### 可复用性

本 Skill 不依赖具体学科：只要提供"课程标准来源文件 + 聚合学情文件"即可为任意课例建包，可被其他教研类 Agent 直接复用。
