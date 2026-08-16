# live-output：AgentTeams 正常流程真实运行产物

> 运行时间：2026-08-16（Asia/Shanghai）
> 运行环境：AgentTeams v1.1.2（embedded）+ qwen3.6-plus（阿里云百炼接入点），本机 Docker
> 协作角色：teachops-manager（调度）+ teachops-evidence / teachops-design / teachops-audit（Worker）
> 交互界面：Element Web（http://127.0.0.1:18088），导师（Admin）在房间内分派任务并作出最终审批

## 文件清单

| 文件 | 产出者 | 说明 |
| --- | --- | --- |
| `evidence-packet.json` | teachops-evidence | CUR-01~03 课标证据 + 学情画像（PK/M/O）+ 10 条交叉映射 |
| `lesson-revised.md` | teachops-design | 对照证据包修订后的教学设计 |
| `design-review-notes.md` | teachops-design | 四类问题清单 + 逐条修改说明 |
| `audit-report.json` | teachops-audit | R-001~R-005 逐条判定（3 PASS / 1 FAIL / 1 WARN） |
| `audit-report.md` | teachops-audit | 审计报告人读版 |
| `review-decision.md` | 导师（Admin）决定 + Manager 记录 | 附条件批准（M-01 环节补入条件） |

原始文件由各 Worker 产出于共享存储（MinIO `hiclaw-storage/shared/tasks/`），经同步下载归档至此。

## 完整性说明（如实标注）

- `evidence-packet.json` 第 17/25 行 `source_ref` 字段中 LLM 原始输出含未转义的 ASCII 引号导致 JSON 不可解析，归档时已将该两处内嵌引号替换为「」（内容零改动）。
- 其余文件未做任何人工修改。
- 与 `expected-output/`（fixture）结构对应关系见 `review-decision.md` 的对照节；live 审计（R-003 FAIL）比 fixture 判定更严格，属真实运行结果，非对 fixture 的复刻。

## Schema 对照（live 产物 vs Skill Contract）

live 产物由 AgentTeams 运行时的**任务级 task-spec** 驱动（本次运行由协作工具协助），其 JSON 结构与仓库 **Skill Contract**（`skills/*/contract.md`）定义的规范 schema 不同。二者关系：

- **live 产物** = 真实多 Agent 协作的原始输出（本目录）；
- **Skill Contract + 确定性实现**（`src/teachops_demo/pipeline.py`、`demo/*/deterministic-output/`）= 规范化的参考实现与对照基线；
- 两者语义等价，仅字段命名与文件组织不同，不影响审计结论的复核。

| 语义 | live（任务级 schema） | 契约（规范 schema） |
| --- | --- | --- |
| 证据包主键 | `evidence_packet_id` | `packet_id` |
| 证据条目 | `curriculum_items[]` + `learner_profile{}` | `evidence_items[]` |
| 交叉映射 | `cross_map[]` | 无独立字段（用 `locator`/`source_item_id`） |
| 时间 | `built_at` | `generated_at` |
| 状态 | READY（正常）/ BLOCKED（缺失） | `status: READY` / `status: BLOCKED` + `missing_items` |
| 审计报告主键 | `audit_id` | `report_id` |
| 审计判定 | `rule_results[]`（status/findings/evidence_refs） | `findings[]`（result/explanation/evidence_ids） |
| 总体结论 | `overall_status` | `overall.has_fail / needs_human_decision` |

**证据 ID 对照（核心四条约证）**：

| 契约 `evidence_id` | live 证据 | 内容 |
| --- | --- | --- |
| EV-001 | `CUR-02` | 课标第二学段数与运算（初步认识分数、同分母比较） |
| EV-002 | `CUR-01` | 课标课程理念（三会） |
| EV-003 | `M-01` | 最高频误解（分母越大分数越大，17/42） |
| EV-004 | `O-01` | 学情观察（专注时长 15-20 分钟） |

live 证据包还含契约最小集之外的条目（`CUR-03` 转述、`PK-01/02` 先备知识、`M-02` 次要误解），属运行时的额外组织，不影响上述四条的追溯。

**文件名对照**：live `evidence-packet.json` / `audit-report.json` / `lesson-revised.md` ↔ 契约 `evidence_packet.json` / `audit_report.json` / `revision.md`。
