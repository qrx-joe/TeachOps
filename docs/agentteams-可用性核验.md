# AgentTeams 本机可用性核验

> 核验日期：2026-08-15（Asia/Shanghai）
> 结论：AgentTeams stable **v1.1.2 已完成本机安装，烟雾测试 6 项全部通过（live）**；正常课例四产物流程尚未运行，正常流程证据仍为 `fixture replay`。

## 1. 环境与安装核验结果

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| Docker CLI / Server | 29.4.1 / Docker Desktop 4.71.0 | `docker version` Client 与 Server 同时可见 |
| AgentTeams 版本 | v1.1.2（embedded 架构） | 镜像 `agentteams-embedded:v1.1.2`，digest `a3654ff6` |
| 运行容器 | `agentteams-controller` + `hiclaw-manager` + 3 个 `hiclaw-worker-*` 常驻运行 | `docker ps` 实时输出 |
| Element Web | http://127.0.0.1:18088 登录成功（admin） | 本机浏览器实测 |
| LLM | 阿里云百炼接入点 + `qwen3.6-plus`，安装器联通测试通过 | API Key 仅用户本机输入，未写入仓库、未出现在任何截图中 |

## 2. 烟雾测试结果（2026-08-15 下午，全部通过）

| # | 检查项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | Docker Server | ✅ | Docker Desktop 4.71.0 / Engine 29.4.1 |
| 2 | AgentTeams v1.1.2 启动且健康 | ✅ | controller/manager/worker 容器 Up |
| 3 | 本地 Element Web 登录 | ✅ | http://127.0.0.1:18088，admin 登录 |
| 4 | Manager 回复最小消息 | ✅ | 发送“你好，请回复 ready”，Manager 回复“ready! 我已经准备就绪……” |
| 5 | Worker 收发任务 | ✅ | Manager 分派“@teachops-evidence 请汇报你的角色”，Worker 回复角色描述 |
| 6 | Qwen 最小调用 | ✅ | 回复由 qwen3.6-plus 经百炼接入点生成 |

界面截图按《截图与产物留存清单》流程先入 `evidence/private/`，脱敏后归档至 `evidence/` 并登记索引。

## 3. 安装过程中修复的工程问题（复现要点）

官方 main 分支安装器（`install/agentteams-install.ps1`）与 v1.1.2 镜像之间存在版本错位，共修复五处：

1. **安装脚本编码**：脚本为无 BOM UTF-8，Windows PowerShell 5.1 按 GBK 解析中文导致语法错误秒退；为脚本添加 UTF-8 BOM 后正常。
2. **环境变量前缀错位**：main 安装器向容器传 `AGENTTEAMS_*`，v1.1.2 镜像内组件（controller、tuwunel、minio 启动脚本）读取 `HICLAW_*`，导致 Tuwunel/MinIO 反复崩溃、admin 注册携带空用户名；将全部 `AGENTTEAMS_X` 桥接为 `HICLAW_X` 后恢复。
3. **Manager 运行时名**：v1.1.2 Manager CR 仅支持 `openclaw`/`copaw`，不识别 main 安装器的默认值 `qwenpaw`；改为 `openclaw` 并使用 `agentteams-manager:v1.1.2` 镜像。
4. **容器间地址**：`CONTROLLER_URL` 以 `127.0.0.1` 传入导致子容器地址替换失效；改为 `http://agentteams-controller:8090`。
5. **存储前缀语义**：`STORAGE_PREFIX` 的语义是 `mc别名/bucket`（v1.1.2 期望 `hiclaw/hiclaw-storage`），bridge 值 `agentteams/agentteams-storage` 会被解释为不存在的 mc 别名与 bucket；对齐官方值后 Worker 配置分发成功。

修复后的容器重建参数与桥接 env 文件保存在仓库外 `D:\agentteams-install\`（含敏感凭据引用，不入库）。

## 4. 当前证据边界

- 烟雾测试（第 2 节六项）：**live**。
- 正常课例流程（Evidence → Design → Audit 四产物 + 导师审批）：尚未在 AgentTeams 上运行，仓库内正常流程产物仍为 `fixture replay`（`demo/normal-case/fixture-replay-output/`），README 与 PPT 相应标注保持不变，待 live 流程完成后替换。

## 5. 恢复正常流程 live 的通过条件

1. `docker version` 同时显示 Client 与 Server。✅（已满足）
2. AgentTeams stable v1.1.2 容器启动且健康。✅（已满足）
3. 本地 Element Web 可登录。✅（已满足）
4. Manager 回复最小消息。✅（已满足）
5. 一个 Worker 成功接收并回传任务。✅（已满足）
6. Qwen 最小调用成功。✅（已满足）
7. 正常课例依次产生四个文件，并由用户在 Team Room 作出审批决定。⏳（待运行）

第 7 项完成前，正常流程在《运行证据索引》中保持 `fixture replay` 标注。
