import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import config

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ToolExecutor:
    """
    Core Execution Sandbox for Innvo.
    Executes Python scripts, shell commands, file operations,
    and system status queries across Windows, Linux, and Android Termux.
    """
    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    # -------------------------------------------------------------
    # 1. Shell & Terminal Execution
    # -------------------------------------------------------------
    def execute_shell(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command on the host OS.
        Windows: powershell -Command ...
        Linux / Termux: bash -c ...
        """
        start = time.time()
        shell_cmd = ["powershell", "-NoProfile", "-Command", command] if config.IS_WINDOWS else ["sh", "-c", command]

        try:
            res = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            elapsed = time.time() - start
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "returncode": res.returncode,
                "elapsed_sec": round(elapsed, 3)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout} seconds.",
                "returncode": -1,
                "elapsed_sec": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "elapsed_sec": round(time.time() - start, 3)
            }

    # -------------------------------------------------------------
    # 2. Python Code Execution Sandbox
    # -------------------------------------------------------------
    def execute_python(self, code: str) -> Dict[str, Any]:
        """
        Executes a Python code block in an isolated subprocess.
        """
        start = time.time()
        try:
            res = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            elapsed = time.time() - start
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "returncode": res.returncode,
                "elapsed_sec": round(elapsed, 3)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds.",
                "returncode": -1,
                "elapsed_sec": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "elapsed_sec": round(time.time() - start, 3)
            }

    # -------------------------------------------------------------
    # 3. Cross-Platform System Metrics & Time
    # -------------------------------------------------------------
    def get_system_time(self) -> Dict[str, Any]:
        """Returns current live system date, day, and time."""
        from datetime import datetime
        now = datetime.now()
        return {
            "time": now.strftime("%I:%M:%S %p"),
            "date": now.strftime("%A, %d %B %Y"),
            "day": now.strftime("%A"),
            "timestamp": now.isoformat()
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Returns real-time CPU, RAM, Disk, and Battery metrics.
        Works across Windows, Linux, and Android Termux.
        """
        metrics = {
            "platform": "Android Termux" if config.IS_TERMUX else ("Windows" if config.IS_WINDOWS else "Linux/Mac"),
            "cpu_percent": 0.0,
            "ram_used_percent": 0.0,
            "ram_free_gb": 0.0,
            "disk_free_gb": 0.0,
            "battery_percent": None,
            "is_charging": None
        }

        # Disk usage via standard library
        try:
            target_path = Path.home()
            disk = shutil.disk_usage(target_path)
            metrics["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
            metrics["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
        except Exception:
            pass

        # CPU & RAM via psutil
        if PSUTIL_AVAILABLE:
            try:
                metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                vm = psutil.virtual_memory()
                metrics["ram_used_percent"] = vm.percent
                metrics["ram_free_gb"] = round(vm.available / (1024 ** 3), 2)
                metrics["ram_total_gb"] = round(vm.total / (1024 ** 3), 2)

                # Battery
                battery = psutil.sensors_battery()
                if battery:
                    metrics["battery_percent"] = battery.percent
                    metrics["is_charging"] = battery.power_plugged
            except Exception:
                pass

        # Android Termux Battery Fallback via termux-api
        if config.IS_TERMUX and metrics["battery_percent"] is None:
            try:
                out = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=2)
                if out.returncode == 0:
                    import json
                    b_data = json.loads(out.stdout)
                    metrics["battery_percent"] = b_data.get("percentage")
                    metrics["is_charging"] = b_data.get("status") == "CHARGING"
            except Exception:
                pass

        return metrics

    # -------------------------------------------------------------
    # 4. File System Operations
    # -------------------------------------------------------------
    def read_file(self, filepath: str, max_chars: int = 8000) -> Dict[str, Any]:
        p = Path(filepath).resolve()
        if not p.exists():
            return {"success": False, "error": f"File does not exist: {filepath}"}
        if not p.is_file():
            return {"success": False, "error": f"Path is not a file: {filepath}"}
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
            return {"success": True, "content": content, "size_bytes": p.stat().st_size}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        p = Path(filepath).resolve()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(p), "bytes_written": len(content.encode("utf-8"))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_dir(self, dirpath: str = ".") -> Dict[str, Any]:
        p = Path(dirpath).resolve()
        if not p.exists() or not p.is_dir():
            return {"success": False, "error": f"Directory not found: {dirpath}"}
        try:
            items = []
            for child in p.iterdir():
                items.append({
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "size_bytes": child.stat().st_size if child.is_file() else 0
                })
            return {"success": True, "items": items[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)}
