import sys
import shutil
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
TEST_DIR = config.BASE_DIR / "data_test_kg_sync"
TEST_DIR.mkdir(exist_ok=True)

from brain.knowledge_graph import KnowledgeGraph
from brain.truth_filter import TruthFilter
from learning.idle_daemon import IdleCuriosityDaemon
from sync.sync_broker import SyncBroker
from sync.delta_protocol import DeltaProtocol

class TestKnowledgeAndSync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kg = KnowledgeGraph(db_path=TEST_DIR / "test_kg.db")
        cls.truth_filter = TruthFilter()
        cls.idle_daemon = IdleCuriosityDaemon()

    @classmethod
    def tearDownClass(cls):
        if TEST_DIR.exists():
            shutil.rmtree(TEST_DIR, ignore_errors=True)

    def test_01_knowledge_graph_triples(self):
        """Test adding and querying semantic triples in SQLite."""
        ok = self.kg.add_triple("Rishu", "likes", "Dark Chocolate", confidence=0.95)
        self.assertTrue(ok)

        # Query relation
        res = self.kg.query_relation("Rishu", "likes")
        self.assertEqual(res, "Dark Chocolate")

        # Query entity
        ent_rows = self.kg.query_entity("Rishu")
        self.assertGreaterEqual(len(ent_rows), 1)

        # Context summary
        summary = self.kg.get_summary_for_context("Does Rishu like Chocolate?")
        self.assertIn("Dark Chocolate", summary)

    def test_02_truth_filter_verification(self):
        """Test fact verification mechanism."""
        claim = "Python is a high-level general-purpose programming language"
        res = self.truth_filter.verify_fact(claim)
        self.assertIn("verified", res)
        self.assertIn("confidence", res)
        self.assertGreater(res["confidence"], 0.0)

    def test_03_idle_curiosity_switch_isolation(self):
        """Test that idle curiosity switch can be toggled without side-effects."""
        self.idle_daemon.disable()
        self.assertFalse(self.idle_daemon.is_enabled())
        # Cycle should return None when disabled
        res_off = self.idle_daemon.run_single_curiosity_cycle()
        self.assertIsNone(res_off)

        # Turn ON
        self.idle_daemon.enable()
        self.assertTrue(self.idle_daemon.is_enabled())

        # Turn OFF again to restore default
        self.idle_daemon.disable()
        self.assertFalse(self.idle_daemon.is_enabled())

    def test_04_hive_mind_delta_sync(self):
        """Test creating, exporting, and importing micro-delta packets."""
        broker = SyncBroker(knowledge_graph=self.kg)
        packet = broker.export_delta()
        self.assertTrue(DeltaProtocol.validate_packet(packet))
        self.assertIn("payload", packet)
        self.assertIn("device_id", packet)

        # Verify export to file
        export_file = broker.export_to_file()
        self.assertTrue(export_file.exists())
        self.assertGreater(export_file.stat().st_size, 0)

        # Test importing delta packet
        incoming_packet = {
            "protocol_version": "1.0",
            "device_id": "phone_satellite_termux",
            "timestamp": 123456789.0,
            "payload": {
                "memories": [{"content": "User prefers concise summaries", "category": "preference", "q_value": 0.8}],
                "skills": [],
                "triples": [{"subject": "Phone", "predicate": "connected_to", "object_val": "Innvo Brain", "confidence": 1.0}],
                "policy": {}
            }
        }
        imported = broker.import_delta(incoming_packet)
        self.assertGreaterEqual(imported["memories"], 1)
        self.assertGreaterEqual(imported["triples"], 1)

if __name__ == "__main__":
    unittest.main()
