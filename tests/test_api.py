import sys
import time
import json
import threading
import unittest
import requests
from pathlib import Path
from http.server import ThreadingHTTPServer

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from brain.orchestrator import InnvoOrchestrator
from api.server import InnvoAPIHandler

TEST_PORT = 8999

class TestAPIServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orchestrator = InnvoOrchestrator(voice_enabled=False)
        InnvoAPIHandler.orchestrator = cls.orchestrator
        cls.server = ThreadingHTTPServer(("127.0.0.1", TEST_PORT), InnvoAPIHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_01_health_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/health"
        res = requests.get(url, timeout=3)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["name"], "Innvo")

    def test_02_rules_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/rules"
        res = requests.get(url, timeout=3)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("laws", data)
        self.assertGreaterEqual(len(data["laws"]), 4)

    def test_03_tools_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/tools"
        res = requests.get(url, timeout=3)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tools", data)

    def test_04_memories_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/memories"
        res = requests.get(url, timeout=3)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("memories", data)

if __name__ == "__main__":
    unittest.main()
