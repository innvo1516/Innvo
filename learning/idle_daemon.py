import time
import json
import psutil
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

import config
from internet.web_searcher import WebSearcher

logger = logging.getLogger("InnvoIdleDaemon")

CURIOSITY_TOPICS = [
    "Latest developments in quantum computing",
    "How do solid state batteries work",
    "Recent breakthroughs in nuclear fusion",
    "Autonomous robotics control systems",
    "Modern low-power embedded AI architectures",
    "History of Vedic mathematics algorithms",
    "Recent space telescope discoveries"
]

class IdleCuriosityDaemon:
    """
    Autonomous Background Curiosity Engine.
    Operates strictly when IDLE_LEARNING_ENABLED is True and the system is idle.
    DOES NOT impact real-time conversational learning, memory updates, or tool synthesis.
    """

    def __init__(self, searcher: Optional[WebSearcher] = None):
        self.searcher = searcher or WebSearcher()
        self.enabled = config.IDLE_LEARNING_ENABLED
        self.staging_file = config.DATA_DIR / "curiosity_staged.json"
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run_time = 0.0

    def enable(self):
        """Turn idle background learning ON."""
        self.enabled = True
        config.IDLE_LEARNING_ENABLED = True
        logger.info("Autonomous idle learning enabled.")

    def disable(self):
        """Turn idle background learning OFF."""
        self.enabled = False
        config.IDLE_LEARNING_ENABLED = False
        logger.info("Autonomous idle learning disabled.")

    def is_enabled(self) -> bool:
        return self.enabled

    def check_system_readiness(self) -> Tuple[bool, str]:
        """
        Verifies system conditions:
        - CPU load must be low (< 30%)
        - Battery must either be plugged in or > 60%
        """
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 40.0:
                return False, f"CPU usage high ({cpu_usage}%)"

            battery = psutil.sensors_battery()
            if battery is not None:
                if not battery.power_plugged and battery.percent < 50.0:
                    return False, f"Battery low ({battery.percent}%) without AC power"

            return True, "System ready for idle curiosity"
        except Exception as e:
            return True, f"Sensors bypassed: {e}"

    def run_single_curiosity_cycle(self, custom_topic: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Executes one autonomous curiosity search and stages learned knowledge.
        Returns the staged candidate if successful, None otherwise.
        """
        if not self.enabled:
            return None

        ready, reason = self.check_system_readiness()
        if not ready:
            logger.debug(f"Idle curiosity skipped: {reason}")
            return None

        topic = custom_topic or self._select_curiosity_topic()
        logger.info(f"Idle curiosity exploring: {topic}")

        results = self.searcher.search(topic, max_results=2)
        if not results:
            return None

        summary_snippets = " ".join([r.get("snippet", "") for r in results[:2]])
        if len(summary_snippets) < 20:
            return None

        staged_entry = {
            "topic": topic,
            "summary": summary_snippets[:300] + ("..." if len(summary_snippets) > 300 else ""),
            "sources": [r.get("url", "") for r in results if r.get("url")],
            "discovered_at": time.time(),
            "status": "pending_user_review"
        }

        self._save_to_staging(staged_entry)
        self._last_run_time = time.time()
        return staged_entry

    def _select_curiosity_topic(self) -> str:
        # Rotate through curated list based on epoch hours
        idx = int(time.time() // 3600) % len(CURIOSITY_TOPICS)
        return CURIOSITY_TOPICS[idx]

    def _save_to_staging(self, entry: Dict[str, Any]):
        staged_list = self.get_staged_curiosities()
        staged_list.append(entry)
        # Keep last 20
        if len(staged_list) > 20:
            staged_list = staged_list[-20:]
        self.staging_file.write_text(json.dumps(staged_list, indent=2), encoding="utf-8")

    def get_staged_curiosities(self) -> List[Dict[str, Any]]:
        """Returns pending facts discovered during idle mode."""
        if not self.staging_file.exists():
            return []
        try:
            return json.loads(self.staging_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def clear_staged_curiosities(self):
        """Clears staged curiosities after user review."""
        if self.staging_file.exists():
            self.staging_file.write_text("[]", encoding="utf-8")
