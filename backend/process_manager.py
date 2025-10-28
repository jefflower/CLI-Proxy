
import asyncio
import pty
import os
import subprocess
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import datetime

@dataclass
class ProcessInfo:
    execution_id: str
    command: str
    process: subprocess.Popen
    master_fd: int
    status: str = "running"
    start_time: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    end_time: Optional[datetime.datetime] = None
    exit_code: Optional[int] = None
    output: List[str] = field(default_factory=list)

class ProcessManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes: Dict[str, ProcessInfo] = {}
            cls._instance.monitor_task: Optional[asyncio.Task] = None
        return cls._instance

    async def startup(self):
        if self.monitor_task is None:
            self.monitor_task = asyncio.create_task(self.monitor_processes())

    async def shutdown(self):
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass # Expected

    def start_process(self, command: str) -> str:
        execution_id = str(uuid.uuid4())
        
        # 使用 pty.openpty() 创建伪终端
        master_fd, slave_fd = pty.openpty()
        
        # 在伪终端中启动子进程
        process = subprocess.Popen(
            command,
            shell=True,
            preexec_fn=os.setsid,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True
        )
        
        os.close(slave_fd)

        self.processes[execution_id] = ProcessInfo(
            execution_id=execution_id,
            command=command,
            process=process,
            master_fd=master_fd
        )
        return execution_id

    def get_process_info(self, execution_id: str) -> Optional[ProcessInfo]:
        return self.processes.get(execution_id)

    def stop_process(self, execution_id: str) -> bool:
        process_info = self.get_process_info(execution_id)
        if process_info and process_info.status == "running":
            try:
                os.killpg(os.getpgid(process_info.process.pid), 9)  # 使用 SIGKILL 强制终止
                process_info.status = "stopped"
                process_info.end_time = datetime.datetime.utcnow()
                return True
            except ProcessLookupError:
                # 进程可能已经结束
                process_info.status = "completed"
                return False
        return False

    def get_all_processes(self) -> List[Dict[str, Any]]:
        return [
            {
                "executionId": info.execution_id,
                "command": info.command,
                "status": info.status,
                "startTime": info.start_time.isoformat() if info.start_time else None,
            }
            for info in self.processes.values()
        ]

    async def monitor_processes(self):
        while True:
            for execution_id, process_info in list(self.processes.items()):
                if process_info.status == "running":
                    ret = process_info.process.poll()
                    if ret is not None:
                        process_info.exit_code = ret
                        process_info.end_time = datetime.datetime.utcnow()
                        process_info.status = "completed" if ret == 0 else "error"
                        os.close(process_info.master_fd) # 关闭 master fd
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                # Allow task to be cancelled
                break

process_manager = ProcessManager()
