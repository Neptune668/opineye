"""单功能应用子进程生命周期管理（核心模块）。

每个单功能应用以独立子进程运行（python apps/{app_name}_app.py），
由 ProcessManager 统一管理启停、状态采集与输出采集。

应用状态机：
    stopped → starting → running → stopping → stopped
                                  └───────→ failed（进程异常退出）
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import sys
from typing import IO

from app import settings

logger = logging.getLogger(__name__)

# 应用名合法性校验（禁止路径穿越等非法字符）
APP_NAME_PATTERN = re.compile(r"^[a-z_]+$")

# 允许启动的状态（其余状态拒绝启动，避免重复启动）
STARTABLE_STATES = {"stopped", "failed"}

# 停止等待超时（秒），超时后强杀
STOP_TIMEOUT = 5.0


class AppProc:
    """子进程运行时上下文。"""

    __slots__ = ("proc", "status", "log_f", "pump_task")

    def __init__(
        self,
        proc: "asyncio.subprocess.Process | None",
        status: str,
        log_f: "IO[str] | None",
        pump_task: "asyncio.Task[None] | None",
    ) -> None:
        self.proc = proc
        self.status = status
        self.log_f = log_f
        self.pump_task = pump_task


class ProcessManager:
    """单功能应用子进程管理器。"""

    def __init__(self):
        self._procs: dict[str, AppProc] = {}

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    def status(self, app_name: str) -> str:
        """查询单个应用状态。"""
        ctx = self._procs.get(app_name)
        return ctx.status if ctx else "stopped"

    def all_status(self) -> dict[str, str]:
        """查询全部已注册应用状态。"""
        return {name: ctx.status for name, ctx in self._procs.items()}

    # ------------------------------------------------------------------
    # 启停
    # ------------------------------------------------------------------
    async def start(self, app_name: str) -> bool:
        """启动子进程，返回是否成功。"""
        if not APP_NAME_PATTERN.match(app_name):
            logger.warning("非法应用名：%s", app_name)
            return False

        current = self.status(app_name)
        if current not in STARTABLE_STATES:
            logger.warning("应用 %s 当前状态 %s，拒绝启动", app_name, current)
            return False

        script = settings.APPS_DIR / f"{app_name}_app.py"
        if not script.exists():
            logger.error("应用脚本不存在：%s", script)
            self._procs[app_name] = AppProc(
                proc=None, status="failed", log_f=None, pump_task=None
            )
            return False

        self._procs[app_name] = AppProc(
            proc=None, status="starting", log_f=None, pump_task=None
        )

        try:
            await self._launch(app_name)
            return True
        except Exception as exc:  # 启动失败兜底
            logger.exception("应用 %s 启动失败", app_name)
            ctx = self._procs.get(app_name)
            if ctx:
                ctx.status = "failed"
            await self._broadcast_error(app_name, f"启动失败: {exc}")
            return False

    async def stop(self, app_name: str) -> bool:
        """停止子进程，返回是否成功。"""
        ctx = self._procs.get(app_name)
        if ctx is None or ctx.status in {"stopped", "failed"}:
            logger.info("应用 %s 已停止或不存在", app_name)
            return True

        ctx.status = "stopping"
        proc = ctx.proc
        if proc is None:
            ctx.status = "stopped"
            return True

        try:
            self._terminate(proc)
            try:
                await asyncio.wait_for(proc.wait(), timeout=STOP_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning("应用 %s 停止超时，强制终止", app_name)
                proc.kill()
                await proc.wait()
        except ProcessLookupError:
            pass  # 进程已退出

        # 取消输出泵任务
        if ctx.pump_task:
            ctx.pump_task.cancel()
            try:
                await ctx.pump_task
            except asyncio.CancelledError:
                pass

        ctx.status = "stopped"
        await self._broadcast_status(app_name, "stopped")
        return True

    # ------------------------------------------------------------------
    # 输出读取
    # ------------------------------------------------------------------
    async def read_output(self, app_name: str) -> str:
        """读取应用最近一次文本输出（outputs/{app_name}/latest.txt）。"""
        path = settings.OUTPUTS_DIR / app_name / "latest.txt"
        if not path.exists():
            return ""
        return await asyncio.to_thread(path.read_text, encoding="utf-8")

    async def read_log(self, app_name: str, tail: int = 200) -> list[str]:
        """读取应用日志尾部（runtime/apps/{app_name}.log）。"""
        path = settings.RUNTIME_APPS_DIR / f"{app_name}.log"
        if not path.exists():
            return []
        lines = await asyncio.to_thread(path.read_text, encoding="utf-8")
        return lines.splitlines()[-tail:]

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------
    async def _launch(self, app_name: str) -> None:
        """创建子进程并启动输出泵。"""
        log_path = settings.RUNTIME_APPS_DIR / f"{app_name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_f = open(log_path, "a", encoding="utf-8")

        # 注入 PYTHONPATH，确保 worker 脚本能 import app 模块
        env = dict(os.environ)
        existing_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{settings.BACKEND_DIR}{os.pathsep}{existing_path}"
            if existing_path
            else str(settings.BACKEND_DIR)
        )

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(settings.APPS_DIR / f"{app_name}_app.py"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # 错误合并进标准输出
            cwd=str(settings.BACKEND_DIR),
            env=env,
        )

        async def _pump():
            try:
                assert proc.stdout is not None
                async for line in proc.stdout:
                    text = line.decode("utf-8", errors="ignore")
                    log_f.write(text)
                    log_f.flush()
                    await self._broadcast_output(app_name, text)
            except asyncio.CancelledError:
                pass  # 停止时主动取消，正常退出
            finally:
                log_f.close()
                await proc.wait()
                exit_code = proc.returncode
                if exit_code == 0:
                    await self._save_latest_output(app_name)
                    new_status = "stopped"
                else:
                    new_status = "failed"
                self._update_status(app_name, new_status)
                await self._broadcast_status(app_name, new_status)
                if exit_code != 0:
                    await self._broadcast_error(
                        app_name, f"进程异常退出，退出码 {exit_code}"
                    )

        pump_task = asyncio.create_task(_pump())
        self._procs[app_name] = AppProc(
            proc=proc, status="running", log_f=log_f, pump_task=pump_task
        )
        await self._broadcast_status(app_name, "running")
        logger.info("应用 %s 已启动（pid=%s）", app_name, proc.pid)

    @staticmethod
    def _terminate(proc: asyncio.subprocess.Process) -> None:
        """跨平台终止信号：Windows terminate，POSIX SIGTERM。"""
        if sys.platform == "win32":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGTERM)

    async def _save_latest_output(self, app_name: str) -> None:
        """应用正常退出时，将日志尾部写入 latest.txt。"""
        try:
            log_path = settings.RUNTIME_APPS_DIR / f"{app_name}.log"
            text = ""
            if log_path.exists():
                text = await asyncio.to_thread(log_path.read_text, encoding="utf-8")
            out_path = settings.OUTPUTS_DIR / app_name / "latest.txt"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(out_path.write_text, text, encoding="utf-8")
        except Exception as exc:
            logger.exception("保存 %s 输出失败", app_name)

    def _update_status(self, app_name: str, status: str) -> None:
        ctx = self._procs.get(app_name)
        if ctx:
            ctx.status = status

    # ------------------------------------------------------------------
    # 广播（WebSocket 依赖 ws_manager，此处做惰性导入避免循环依赖）
    # ------------------------------------------------------------------
    async def _broadcast_status(self, app_name: str, status: str) -> None:
        try:
            from app.core.ws_manager import ws_manager  # type: ignore[reportImplicitRelativeImport]
            await ws_manager.broadcast(
                {"type": "app_status", "data": {"app_name": app_name, "status": status}}
            )
        except Exception:
            pass

    async def _broadcast_output(self, app_name: str, output_text: str) -> None:
        try:
            from app.core.ws_manager import ws_manager  # type: ignore[reportImplicitRelativeImport]
            await ws_manager.broadcast(
                {
                    "type": "app_output",
                    "data": {"app_name": app_name, "output_text": output_text},
                }
            )
        except Exception:
            pass

    async def _broadcast_error(self, module_name: str, error_message: str) -> None:
        try:
            from app.core.ws_manager import ws_manager  # type: ignore[reportImplicitRelativeImport]
            await ws_manager.broadcast(
                {
                    "type": "error",
                    "data": {"module_name": module_name, "error_message": error_message},
                }
            )
        except Exception:
            pass


# 全局单例
process_manager = ProcessManager()
