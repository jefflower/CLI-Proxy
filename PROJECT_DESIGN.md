# 本地 CLI 服务化项目设计文档

## 1. 项目概述

本项目旨在为本地命令行工具（CLI）创建一个代理服务层。该服务将本地的 CLI 工具能力通过网络 API 的形式暴露出去，允许远程客户端通过标准的 HTTP 和 WebSocket 协议与之交互。

核心目标是解决直接调用 CLI 的限制，实现：
- **远程触发**：允许外部系统通过网络请求来启动和控制本地的 CLI 命令。
- **进程管理**：对每一个由请求触发的 CLI 进程进行独立的生命周期管理。
- **实时输出**：支持将 CLI 的流式输出（例如 AI 应用的实时文本生成）通过 WebSocket 实时传输给客户端。
- **状态监控**：提供查询特定命令执行状态（如运行中、已完成、失败）的接口。

## 2. 核心需求分析

- **CLI 封装**：服务需要能接收指定的命令行字符串，并在服务器本地环境中安全地执行它。
- **双协议支持**：
    - **HTTP**: 用于管理和控制命令，如启动、停止、查询状态。这是一种无状态的、请求-响应式的交互。
    - **WebSocket**: 用于实时数据流传输。一旦命令开始执行，客户端可以建立一个 WebSocket 连接来接收实时的 `stdout` 和 `stderr` 输出。
- **异步执行与进程管理**：每个 CLI 命令都应在一个独立的子进程中异步执行，避免阻塞主服务。服务需要维护一个进程池或管理器，用于追踪每个命令的 `pid`、状态、开始/结束时间等信息。
- **唯一标识**：每个执行的命令都必须有一个唯一的 ID（`executionId`），客户端将使用此 ID 来查询状态或建立 WebSocket 连接。
- **健壮性**：服务需要妥善处理各种异常情况，例如命令执行失败、进程意外退出等，并向客户端报告正确的状态。

## 3. 技术选型

为了快速、高效地实现以上需求，我们推荐以下技术栈：

- **后端框架**: **Node.js + Express.js**
    - **原因**: Node.js 的异步、事件驱动模型非常适合处理 I/O 密集型任务，如管理子进程和网络套接字。Express.js 是一个成熟、简洁的 Web 框架，可以快速搭建 HTTP 服务。
- **CLI 交互**: **`node-pty`**
    - **原因**: 相比 Node.js 内置的 `child_process`，`node-pty` 可以在一个伪终端（pseudo-terminal）环境中执行命令。这能更好地模拟真实的用户终端，可以正确处理颜色代码、光标移动等复杂的终端输出，对于交互式或格式丰富的 AI CLI 工具来说是最佳选择。
- **WebSocket 库**: **`ws`**
    - **原因**: 这是一个流行、高性能且易于与 Express 集成的 WebSocket 库。
- **唯一 ID 生成**: **`uuid`**
    - **原因**: 用于为每个命令执行实例生成唯一的 `executionId`。

## 4. 架构设计

整体架构分为三层：

1.  **API 层 (HTTP & WS Server)**：负责接收和解析客户端请求。HTTP 服务器处理控制指令，WebSocket 服务器处理实时数据流。
2.  **进程管理层 (Process Manager)**：这是服务的核心。它维护一个内存中的注册表，记录了所有命令执行实例的状态。
    -   注册表结构 (示例):
        ```json
        {
          "executionId-123-abc": {
            "command": "ai-cli --stream 'hello'",
            "status": "running", // running, completed, error, stopped
            "pid": 45678,
            "ptyProcess": PTY_PROCESS_OBJECT, // node-pty 进程实例
            "startTime": "2023-10-27T10:00:00Z",
            "endTime": null,
            "exitCode": null,
            "output": [...] // 可以缓存部分最近的输出
          },
          ...
        }
        ```
3.  **执行层 (CLI Execution)**：由 `node-pty` 负责在操作系统的子进程中实际执行 CLI 命令。

**数据流**:
- **控制流 (HTTP)**: `Client -> HTTP POST /commands/start -> Process Manager -> node-pty spawns process -> Return executionId to Client`
- **数据流 (WebSocket)**: `Client -> WS /commands/{executionId}/stream -> Process Manager finds process -> Pipes pty output to WebSocket -> Client receives stream`

## 5. API 设计

### HTTP Endpoints

#### 1. 启动一个新命令

- **Endpoint**: `POST /commands/start`
- **说明**: 异步启动一个新的 CLI 命令。服务会立即返回一个唯一的执行 ID，客户端稍后可以使用此 ID 来查询状态或连接 WebSocket。
- **Request Body**:
    ```json
    {
      "command": "your-cli-tool --arg1 value1 --stream"
    }
    ```
