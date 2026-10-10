import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import config
from .delta_protocol import DeltaProtocol
from rl.memory_store import MemoryStore
from tools.skill_registry import SkillRegistry
from brain.knowledge_graph import KnowledgeGraph
from rl.contextual_bandit import ContextualBandit

logger = logging.getLogger("InnvoSyncBroker")

class SyncBroker:
    """
    Broker for local and P2P synchronization between Innvo devices
    (Laptop Central Brain <-> Phone/Termux Satellite <-> Embedded devices).
    """

    def __init__(self, 
                 memory_store: Optional[MemoryStore] = None,
                 skill_registry: Optional[SkillRegistry] = None,
                 knowledge_graph: Optional[KnowledgeGraph] = None,
                 bandit: Optional[ContextualBandit] = None):
        self.memory_store = memory_store or MemoryStore()
        self.skill_registry = skill_registry or SkillRegistry()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.bandit = bandit or ContextualBandit()
        self.sync_dir = config.SYNC_DIR

    def export_delta(self) -> Dict[str, Any]:
        """Gathers local state changes and returns a Delta packet."""
        memories = self.memory_store.list_all_active()
        skills = self.skill_registry.list_tools()
        triples = self.knowledge_graph.list_all(limit=100)
        policy = self.bandit.get_status()

        return DeltaProtocol.create_delta_packet(
            memories=memories,
            skills=skills,
            triples=triples,
            policy=policy
        )

    def export_to_file(self, filename: Optional[str] = None) -> Path:
        """Saves current delta packet to a sync file."""
        packet = self.export_delta()
        fname = filename or f"sync_delta_{int(time.time())}.json"
        target = self.sync_dir / fname
        target.write_text(json.dumps(packet, indent=2), encoding="utf-8")
        logger.info(f"Exported delta sync packet to {target}")
        return target

    def import_delta(self, packet: Dict[str, Any]) -> Dict[str, int]:
        """
        Applies an incoming delta packet into the local brain state.
        Returns counts of merged items.
        """
        if not DeltaProtocol.validate_packet(packet):
            raise ValueError("Invalid delta sync packet format")

        payload = packet.get("payload", {})
        merged = {"memories": 0, "skills": 0, "triples": 0}

        # 1. Merge Memories
        for m in payload.get("memories", []):
            content = m.get("content")
            cat = m.get("category", "general")
            if content:
                # Add or reinforce memory
                mem_id = self.memory_store.add_memory(content, category=cat, initial_q=m.get("q_value", 0.5))
                if mem_id:
                    merged["memories"] += 1

        # 2. Merge Knowledge Graph Triples
        for t in payload.get("triples", []):
            subj = t.get("subject")
            pred = t.get("predicate")
            obj = t.get("object_val")
            conf = t.get("confidence", 1.0)
            if subj and pred and obj:
                if self.knowledge_graph.add_triple(subj, pred, obj, confidence=conf, source="sync"):
                    merged["triples"] += 1

        # 3. Merge Skills
        for sk in payload.get("skills", []):
            s_name = sk.get("name")
            s_desc = sk.get("description", "")
            s_code = sk.get("code")
            if s_name and s_code and s_name not in self.skill_registry.tools:
                self.skill_registry.register_tool(s_name, s_desc, s_code, initial_q=sk.get("q_score", 0.5))
                merged["skills"] += 1

        logger.info(f"Imported delta: {merged}")
        return merged

    def import_from_file(self, file_path: Path) -> Dict[str, int]:
        """Reads a sync JSON file and imports into local brain."""
        if not file_path.exists():
            raise FileNotFoundError(f"Sync file {file_path} does not exist.")
        packet = json.loads(file_path.read_text(encoding="utf-8"))
        return self.import_delta(packet)
