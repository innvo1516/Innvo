import json
import random
from pathlib import Path
from typing import Dict, Any, Tuple
import config

class ContextualBandit:
    """
    Lightweight Contextual Multi-Armed Bandit that optimizes Innvo's:
    1. Tone Policy (chill_hinglish vs crisp_concise vs detailed_guide)
    2. Search Decision (search vs local_only)
    Runs in <1ms without any heavy machine learning frameworks.
    """
    def __init__(self, policy_file=None):
        self.policy_file = Path(policy_file or config.RL_POLICY_PATH)
        self.tones = ["chill_hinglish", "crisp_concise", "detailed_guide"]
        self.search_actions = ["search", "local_only"]
        self.q_table: Dict[str, Dict[str, float]] = self._load_policy()

    def _default_policy(self) -> Dict[str, Dict[str, float]]:
        return {
            "tone": {
                "chill_hinglish": 1.2,    # Default favorable bias for natural buddy tone
                "crisp_concise": 1.0,
                "detailed_guide": 0.8
            },
            "search_need": {
                "search": 1.0,
                "local_only": 1.0
            }
        }

    def _load_policy(self) -> Dict[str, Dict[str, float]]:
        if self.policy_file.exists():
            try:
                with open(self.policy_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        policy = self._default_policy()
        self._save_policy(policy)
        return policy

    def _save_policy(self, policy: Dict[str, Dict[str, float]]):
        try:
            with open(self.policy_file, "w", encoding="utf-8") as f:
                json.dump(policy, f, indent=2)
        except Exception:
            pass

    def select_tone(self) -> str:
        """Epsilon-greedy selection of conversational tone."""
        if random.random() < config.RL_EPSILON:
            # Exploration
            return random.choice(self.tones)
        # Exploitation
        tone_scores = self.q_table.get("tone", {})
        return max(self.tones, key=lambda t: tone_scores.get(t, 0.0))

    def should_search(self, user_query: str) -> bool:
        """
        Determines if real-time web search should be executed.
        Combines intent heuristics with RL search action values.
        """
        q = user_query.lower()
        # Direct indicator keywords
        explicit_search_cues = [
            "search", "google", "kya chal raha", "current", "latest", "today", "aaj ka",
            "weather", "score", "price", "news", "kab hai", "who is", "what is", "kaun hai"
        ]
        has_cue = any(cue in q for cue in explicit_search_cues)

        if has_cue:
            return True

        # Check RL search weights
        search_scores = self.q_table.get("search_need", {})
        if random.random() < config.RL_EPSILON:
            return random.choice([True, False])
        return search_scores.get("search", 1.0) > search_scores.get("local_only", 1.0)

    def update_policy(self, dimension: str, action: str, reward: float):
        """
        Applies online Q-learning update:
        Q(s, a) <- Q(s, a) + alpha * [Reward - Q(s, a)]
        """
        if dimension not in self.q_table:
            self.q_table[dimension] = {}
        current_val = self.q_table[dimension].get(action, 1.0)
        new_val = current_val + config.RL_ALPHA * (reward - current_val)
        self.q_table[dimension][action] = round(new_val, 4)
        self._save_policy(self.q_table)

    def get_status(self) -> Dict[str, Any]:
        return {
            "top_tone": max(self.tones, key=lambda t: self.q_table.get("tone", {}).get(t, 0.0)),
            "tone_q_values": self.q_table.get("tone", {}),
            "search_q_values": self.q_table.get("search_need", {})
        }
