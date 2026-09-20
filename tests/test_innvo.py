import sys
import os
import shutil
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
TEST_DATA_DIR = config.BASE_DIR / "data_test"
TEST_DATA_DIR.mkdir(exist_ok=True)
config.RL_DB_PATH = TEST_DATA_DIR / "test_memory.db"
config.RL_POLICY_PATH = TEST_DATA_DIR / "test_policy.json"
config.RL_REFLEXION_PATH = TEST_DATA_DIR / "test_reflexion.json"

from brain.orchestrator import InnvoOrchestrator
from internet.web_searcher import WebSearcher
from rl.memory_store import MemoryStore
from rl.approval_engine import ApprovalEngine
from rl.contextual_bandit import ContextualBandit

class TestInnvoCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orchestrator = InnvoOrchestrator(voice_enabled=False)

    @classmethod
    def tearDownClass(cls):
        # Cleanup test files safely on Windows
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_01_candidate_detection_and_approval(self):
        """Test learning a fact with human approval."""
        # 1. User mentions a preference in Hinglish
        res1 = self.orchestrator.process_input("Mujhe Black Coffee pasand hai")
        self.assertTrue(res1["pending_approval"], "Should detect learnable preference")
        self.assertIn("Black Coffee", res1["reply"], "Should mention Black Coffee in proposal")

        # 2. User approves: "Haan save kar le"
        res2 = self.orchestrator.process_input("Haan save kar le")
        self.assertFalse(res2["pending_approval"])
        self.assertIn("Done sir", res2["reply"])
        self.assertEqual(res2["reward"], config.REWARD_APPROVAL)

        # 3. Verify memory is in SQLite with high Q-value
        active = self.orchestrator.memory_store.list_all_active()
        coffee_mems = [m for m in active if "Black Coffee" in m["content"]]
        self.assertTrue(len(coffee_mems) > 0, "Memory should be saved in DB")
        self.assertEqual(coffee_mems[0]["q_value"], 1.0)

    def test_02_memory_retrieval(self):
        """Test retrieving approved knowledge."""
        relevant = self.orchestrator.memory_store.get_relevant_memories("coffee")
        self.assertTrue(len(relevant) > 0)
        self.assertIn("Coffee", relevant[0]["content"])

    def test_03_rejection_flow(self):
        """Test rejecting a proposed memory."""
        res1 = self.orchestrator.process_input("Main London me kaam karta hu")
        self.assertTrue(res1["pending_approval"])

        # User rejects: "Nahi rehne do"
        res2 = self.orchestrator.process_input("Nahi rehne do")
        self.assertFalse(res2["pending_approval"])
        self.assertIn("discard", res2["reply"].lower())
        self.assertEqual(res2["reward"], config.REWARD_REJECTION)

    def test_04_reflexion_correction(self):
        """Test error feedback and constraint recording."""
        res = self.orchestrator.process_input("Galat bol rahe ho, aisa bilkul nahi hai")
        self.assertEqual(res["reward"], config.REWARD_CORRECTION)
        self.assertIn("galti", res["reply"].lower())

    def test_05_web_search(self):
        """Test internet search fallback."""
        ws = WebSearcher()
        results = ws.search("Python", max_results=2)
        self.assertTrue(len(results) > 0, "Should return at least 1 search result")
        self.assertTrue(len(results[0]["snippet"]) > 10)

    def test_06_contextual_bandit(self):
        """Test bandit policy selection and Q update."""
        bandit = ContextualBandit(policy_file=config.RL_POLICY_PATH)
        tone = bandit.select_tone()
        self.assertIn(tone, ["chill_hinglish", "crisp_concise", "detailed_guide"])
        
        bandit.update_policy("tone", "chill_hinglish", 1.0)
        status = bandit.get_status()
        self.assertIn("chill_hinglish", status["tone_q_values"])

    def test_07_multi_turn_context(self):
        """Test conversation context retention across multiple turns."""
        self.orchestrator.clear_context()
        self.assertEqual(len(self.orchestrator.conversation_history), 0)

        # Turn 1: Introduce a detail
        res1 = self.orchestrator.process_input("I am working on an AI project called Vega.")
        self.assertGreater(len(self.orchestrator.conversation_history), 0)

        # Turn 2: Refer back using pronoun/context without repeating the name
        res2 = self.orchestrator.process_input("What is the name of the project I just mentioned?")
        # The reply or context must contain Vega
        history_text = " ".join([m["content"] for m in self.orchestrator.conversation_history])
        self.assertIn("Vega", history_text, "Context history must preserve project name Vega")

if __name__ == "__main__":
    unittest.main()
