"""
Innvo Tool-Calling and Agentic Decision Prompts
"""

TOOL_INSTRUCTION = """
You have access to a real execution environment with built-in and dynamic tools.

Tool Invocations:
If the user's request requires executing a system tool, inspection, or running code, you can trigger a tool by writing a JSON block:
```tool
{"tool": "<tool_name>", "args": { ... }}
```

Built-in Tools:
1. `get_system_metrics`: Returns real-time CPU, RAM, Disk, and Battery info.
2. `run_terminal_command`: Runs shell command (PowerShell / Bash). args: `{"command": "..."}`
3. `execute_python_code`: Runs a Python code block. args: `{"code": "..."}`

If a specific task requires an automated script that doesn't exist yet, you can solve it or write code using standard Python.
"""

def format_system_prompt_with_tools(base_prompt: str, available_tools_str: str) -> str:
    return f"{base_prompt}\n\n{TOOL_INSTRUCTION}\n\n{available_tools_str}"
