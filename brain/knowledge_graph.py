import sqlite3
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import config

logger = logging.getLogger("InnvoKnowledgeGraph")

class KnowledgeGraph:
    """
    SQLite-backed Semantic Triplet Store (Subject - Predicate - Object).
    Provides structured entity-relationship reasoning for Innvo.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.KNOWLEDGE_GRAPH_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object_val TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'conversation',
                    created_at REAL NOT NULL,
                    UNIQUE(subject, predicate, object_val)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_subj ON semantic_triples(subject)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_obj ON semantic_triples(object_val)")
            conn.commit()

    def add_triple(self, subject: str, predicate: str, object_val: str, 
                   confidence: float = 1.0, source: str = "conversation") -> bool:
        """
        Inserts or updates a semantic triple (e.g., 'Rishu', 'likes', 'Black Coffee').
        """
        subj = subject.strip().lower()
        pred = predicate.strip().lower()
        obj = object_val.strip()

        now = time.time()
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO semantic_triples (subject, predicate, object_val, confidence, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(subject, predicate, object_val) DO UPDATE SET
                        confidence = ?,
                        source = ?,
                        created_at = ?
                """, (subj, pred, obj, confidence, source, now, confidence, source, now))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add triple ({subject}, {predicate}, {object_val}): {e}")
            return False

    def query_entity(self, entity: str) -> List[Dict[str, Any]]:
        """Finds all relationships involving the given entity as subject or object."""
        ent = entity.strip().lower()
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT subject, predicate, object_val, confidence, source, created_at
                FROM semantic_triples
                WHERE subject = ? OR object_val LIKE ?
                ORDER BY confidence DESC
            """, (ent, f"%{ent}%")).fetchall()
            return [dict(r) for r in rows]

    def query_relation(self, subject: str, predicate: str) -> Optional[str]:
        """Finds object for a given (subject, predicate) pair."""
        subj = subject.strip().lower()
        pred = predicate.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT object_val FROM semantic_triples
                WHERE subject = ? AND predicate = ?
                ORDER BY confidence DESC LIMIT 1
            """, (subj, pred)).fetchone()
            if row:
                return row["object_val"]
        return None

    def get_summary_for_context(self, text: str) -> str:
        """Finds relevant triples matching words in text to inject into SLM context."""
        words = [w.lower() for w in text.split() if len(w) > 3]
        if not words:
            return ""

        matched = []
        with self._get_connection() as conn:
            for word in words[:5]:
                rows = conn.execute("""
                    SELECT subject, predicate, object_val FROM semantic_triples
                    WHERE subject LIKE ? OR object_val LIKE ?
                    LIMIT 2
                """, (f"%{word}%", f"%{word}%")).fetchall()
                for r in rows:
                    trip = f"({r['subject']} -> {r['predicate']} -> {r['object_val']})"
                    if trip not in matched:
                        matched.append(trip)

        if matched:
            return "[Knowledge Graph Triples: " + "; ".join(matched) + "]"
        return ""

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, subject, predicate, object_val, confidence, source, created_at
                FROM semantic_triples ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]
