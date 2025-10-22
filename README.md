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

## Demo 测试

本项目包含一个简单的测试应用 `test_app.py`，可以用来验证代理服务是否正常工作。

### 1. 启动主服务

首先，确保主服务 `main.py` 正在运行：

```bash
python main.py
```

服务将默认在 `http://0.0.0.0:8000` 上启动。

### 2. 启动测试应用

在另一个终端中，启动测试应用 `test_app.py`：

```bash
python test_app.py
```

测试应用将启动在 `http://localhost:8001`。

### 3. 进行测试

在浏览器中打开 `http://localhost:8001`。你会看到一个 "开始 Ping 测试" 的按钮。

点击该按钮，测试应用会：
1.  向主服务的 `/commands/start` 端点发送请求，要求执行 `ping 8.8.8.8 -c 5` 命令。
2.  建立一个 WebSocket 连接到主服务，以接收命令的实时输出。
3.  在页面上实时显示 `ping` 命令的输出。

如果一切正常，你将看到 `ping` 命令的输出结果实时显示在页面上。
