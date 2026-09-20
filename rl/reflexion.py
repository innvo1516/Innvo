import json
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import config

class ReflexionEngine:
    """
    Reflexion Engine:
    Tracks mistakes and user corrections. Stores them as high-priority
    constraints in reflexions.json so Innvo avoids making repeated mistakes.
    """
    def __init__(self, reflexion_file=None):
        self.reflexion_file = Path(reflexion_file or config.RL_REFLEXION_PATH)
        self.reflexions: List[Dict[str, Any]] = self._load_reflexions()

    def _load_reflexions(self) -> List[Dict[str, Any]]:
        if self.reflexion_file.exists():
            try:
                with open(self.reflexion_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_reflexions(self):
        try:
            with open(self.reflexion_file, "w", encoding="utf-8") as f:
                json.dump(self.reflexions, f, indent=2)
        except Exception:
            pass

    def detect_correction(self, user_text: str) -> Optional[str]:
        """
        Detects if the user is pointing out a mistake or correcting Innvo.
        """
        text = user_text.lower().strip()
        correction_patterns = [
            r"(?:galat\s+hai|galat\s+bol\s+rahe\s+ho|that's\s+wrong|you\s+are\s+wrong|not\s+correct)",
            r"(?:aisa\s+nahi\s+hai|maine\s+ye\s+nahi\s+kaha|actually\s+aisa\s+hai)",
            r"(?:wrong\s+answer|bekaar\s+answer|galti\s+ho\s+gayi)"
        ]
        for pat in correction_patterns:
            if re.search(pat, text):
                return user_text.strip()
        return None

    def record_correction(self, correction_detail: str, context: str = "") -> Dict[str, Any]:
        entry = {
            "id": len(self.reflexions) + 1,
            "correction": correction_detail,
            "context": context,
            "timestamp": time.time(),
            "active": True
        }
        self.reflexions.append(entry)
        self._save_reflexions()
        return entry

    def get_active_constraints(self) -> List[str]:
        """Returns lessons learned to inject into system prompt."""
        return [f"Rule: {r['correction']}" for r in self.reflexions[-5:] if r.get("active", True)]
