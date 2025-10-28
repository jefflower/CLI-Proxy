
import asyncio
import os
import fcntl
from fastapi import FastAPI, WebSocket, HTTPException, status, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from process_manager import process_manager, ProcessInfo

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await process_manager.startup()
    yield
    # Clean up resources if needed

app = FastAPI(lifespan=lifespan)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    message: str
    executionId: str

class StatusResponse(BaseModel):
    executionId: str
    command: str
    status: str
    startTime: str
    endTime: str = None
    exitCode: int = None

class AllProcessResponse(BaseModel):
    executionId: str
    command: str
    status: str
    startTime: str

@app.post("/commands/start", response_model=CommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_command(request: CommandRequest):
    execution_id = process_manager.start_process(request.command)
    return {
        "message": "Command execution started.",
        "executionId": execution_id
    }

@app.get("/commands/{execution_id}/status", response_model=StatusResponse)
async def get_status(execution_id: str):
    info = process_manager.get_process_info(execution_id)
    if not info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution ID not found.")
    
    return {
        "executionId": info.execution_id,
        "command": info.command,
        "status": info.status,
        "startTime": info.start_time.isoformat() if info.start_time else None,
        "endTime": info.end_time.isoformat() if info.end_time else None,
        "exitCode": info.exit_code
    }

@app.post("/commands/{execution_id}/stop")
async def stop_command(execution_id: str):
    if not process_manager.stop_process(execution_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution ID not found or process already stopped.")
    return {"message": "Command termination signal sent.", "executionId": execution_id}

@app.get("/commands", response_model=List[AllProcessResponse])
async def list_all_commands():
    return process_manager.get_all_processes()

@app.websocket("/commands/{execution_id}/stream")
async def websocket_stream(websocket: WebSocket, execution_id: str):
    await websocket.accept()
    info = process_manager.get_process_info(execution_id)

    if not info or info.status != "running":
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Execution ID not found or process is not running.")
        return

    master_fd = info.master_fd
    
    # 设置文件描述符为非阻塞
    fl = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    try:
        while info.status == "running":
            try:
                data = os.read(master_fd, 1024)
                if data:
                    await websocket.send_text(data.decode(errors='replace'))
            except BlockingIOError:
                # 没有数据可读，短暂等待
                pass
            await asyncio.sleep(0.1) # 防止CPU占用过高
        
        # 进程结束后，发送最后可能剩余的数据
        try:
            data = os.read(master_fd, 1024)
            if data:
                await websocket.send_text(data.decode(errors='replace'))
        except: # noqa
            pass

        await websocket.send_text("\n[EOF]")
        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected from {execution_id}")
    except Exception as e:
        print(f"An error occurred in websocket for {execution_id}: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
