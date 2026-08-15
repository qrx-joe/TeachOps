# AgentTeams 本机可用性核验

> 核验日期：2026-08-15（Asia/Shanghai）
> 结论：Docker Server 可用；AgentTeams 正常流程烟雾测试未通过；当前采用 `fixture replay`。

## 1. 实际检查结果

| 检查项 | 实际结果 | 证据边界 |
| --- | --- | --- |
| Docker CLI | 29.4.1 | `docker version` 的 Client 输出 |
| Docker Server | Docker Desktop 4.71.0，Engine 29.4.1，linux/amd64 | 启动 Docker Desktop 后，在沙箱外只读执行 `docker version` |
| Docker 容器/镜像 | 可列出；没有 `agentteams-*` 容器或 AgentTeams 镜像 | `docker ps -a`、`docker images` |
| AgentTeams CLI | `agentteams`、`agent-teams`、`ateams` 均未找到 | PowerShell `Get-Command` |
| 模型凭据 | 当前进程环境未发现 Qwen/DashScope/OpenAI/AgentTeams 相关变量名 | 仅检查变量名，未读取或记录任何值 |
| Manager / Worker / Qwen | 未运行、未验证 | 没有 Team Room、消息收发或模型调用证据 |

## 2. 止损决定

官方安装流程需要运行 Docker，并在交互式安装中配置 LLM provider、API Key、管理员凭据与本地访问参数。本机虽然已具备 Docker，但缺少 AgentTeams 安装和可用模型凭据。继续安装需要用户提供敏感凭据并改变本机第三方运行状态，因此本次在进入该步骤前停止，不制作模拟聊天记录。

当前仓库的正常流程使用：

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python scripts/replay_fixture.py
```

输出明确标记为 `fixture replay`，不是 AgentTeams、Qwen 或真实用户运行。

## 3. 后续恢复 live 烟雾测试的通过条件

只有以下项目全部有真实输出时，才能把正常流程登记为 `live`：

1. `docker version` 同时显示 Client 与 Server。
2. AgentTeams stable v1.1.2 容器启动且健康。
3. 本地 Element Web 可登录。
4. Manager 回复最小消息。
5. 一个 Worker 成功接收并回传任务。
6. Qwen 最小调用成功。
7. 正常课例依次产生四个文件，并由用户在 Team Room 作出审批决定。

任一项缺失，都只能分别标记为环境核验、`design` 或 `fixture replay`。
