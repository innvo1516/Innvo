import re
import json
import logging
from typing import Dict, Any, Tuple, Optional, List

import config
from rl.memory_store import MemoryStore
from rl.approval_engine import ApprovalEngine
from rl.contextual_bandit import ContextualBandit
from rl.reflexion import ReflexionEngine
from internet.web_searcher import WebSearcher
from hardware.audio_engine import AudioEngine
from tools.skill_registry import SkillRegistry
from tools.tool_creator import ToolCreator
from .slm_engine import SLMEngine
from .prompts import build_system_prompt
from .tool_prompts import format_system_prompt_with_tools

logger = logging.getLogger("InnvoOrchestrator")

class InnvoOrchestrator:
    """
    Central cognitive controller for Innvo.
    Coordinates generative AI with multi-turn context,
    tool execution, self-developing skills, RL memory, and audio.
    """
    def __init__(self, voice_enabled: bool = True, max_history_turns: int = 10):
        self.memory_store = MemoryStore()
        self.approval_engine = ApprovalEngine(self.memory_store)
        self.bandit = ContextualBandit()
        self.reflexion_engine = ReflexionEngine()
        self.searcher = WebSearcher()
        self.audio = AudioEngine(enabled=voice_enabled)
        self.slm = SLMEngine()
        
        # Tool System
        self.registry = SkillRegistry()
        self.tool_creator = ToolCreator(self.registry)

        # Multi-turn Short-Term Conversation Context
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_turns = max_history_turns

    def clear_context(self):
        """Resets active conversation context while keeping permanent RL memory and tools."""
        self.conversation_history.clear()

    def listen_and_process(self) -> Tuple[Optional[str], Dict[str, Any]]:
        transcribed = self.audio.listen()
        if not transcribed:
            return None, {"reply": "Voice clear nahi aayi sir, kya aap repeat kar sakte hain?", "pending_approval": False}

        result = self.process_input(transcribed)
        return transcribed, result

    def process_input(self, user_input: str) -> Dict[str, Any]:
        text = user_input.strip()
        if not text:
            return {"reply": "", "pending_approval": False}

        # -------------------------------------------------------------
        # STEP 1A: Check if user is answering a PENDING TOOL PROPOSAL
        # -------------------------------------------------------------
        if self.tool_creator.has_pending_proposal():
            handled, reply_msg, reward = self.tool_creator.process_approval_response(text)
            if handled:
                self.audio.speak_async(reply_msg)
                self._append_to_history("user", text)
                self._append_to_history("assistant", reply_msg)
                return {
                    "reply": reply_msg,
                    "pending_approval": False,
                    "reward": reward
                }

        # -------------------------------------------------------------
        # STEP 1B: Check if user is answering a PENDING MEMORY PROPOSAL
        # -------------------------------------------------------------
        if self.approval_engine.has_pending_candidate():
            handled, reply_msg, reward = self.approval_engine.process_approval_response(text)
            if handled:
                self.bandit.update_policy("memory_action", "propose", reward)
                self.audio.speak_async(reply_msg)
                self._append_to_history("user", text)
                self._append_to_history("assistant", reply_msg)
                return {
                    "reply": reply_msg,
                    "pending_approval": False,
                    "reward": reward
                }

        # -------------------------------------------------------------
        # STEP 2: Check for User Correction / Reflexion
        # -------------------------------------------------------------
        correction = self.reflexion_engine.detect_correction(text)
        if correction:
            self.reflexion_engine.record_correction(correction, context="Previous interaction")
            self.memory_store.log_feedback("correction", correction, config.REWARD_CORRECTION)
            reply = "Maafi chahta hoon sir, mujhse galti hui. Maine is rule ko note kar liya hai taaki aage se repeat na ho."
            self.audio.speak_async(reply)
            self._append_to_history("user", text)
            self._append_to_history("assistant", reply)
            return {"reply": reply, "pending_approval": False, "reward": config.REWARD_CORRECTION}

        # -------------------------------------------------------------
        # STEP 3: Check for Explicit Tool Synthesis Request
        # e.g., "ek naya tool banao jo ...", "create a tool to ..."
        # -------------------------------------------------------------
        tool_req_match = re.search(r"(?:tool\s+banao|create\s+a?\s*tool|develop\s+a?\s*tool|naya\s+tool)\s+(?:to\s+|for\s+|jo\s+|ki\s+)?(.+)", text, re.IGNORECASE)
        if tool_req_match:
            task = tool_req_match.group(1).strip()
            tool_info = self.tool_creator.synthesize_tool(task, self.slm)
            if tool_info:
                self.tool_creator.stage_proposal(tool_info)
                proposal = self.tool_creator.get_proposal_text()
                self.audio.speak_async(proposal)
                self._append_to_history("user", text)
                self._append_to_history("assistant", proposal)
                return {
                    "reply": f"[Tool Synthesis Success]:\n{proposal}",
                    "pending_approval": True,
                    "proposal": proposal
                }

        # -------------------------------------------------------------
        # STEP 4: Direct Tool Execution Shortcuts (Fast System Metrics)
        # -------------------------------------------------------------
        text_lower = text.lower()
        tool_output_context = ""
        used_tool_name = None

        if any(w in text_lower for w in ["time", "date", "tarikh", "samay", "kitne baje", "current time", "what time", "today date", "aaj kaun sa din", "what day"]):
            m = self.registry.execute("get_system_time")
            if m["success"]:
                used_tool_name = "get_system_time"
                d = m["data"]
                tool_output_context = f"[Live System Date & Time: {d['date']}, {d['time']}]"

        elif any(w in text_lower for w in ["battery", "battery kitni hai", "battery percent", "charging"]):
            m = self.registry.execute("get_system_metrics")
            if m["success"]:
                used_tool_name = "get_system_metrics"
                b = m["data"]["battery_percent"]
                ch = "charging" if m["data"]["is_charging"] else "not charging"
                tool_output_context = f"[Live Battery Status: {b}% ({ch})]"

        elif any(w in text_lower for w in ["ram", "cpu", "disk space", "storage", "free space", "system status"]):
            m = self.registry.execute("get_system_metrics")
            if m["success"]:
                used_tool_name = "get_system_metrics"
                d = m["data"]
                tool_output_context = (
                    f"[Live System Status: CPU: {d['cpu_percent']}%, RAM Used: {d['ram_used_percent']}% "
                    f"(Free: {d['ram_free_gb']} GB), Disk Free: {d['disk_free_gb']} GB]"
                )

        # -------------------------------------------------------------
        # STEP 5: Check for Learnable Facts / Preferences
        # -------------------------------------------------------------
        candidate = self.approval_engine.extract_candidate(text, slm_engine=self.slm)
        if candidate:
            self.approval_engine.stage_candidate(candidate)

        # -------------------------------------------------------------
        # STEP 6: Policy & Memory Retrieval
        # -------------------------------------------------------------
        tone = self.bandit.select_tone()
        should_search = self.bandit.should_search(text) and not tool_output_context

        search_query = text
        if self.conversation_history:
            last_user_turn = [m["content"] for m in self.conversation_history if m["role"] == "user"]
            if last_user_turn:
                search_query = f"{last_user_turn[-1]} {text}"

        relevant_memories = self.memory_store.get_relevant_memories(search_query, top_k=3)
        active_constraints = self.reflexion_engine.get_active_constraints()

        # -------------------------------------------------------------
        # STEP 7: Internet Search (if needed)
        # -------------------------------------------------------------
        internet_context = ""
        if should_search:
            internet_context = self.searcher.get_summary_context(text)

        # Combine tools and grounding
        grounding = ""
        if tool_output_context:
            grounding += tool_output_context + "\n"
        if internet_context:
            grounding += internet_context + "\n"

        # -------------------------------------------------------------
        # STEP 8: Prompt Building & Generation
        # -------------------------------------------------------------
        base_system_prompt = build_system_prompt(
            tone=tone,
            memories=relevant_memories,
            constraints=active_constraints
        )
        tools_summary = self.registry.get_tool_signatures_prompt()
        full_system_prompt = format_system_prompt_with_tools(base_system_prompt, tools_summary)

        self._append_to_history("user", text)

        base_reply = self.slm.chat(
            system_prompt=full_system_prompt,
            history=self.conversation_history,
            context=grounding
        )

        # -------------------------------------------------------------
        # STEP 9: Check if SLM output contained a dynamic tool call
        # e.g. ```tool {"tool": "...", "args": {...}} ```
        # -------------------------------------------------------------
        tool_call_match = re.search(r"```tool\s*(.+?)\s*```", base_reply, re.DOTALL)
        if tool_call_match:
            try:
                call_data = json.loads(tool_call_match.group(1).strip())
                t_name = call_data.get("tool")
                t_args = call_data.get("args", {})
                base_reply = re.sub(r"```tool\s*.+?\s*```", "", base_reply).strip()

                tool_res = self.registry.execute(t_name, **t_args)

                # AUTONOMOUS SELF-DEVELOPMENT: If tool was not found, synthesize it on the fly!
                if not tool_res.get("success") and "not found" in str(tool_res.get("error", "")).lower():
                    task_desc = f"Create a Python tool named '{t_name}' to satisfy: '{text}'"
                    tool_info = self.tool_creator.synthesize_tool(task_desc, self.slm)
                    if tool_info:
                        self.registry.register_tool(tool_info["name"], tool_info["description"], tool_info["code"], initial_q=1.0)
                        tool_res = self.registry.execute(tool_info["name"], **t_args)
                        self.tool_creator.stage_proposal(tool_info)
                        base_reply += f"\n[Self-Developed Tool '{tool_info['name']}']: {tool_res.get('data') or tool_res.get('stdout') or tool_res.get('output')}"
                        proposal_msg = self.tool_creator.get_proposal_text()
                        base_reply += f"\n\n[Skill Learning Proposal]: {proposal_msg}"
                        self._append_to_history("assistant", base_reply)
                        self.audio.speak_async(base_reply)
                        return {
                            "reply": base_reply,
                            "pending_approval": True,
                            "proposal": proposal_msg,
                            "tool_used": tool_info["name"]
                        }

                if tool_res.get("success"):
                    base_reply += f"\n[Tool Output]: {tool_res.get('data') or tool_res.get('stdout') or tool_res.get('output')}"
                else:
                    base_reply += f"\n[Tool Error]: {tool_res.get('error') or tool_res.get('stderr')}"
            except Exception as e:
                logger.debug(f"Failed to parse tool call: {e}")

        # -------------------------------------------------------------
        # STEP 10: Append Approval Proposal if Candidate was detected
        # -------------------------------------------------------------
        final_reply = base_reply
        proposal_text = None

        if candidate:
            proposal_text = candidate["proposal"]
            final_reply += f"\n\n[Innvo Learning Suggestion]: {proposal_text} (Haan/Nahi)"

        self._append_to_history("assistant", base_reply)

        # -------------------------------------------------------------
        # STEP 11: Voice Output
        # -------------------------------------------------------------
        speech_text = base_reply
        if proposal_text:
            speech_text += f". {proposal_text}"
        self.audio.speak_async(speech_text)

        return {
            "reply": final_reply,
            "pending_approval": candidate is not None,
            "proposal": proposal_text,
            "tool_used": used_tool_name,
            "search_used": bool(internet_context),
            "tone": tone
        }

    def _append_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history_turns:
            self.conversation_history.pop(0)
