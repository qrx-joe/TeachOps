# live 产物哈希核验

> 核验日期：2026-08-16（Asia/Shanghai）
> 算法：SHA-256

| 产物 | MinIO SHA-256 | evidence 归档说明 |
| --- | --- | --- |
| 正常链路 Evidence 原始包 | `120425e88e889d07a1b21217a82a6b5ec36fc2f9d0c8a7f6fe1e077b1e28f759` | `live-10-normal-evidence-packet.raw.txt`，原始输出含两处未转义 ASCII 引号，故以 `.txt` 原样保存 |
| 正常链路 Evidence 脱敏/可解析包 | `1c5795a640c68b0f2cce07a84c027a5f6ac77a984bb58214abc72bcf24ffa1c4` | `live-11-normal-evidence-packet.sanitized.json`，只把两处内嵌 ASCII 引号替换为中文引号，语义不变 |
| 正常链路修订稿 | `87e95fff23a131414fd5dcdbb700e1f60f910ed6e1cb671d1bf1c51a5b7814ff` | `live-12-normal-lesson-revised.md`，与 MinIO 一致 |
| 正常链路修订说明 | `846346150e7e0d21632175881b190a48d642025a161d42da015328de6771b30d` | `live-13-normal-design-review-notes.md`，与 MinIO 一致 |
| 正常链路审计 JSON | `ef27aaeee7c508fea69ee85fe7c50b4e9298f38bdf7047ce86dcc6726015b61b` | `live-14-normal-audit-report.json`，与 MinIO 一致 |
| 正常链路审计人读版 | `84b2a85e413ba78a627eba7959d597d02b95c9fec6b6e0f32d47d8d05de15b06` | `live-15-normal-audit-report.md`，与 MinIO 一致 |
| 缺证据 BLOCKED JSON | `c4a4c57597dc88e96826b8a3d5681a5c5e90679248bc52a3706c282a29a893a2` | `live-17-missing-evidence-packet.json`，直接从 MinIO 复制 |

导师审批记录 `live-16-normal-mentor-decision.md` 来源于 Team Room 的真人决定与 Manager 确认，不是 Worker 产物，因此不与 MinIO 对象做同源哈希比较。

