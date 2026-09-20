import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
from .memory_store import MemoryStore
import config

logger = logging.getLogger("InnvoApprovalEngine")

class ApprovalEngine:
    def __init__(self, memory_store: MemoryStore):
        self.store = memory_store
        self.pending_candidate: Optional[Dict[str, Any]] = None

    def extract_candidate(self, user_text: str, slm_engine=None) -> Optional[Dict[str, Any]]:
        """
        Analyzes user input in Hindi/English/Hinglish to detect learnable facts,
        habits, preferences, or rules using both fast pattern matching and dynamic LLM analysis.
        """
        text = user_text.strip()
        text_lower = text.lower()

        # Guard: Skip system queries, time, battery, tool requests from being saved as user facts
        non_fact_cues = ["time", "date", "tarikh", "samay", "kitne baje", "battery", "disk space", "storage", "ram", "cpu", "tool banao", "create tool", "run command"]
        if any(cue in text_lower for cue in non_fact_cues) and not any(w in text_lower for w in ["mera", "meri", "mujhe", "my name", "i like", "i prefer"]):
            return None

        # ---------------------------------------------------------
        # 1. Fast Pattern Matching
        # ---------------------------------------------------------
        # Rule / Direct instruction
        remember_match = re.search(r"(?:yaad\s+rakhna|remember\s+that|note\s+kar\s+lo|always\s+remember)\s+(?:ki\s+|that\s+)?(.+)", text, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            return {
                "category": "rule",
                "key": fact[:35],
                "content": fact,
                "proposal": f"Aapne bola: '{fact}'. Kya main ise apni permanent memory me save kar lu?"
            }

        # Preference: "Mujhe ... pasand hai" / "I like ..."
        pref_hindi = re.search(r"mujhe\s+(.+?)\s+pasand\s+(?:hai|hoti\s+hai)", text, re.IGNORECASE)
        if pref_hindi:
            item = pref_hindi.group(1).strip()
            fact = f"User ko '{item}' pasand hai"
            return {
                "category": "preference",
                "key": f"likes_{item[:25]}",
                "content": fact,
                "proposal": f"Maine notice kiya ki aapko '{item}' pasand hai. Kya main ise permanent memory me save kar lu?"
            }

        pref_eng = re.search(r"i\s+(?:like|love|prefer)\s+(.+)", text, re.IGNORECASE)
        if pref_eng and not re.search(r"i\s+like\s+to\s+know", text_lower):
            item = pref_eng.group(1).strip().rstrip(".!?")
            fact = f"User likes/prefers '{item}'"
            return {
                "category": "preference",
                "key": f"likes_{item[:25]}",
                "content": fact,
                "proposal": f"Maine note kiya ki you like '{item}'. Kya main ise permanent memory me save kar lu?"
            }

        # Dislike: "Mujhe ... pasand nahi"
        dislike_hindi = re.search(r"mujhe\s+(.+?)\s+pasand\s+nahi", text, re.IGNORECASE)
        if dislike_hindi:
            item = dislike_hindi.group(1).strip()
            fact = f"User ko '{item}' pasand NAHI hai"
            return {
                "category": "preference",
                "key": f"dislikes_{item[:25]}",
                "content": fact,
                "proposal": f"Aapne bataya ki aapko '{item}' pasand nahi hai. Kya main is rule ko yaad rakhu?"
            }

        # Name / Identity
        name_match = re.search(r"(?:mera\s+naam|my\s+name\s+is)\s+([A-Za-z0-9_\s]+?)(?:\s+hai|$|\.)", text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            fact = f"User ka naam {name} hai"
            return {
                "category": "user_fact",
                "key": "user_name",
                "content": fact,
                "proposal": f"Aapne apna naam '{name}' bataya. Kya main ise save kar lu taaki hamesha yaad rahe?"
            }

        # ---------------------------------------------------------
        # 2. Dynamic LLM Extraction (Non-Hardcoded)
        # ---------------------------------------------------------
        # If fast patterns didn't match and we have a working SLM, let the LLM check
        # for personal facts, routines, or instructions
        if slm_engine and slm_engine.is_model_loaded() and len(text.split()) >= 3:
            try:
                extract_prompt = (
                    "You are a Knowledge Extraction Engine. Determine if the user stated any personal fact, habit, "
                    "preference, identity, or rule about themselves in their message.\n"
                    f"User message: \"{text}\"\n\n"
                    "If yes, reply with JSON only in this format:\n"
                    "{\"has_fact\": true, \"fact\": \"<1 concise sentence in English or Hinglish>\", \"category\": \"preference|user_fact|rule\"}\n"
                    "If no, reply with:\n"
                    "{\"has_fact\": false}"
                )
                raw_json = slm_engine.generate("Output JSON only.", extract_prompt)
                # Clean code fences if present
                clean_json = re.sub(r"```(?:json)?", "", raw_json).strip()
                if "{" in clean_json and "}" in clean_json:
                    clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
                    parsed = json.loads(clean_json)
                    if parsed.get("has_fact") and parsed.get("fact"):
                        fact = parsed["fact"].strip()
                        cat = parsed.get("category", "user_fact")
                        return {
                            "category": cat,
                            "key": fact[:30],
                            "content": fact,
                            "proposal": f"Maine note kiya ki: '{fact}'. Kya main ise apni memory me save kar lu?"
                        }
            except Exception as e:
                logger.debug(f"Dynamic extraction error: {e}")

        return None

    def has_pending_candidate(self) -> bool:
        return self.pending_candidate is not None

    def get_pending_proposal(self) -> Optional[str]:
        if self.pending_candidate:
            return self.pending_candidate["proposal"]
        return None

    def stage_candidate(self, candidate: Dict[str, Any]):
        self.pending_candidate = candidate

    def process_approval_response(self, user_text: str) -> Tuple[bool, str, float]:
        """
        Handles user feedback to a proposed memory.
        Returns: (handled: bool, reply_message: str, reward: float)
        """
        if not self.pending_candidate:
            return False, "", 0.0

        clean = user_text.lower().strip().rstrip(".!?")
        cand = self.pending_candidate

        positive_cues = ["haan", "ha", "haa", "yes", "y", "save", "kar lo", "karle", "sure", "bilkul", "theek hai", "ok", "yap", "yup", "done", "thik hai"]
        negative_cues = ["nahi", "na", "no", "n", "rehne de", "rehne do", "mat karo", "cancel", "dont", "don't", "skip", "discard", "mat kar"]

        # User approved
        if any(clean == cue or clean.startswith(cue + " ") or clean.endswith(" " + cue) for cue in positive_cues):
            mem_id = self.store.save_memory(
                category=cand["category"],
                key=cand["key"],
                content=cand["content"],
                initial_q=config.REWARD_APPROVAL,
                status="approved"
            )
            self.store.log_feedback("approval", f"Approved: {cand['content']}", config.REWARD_APPROVAL, mem_id)
            self.pending_candidate = None
            return True, f"Done sir! Maine ise permanent memory me save kar liya hai. [RL Reward: +{config.REWARD_APPROVAL}]", config.REWARD_APPROVAL

        # User rejected
        if any(clean == cue or clean.startswith(cue + " ") or clean.endswith(" " + cue) for cue in negative_cues):
            self.store.log_feedback("rejection", f"Rejected: {cand['content']}", config.REWARD_REJECTION)
            self.pending_candidate = None
            return True, "Samajh gaya sir, maine ise discard kar diya. Memory me save nahi kiya.", config.REWARD_REJECTION

        # If user said something else, drop pending candidate
        self.pending_candidate = None
        return False, "", 0.0
