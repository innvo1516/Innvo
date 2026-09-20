import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
import config
from .executor import ToolExecutor
from .skill_registry import SkillRegistry

logger = logging.getLogger("InnvoToolCreator")

class ToolCreator:
    """
    Self-Development Engine for Innvo.
    Synthesizes new Python tools on the fly, tests them in a sandbox,
    and stages them for user discussion & approval.
    """
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.executor = ToolExecutor()
        self.pending_tool_proposal: Optional[Dict[str, Any]] = None

    def synthesize_tool(self, task_description: str, slm_engine) -> Optional[Dict[str, Any]]:
        """
        Uses the local SLM to write a self-contained Python tool for a requested task.
        """
        if not slm_engine or not slm_engine.is_model_loaded():
            return None

        platform_hint = "Android Termux (Linux environment)" if config.IS_TERMUX else ("Windows" if config.IS_WINDOWS else "Linux/Mac")

        system_prompt = (
            "You are an expert Python tool developer for an AI assistant. "
            "Write a self-contained Python module that accomplishes the user's task.\n"
            f"Target Environment: {platform_hint}.\n\n"
            "STRICT RULES:\n"
            "1. You MUST define a function: `def run(**kwargs)` that returns a string or dictionary.\n"
            "2. Prioritize standard library (os, sys, shutil, pathlib, urllib, json, subprocess, math) or psutil, requests.\n"
            "3. Catch all exceptions inside run() and return error strings rather than crashing.\n"
            "4. Return ONLY valid Python code inside ```python ``` markdown blocks. No explanations."
        )

        user_prompt = f"Task: {task_description}\nCreate a clean Python tool with def run(**kwargs)."

        try:
            raw_output = slm_engine.generate(system_prompt, user_prompt)
            # Extract code block
            code_match = re.search(r"```(?:python)?\s*(.+?)\s*```", raw_output, re.DOTALL)
            code = code_match.group(1).strip() if code_match else raw_output.strip()

            # Ensure run function exists
            if "def run(" not in code:
                return None

            # Generate short tool name
            name_prompt = f"Give a 1-to-2 word pythonic function name for this task: '{task_description}'. Example: disk_checker, ip_fetcher. Reply with name only."
            name_raw = slm_engine.generate("Output name only.", name_prompt)
            clean_name = re.sub(r"[^a-zA-Z0-9_]", "", name_raw.strip().lower())
            if not clean_name:
                clean_name = "custom_tool_" + str(int(time.time()) % 10000)

            # ---------------------------------------------------------
            # Sandbox Test Execution
            # ---------------------------------------------------------
            test_harness = f"{code}\n\nif __name__ == '__main__':\n    res = run()\n    print('TEST_OK:', res)\n"
            test_res = self.executor.execute_python(test_harness)

            if not test_res["success"] or "TEST_OK:" not in test_res["stdout"]:
                logger.debug(f"Initial tool test failed: {test_res['stderr']}")
                # Attempt 1 self-repair
                repair_prompt = (
                    f"The code failed with error:\n{test_res['stderr']}\n\n"
                    f"Original Code:\n{code}\n\n"
                    "Fix the code. Return ONLY valid Python code inside ```python ``` blocks."
                )
                repaired_raw = slm_engine.generate(system_prompt, repair_prompt)
                rep_match = re.search(r"```(?:python)?\s*(.+?)\s*```", repaired_raw, re.DOTALL)
                if rep_match:
                    code = rep_match.group(1).strip()
                    test_harness = f"{code}\n\nif __name__ == '__main__':\n    res = run()\n    print('TEST_OK:', res)\n"
                    test_res = self.executor.execute_python(test_harness)

            if not test_res["success"]:
                return None

            test_output = test_res["stdout"].replace("TEST_OK:", "").strip()

            return {
                "name": clean_name,
                "description": task_description,
                "code": code,
                "test_output": test_output
            }

        except Exception as e:
            logger.error(f"Error during tool synthesis: {e}")
            return None

    def stage_proposal(self, tool_info: Dict[str, Any]):
        self.pending_tool_proposal = tool_info

    def has_pending_proposal(self) -> bool:
        return self.pending_tool_proposal is not None

    def get_proposal_text(self) -> Optional[str]:
        if self.pending_tool_proposal:
            p = self.pending_tool_proposal
            return (
                f"Maine '{p['description']}' ke liye ek naya tool '{p['name']}' develop kiya hai. "
                f"Test output: '{p['test_output']}'. "
                "Kya main is tool ko apni permanent skill library me save kar lu? (Haan/Nahi)"
            )
        return None

    def process_approval_response(self, user_text: str) -> Tuple[bool, str, float]:
        """
        Handles user feedback to a proposed tool.
        Returns: (handled: bool, reply_message: str, reward: float)
        """
        if not self.pending_tool_proposal:
            return False, "", 0.0

        clean = user_text.lower().strip().rstrip(".!?")
        cand = self.pending_tool_proposal

        positive_cues = ["haan", "ha", "haa", "yes", "y", "save", "kar lo", "karle", "sure", "bilkul", "theek hai", "ok", "thik hai"]
        negative_cues = ["nahi", "na", "no", "n", "rehne de", "rehne do", "mat karo", "cancel", "dont", "don't", "skip", "discard"]

        # Approved
        if any(clean == cue or clean.startswith(cue + " ") or clean.endswith(" " + cue) for cue in positive_cues):
            success = self.registry.register_tool(
                name=cand["name"],
                description=cand["description"],
                code=cand["code"],
                initial_q=config.REWARD_APPROVAL
            )
            self.pending_tool_proposal = None
            if success:
                return True, f"Done sir! Tool '{cand['name']}' ko permanent skill library me register kar diya hai. [Q-Score: +1.0]", config.REWARD_APPROVAL
            else:
                return True, "Tool register karne me error aaya sir.", 0.0

        # Rejected
        if any(clean == cue or clean.startswith(cue + " ") or clean.endswith(" " + cue) for cue in negative_cues):
            self.pending_tool_proposal = None
            return True, "Samajh gaya sir, maine is tool ko discard kar diya.", config.REWARD_REJECTION

        self.pending_tool_proposal = None
        return False, "", 0.0