- **Success Response (202) - Accepted**:
    ```json
    {
      "message": "Command execution started.",
      "executionId": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
    }
    ```

#### 2. 获取命令执行状态

- **Endpoint**: `GET /commands/{executionId}/status`
- **说明**: 查询指定命令的当前状态。
- **Success Response (200) - OK**:
    ```json
    {
      "executionId": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
      "command": "your-cli-tool --arg1 value1 --stream",
      "status": "running", // "running", "completed", "error", "stopped"
      "startTime": "2023-10-27T10:00:00Z",
      "endTime": null, // or timestamp if completed/error
      "exitCode": null // or exit code if completed/error
    }
    ```
- **Error Response (404) - Not Found**: 如果 `executionId` 不存在。

#### 3. 停止一个正在运行的命令

- **Endpoint**: `POST /commands/{executionId}/stop`
- **说明**: 强制终止一个正在运行的命令。
- **Success Response (200) - OK**:
    ```json
    {
      "message": "Command termination signal sent.",
      "executionId": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
    }
    ```

#### 4. 列出所有命令

- **Endpoint**: `GET /commands`
- **说明**: 获取所有（或最近的）命令执行实例的列表及其简要状态。
- **Success Response (200) - OK**:
    ```json
    [
      {
        "executionId": "a1b2c3d4-...",
        "command": "your-cli-tool ...",
        "status": "running",
        "startTime": "2023-10-27T10:00:00Z"
      },
      {
        "executionId": "z9y8x7w6-...",
        "command": "another-cli ...",
        "status": "completed",
        "startTime": "2023-10-27T09:55:00Z"
      }
    ]
    ```

### WebSocket Endpoint

#### 1. 订阅命令的实时输出

- **Endpoint**: `WS /commands/{executionId}/stream`
- **说明**: 客户端通过此 WebSocket 地址连接，以接收指定命令的实时 `stdout` 和 `stderr` 输出。
- **协议**:
    1.  客户端使用 `executionId` 建立 WebSocket 连接。
    2.  服务器验证 `executionId` 是否存在且正在运行。如果无效，则立即关闭连接。
    3.  如果有效，服务器会将该 `ptyProcess` 的 `data` 事件（输出流）直接转发到此 WebSocket 连接。
    4.  当 CLI 进程结束时，服务器会向客户端发送一个特殊的 `[EOF]` 消息（或一个结构化的 JSON 消息），然后关闭 WebSocket 连接。
- **数据格式**: 服务器将原始的终端输出数据块作为消息直接发送。客户端负责拼接和渲染。

## 6. 工作流程示例

1.  **客户端** 向 `POST /commands/start` 发送请求，Body 为 `{"command": "ai-cli --model gpt-4 --prompt '写一首关于秋天的诗'"}`。
2.  **服务器** 收到请求，生成 `executionId: "poet-9000"`，使用 `node-pty` 启动该命令，并在进程管理器中记录该实例。然后立即向客户端返回 `{"executionId": "poet-9000"}`。
3.  **客户端** 收到 `executionId` 后，立即建立一个 WebSocket 连接到 `WS /commands/poet-9000/stream`。
4.  **服务器** 的 WebSocket 服务接收到连接请求，在进程管理器中找到 `poet-9000` 对应的 `ptyProcess` 实例。
5.  `ai-cli` 开始生成诗句，其输出被 `ptyProcess` 捕获。服务器将这些输出（如 "金色的叶子，"、"随风飘舞，" 等）通过 WebSocket 实时发送给客户端。
6.  **客户端** 的界面上实时显示出诗句。
7.  在任何时候，**客户端** 都可以向 `GET /commands/poet-9000/status` 发送请求，以确认命令仍在 "running"。
8.  诗句生成完毕，`ai-cli` 进程退出。
9.  **服务器** 捕获到进程退出事件，更新 `poet-9000` 的状态为 "completed"，记录 `exitCode` 和 `endTime`，然后关闭相关的 WebSocket 连接。

## 7. 下一步计划

1.  **环境搭建**: 初始化 Node.js 项目，安装 `express`, `ws`, `node-pty`, `uuid`。
2.  **HTTP 服务实现**: 搭建基础的 Express 服务器，并实现上述所有 HTTP 路由。
3.  **进程管理器实现**: 创建一个模块用于管理所有子进程的状态。
4.  **WebSocket 服务实现**: 将 WebSocket 服务器与 HTTP 服务器集成，并实现流式转发逻辑。
5.  **错误处理与日志**: 完善全局的错误处理和日志记录。
6.  **测试**: 编写单元测试和集成测试，确保服务稳定可靠。
