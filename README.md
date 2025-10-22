# CLI 代理服务

本项目是一个用 Python 实现的 CLI 代理服务，基于 FastAPI 和 ptyprocess。

它将本地的命令行工具（CLI）通过网络 API 的形式暴露出去，允许远程客户端通过标准的 HTTP 和 WebSocket 协议与之交互。

## 功能

- **远程触发**: 通过 HTTP POST 请求启动任何 CLI 命令。
- **实时输出**: 通过 WebSocket 实时获取命令的输出流。
- **进程管理**: 跟踪每个命令的执行状态（运行中、已完成、失败、已停止）。
- **状态查询**: 通过 HTTP GET 请求查询特定命令的状态。
- **停止命令**: 通过 HTTP POST 请求终止一个正在运行的命令。

## 如何运行

### 1. 安装依赖

首先，请确保你已经安装了 Python 3.7+。然后通过 pip 安装项目所需的依赖：

```bash
pip install -r requirements.txt
```

### 2. 启动服务

直接运行 `main.py` 即可启动服务：

```bash
python main.py
```

服务将默认在 `http://0.0.0.0:8000` 上启动。

## API 端点

关于 API 的详细设计，请参考 `PROJECT_DESIGN.md` 文档。

- `POST /commands/start`: 启动一个新命令。
- `GET /commands/{execution_id}/status`: 获取命令执行状态。
- `POST /commands/{execution_id}/stop`: 停止一个正在运行的命令。
- `GET /commands`: 列出所有命令。
- `WS /commands/{execution_id}/stream`: 订阅命令的实时输出。
