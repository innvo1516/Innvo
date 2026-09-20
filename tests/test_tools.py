import sys
import shutil
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
TEST_DATA_DIR = config.BASE_DIR / "data_test_tools"
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_DYNAMIC_DIR = TEST_DATA_DIR / "dynamic"
TEST_DYNAMIC_DIR.mkdir(exist_ok=True)

from tools.executor import ToolExecutor
from tools.skill_registry import SkillRegistry
from tools.tool_creator import ToolCreator

class TestToolSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.executor = ToolExecutor()
        cls.registry = SkillRegistry(
            registry_file=TEST_DATA_DIR / "test_skills.json",
            dynamic_dir=TEST_DYNAMIC_DIR
        )
        cls.creator = ToolCreator(cls.registry)

    @classmethod
    def tearDownClass(cls):
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_01_executor_python(self):
        """Test Python sandbox execution."""
        code = "print(15 + 27)"
        res = self.executor.execute_python(code)
        self.assertTrue(res["success"])
        self.assertEqual(res["stdout"], "42")

    def test_02_executor_shell(self):
        """Test shell execution."""
        cmd = "echo INNVO_ONLINE"
        res = self.executor.execute_shell(cmd)
        self.assertTrue(res["success"])
        self.assertIn("INNVO_ONLINE", res["stdout"])

    def test_03_system_metrics(self):
        """Test cross-platform system metrics."""
        m = self.executor.get_system_metrics()
        self.assertIn("platform", m)
        self.assertIn("disk_free_gb", m)
        self.assertGreater(m["disk_free_gb"], 0)

    def test_04_dynamic_tool_registration_and_run(self):
        """Test creating and running a dynamic Python tool."""
        tool_code = """
def run(**kwargs):
    target = kwargs.get('name', 'World')
    return f'Hello {target} from dynamic tool!'
"""
        registered = self.registry.register_tool(
            name="greeter_tool",
            description="Greets a person by name",
            code=tool_code,
            initial_q=1.0
        )
        self.assertTrue(registered)

        # Execute dynamic tool
        res = self.registry.execute("greeter_tool", name="Rishu")
        self.assertTrue(res["success"])
        self.assertEqual(res["output"], "Hello Rishu from dynamic tool!")

    def test_05_tool_creator_approval_loop(self):
        """Test ToolCreator proposal and user approval."""
        tool_info = {
            "name": "sample_calculator",
            "description": "Calculates power of two",
            "code": "def run(**kwargs):\n    return 2 ** 8\n",
            "test_output": "256"
        }
        self.creator.stage_proposal(tool_info)
        self.assertTrue(self.creator.has_pending_proposal())

        # User approves
        handled, msg, reward = self.creator.process_approval_response("Haan save kar lo")
        self.assertTrue(handled)
        self.assertEqual(reward, config.REWARD_APPROVAL)
        self.assertIn("sample_calculator", self.registry.skills)

    def test_06_tool_creator_rejection(self):
        """Test ToolCreator rejection."""
        tool_info = {
            "name": "unwanted_tool",
            "description": "Unwanted",
            "code": "def run(): return 0",
            "test_output": "0"
        }
        self.creator.stage_proposal(tool_info)
        handled, msg, reward = self.creator.process_approval_response("Nahi mat karo")
        self.assertTrue(handled)
        self.assertEqual(reward, config.REWARD_REJECTION)
        self.assertNotIn("unwanted_tool", self.registry.skills)

if __name__ == "__main__":
    unittest.main()
