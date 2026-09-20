import os
import sys
import json
import time
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional
import config
from .executor import ToolExecutor

class SkillRegistry:
    """
    Manages Innvo's dynamic tool library.
    Skills are stored in tools/dynamic/ and registered with RL Q-values.
    """
    def __init__(self, registry_file=None, dynamic_dir=None):
        self.executor = ToolExecutor()
        self.dynamic_dir = Path(dynamic_dir or (config.BASE_DIR / "tools" / "dynamic"))
        self.dynamic_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = Path(registry_file or (config.DATA_DIR / "skills.json"))
        self.skills: Dict[str, Dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default built-in system primitives
        default_skills = {
            "get_system_metrics": {
                "name": "get_system_metrics",
                "description": "Returns current CPU, RAM, Disk space, and Battery metrics.",
                "type": "builtin",
                "q_value": 1.0,
                "invocations": 0
            },
            "run_terminal_command": {
                "name": "run_terminal_command",
                "description": "Runs a shell command (PowerShell on Windows, Bash on Linux/Termux).",
                "type": "builtin",
                "q_value": 1.0,
                "invocations": 0
            },
            "execute_python_code": {
                "name": "execute_python_code",
                "description": "Executes a Python code block and returns stdout/stderr.",
                "type": "builtin",
                "q_value": 1.0,
                "invocations": 0
            }
        }
        self._save_registry(default_skills)
        return default_skills

    def _save_registry(self, skills_dict: Dict[str, Dict[str, Any]]):
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(skills_dict, f, indent=2)
        except Exception:
            pass

    def register_tool(self, name: str, description: str, code: str, initial_q: float = 1.0) -> bool:
        """
        Saves a newly synthesized tool to tools/dynamic/<name>.py
        and logs it in skills.json with an initial Q-value.
        """
        clean_name = name.lower().strip().replace(" ", "_").replace("-", "_")
        file_path = self.dynamic_dir / f"{clean_name}.py"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            self.skills[clean_name] = {
                "name": clean_name,
                "description": description,
                "type": "dynamic",
                "file_path": str(file_path),
                "q_value": initial_q,
                "invocations": 0,
                "created_at": time.time(),
                "last_run_success": True
            }
            self._save_registry(self.skills)
            return True
        except Exception:
            return False

    def list_skills(self) -> List[Dict[str, Any]]:
        return list(self.skills.values())

    def get_tool_signatures_prompt(self) -> str:
        """Generates formatted documentation of available tools for the SLM."""
        lines = ["[Available System & Learned Tools]"]
        for s in self.skills.values():
            lines.append(f"- {s['name']}: {s['description']} (Q-Score: {s.get('q_value', 1.0):.2f})")
        return "\n".join(lines)

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatches execution to either built-in primitives or dynamic scripts.
        """
        clean_name = tool_name.lower().strip()
        if clean_name not in self.skills:
            return {"success": False, "error": f"Tool '{tool_name}' not found in registry."}

        tool_meta = self.skills[clean_name]
        tool_meta["invocations"] = tool_meta.get("invocations", 0) + 1

        # 1. Built-in Primitives
        if clean_name == "get_system_metrics":
            res = self.executor.get_system_metrics()
            self._save_registry(self.skills)
            return {"success": True, "data": res}

        elif clean_name == "run_terminal_command":
            cmd = kwargs.get("command", "")
            res = self.executor.execute_shell(cmd)
            self._save_registry(self.skills)
            return res

        elif clean_name == "execute_python_code":
            code = kwargs.get("code", "")
            res = self.executor.execute_python(code)
            self._save_registry(self.skills)
            return res

        # 2. Dynamic Learned Tools
        if tool_meta.get("type") == "dynamic":
            file_path = Path(tool_meta["file_path"])
            if not file_path.exists():
                return {"success": False, "error": f"Tool file missing: {file_path}"}

            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(clean_name, str(file_path))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # Expecting a run() function in the module
                if hasattr(mod, "run"):
                    result = mod.run(**kwargs)
                    tool_meta["last_run_success"] = True
                    self._save_registry(self.skills)
                    return {"success": True, "output": result}
                else:
                    return {"success": False, "error": f"Module {clean_name} has no run() function."}
            except Exception as e:
                tool_meta["last_run_success"] = False
                # Penalize Q-value on execution failure
                tool_meta["q_value"] = max(-1.0, tool_meta.get("q_value", 1.0) - config.RL_ALPHA)
                self._save_registry(self.skills)
                return {"success": False, "error": f"Execution error in {clean_name}: {e}"}

        return {"success": False, "error": "Unknown tool execution path."}

    def update_tool_q(self, tool_name: str, reward: float):
        clean_name = tool_name.lower().strip()
        if clean_name in self.skills:
            current_q = self.skills[clean_name].get("q_value", 1.0)
            new_q = current_q + config.RL_ALPHA * (reward - current_q)
            self.skills[clean_name]["q_value"] = round(max(-1.0, min(1.0, new_q)), 3)
            self._save_registry(self.skills)
