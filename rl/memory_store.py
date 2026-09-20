import sqlite3
import time
from typing import List, Dict, Any, Optional
import config

class MemoryStore:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or config.RL_DB_PATH)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Primary Knowledge & Memory table with RL Q-values
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,         -- 'user_fact', 'preference', 'rule', 'correction'
                    key TEXT NOT NULL,              -- Short descriptor or normalized key
                    content TEXT NOT NULL,          -- Full knowledge text
                    q_value REAL DEFAULT 1.0,       -- Reinforcement learning value score (-1.0 to 1.0)
                    access_count INTEGER DEFAULT 0, -- How many times recalled
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_reward REAL DEFAULT 1.0,
                    status TEXT DEFAULT 'approved'  -- 'approved', 'deprecated', 'pending'
                )
            """)

            # Feedback and reward history log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,       -- 'approval', 'rejection', 'correction', 'response_rating'
                    target_id INTEGER,
                    detail TEXT,
                    reward REAL NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.commit()

    def save_memory(self, category: str, key: str, content: str, initial_q: float = 1.0, status: str = 'approved') -> int:
        now = time.time()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Check if key or similar content already exists
            cursor.execute("SELECT id, q_value FROM memories WHERE key = ? AND status != 'deprecated'", (key,))
            existing = cursor.fetchone()
            if existing:
                mem_id = existing["id"]
                # Update content and reinforce Q-value
                new_q = min(1.0, existing["q_value"] + (config.RL_ALPHA * (initial_q - existing["q_value"])))
                cursor.execute("""
                    UPDATE memories 
                    SET content = ?, q_value = ?, updated_at = ?, status = ?
                    WHERE id = ?
                """, (content, new_q, now, status, mem_id))
                conn.commit()
                return mem_id
            else:
                cursor.execute("""
                    INSERT INTO memories (category, key, content, q_value, access_count, created_at, updated_at, last_reward, status)
                    VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
                """, (category, key, content, initial_q, now, now, initial_q, status))
                conn.commit()
                return cursor.lastrowid

    def update_q_value(self, memory_id: int, reward: float) -> float:
        """Applies Bellman/Q-learning update: Q = Q + alpha * (R - Q)"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT q_value FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return 0.0
            current_q = row["q_value"]
            new_q = current_q + config.RL_ALPHA * (reward - current_q)
            # Bound Q value between -1.0 and 1.0
            new_q = max(-1.0, min(1.0, new_q))
            
            # If Q-value drops too low, automatically mark as deprecated
            new_status = 'deprecated' if new_q < -0.3 else 'approved'

            cursor.execute("""
                UPDATE memories 
                SET q_value = ?, last_reward = ?, updated_at = ?, status = ?
                WHERE id = ?
            """, (new_q, reward, time.time(), new_status, memory_id))

            cursor.execute("""
                INSERT INTO feedback_logs (event_type, target_id, detail, reward, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, ('q_update', memory_id, f"Q updated from {current_q:.2f} to {new_q:.2f}", reward, time.time()))

            conn.commit()
            return new_q

    def get_relevant_memories(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves memories matching query keywords, ranked by:
        Score = (Keyword Match Count) * (1.0 + Q_value)
        Ensures high-Q (heavily approved) memories are prioritized.
        """
        query_words = set([w.lower().strip(",.?!:;'\"") for w in query.split() if len(w) > 2])
        if not query_words:
            return []

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, category, key, content, q_value, access_count 
                FROM memories 
                WHERE status = 'approved' AND q_value > -0.2
            """)
            all_memories = cursor.fetchall()

        scored = []
        for row in all_memories:
            content_lower = (row["key"] + " " + row["content"]).lower()
            match_count = sum(1 for word in query_words if word in content_lower)
            if match_count > 0:
                # Combined score using match strength and RL Q-value
                score = match_count * (1.0 + row["q_value"])
                scored.append((score, dict(row)))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]

        # Increment access count
        if results:
            ids = [r["id"] for r in results]
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE memories SET access_count = access_count + 1 WHERE id IN ({','.join(['?']*len(ids))})", ids)
                conn.commit()

        return results

    def list_all_active(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, key, content, q_value, access_count, updated_at FROM memories WHERE status = 'approved' ORDER BY q_value DESC")
            return [dict(r) for r in cursor.fetchall()]

    def log_feedback(self, event_type: str, detail: str, reward: float, target_id: Optional[int] = None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback_logs (event_type, target_id, detail, reward, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, target_id, detail, reward, time.time()))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total, AVG(q_value) as avg_q FROM memories WHERE status = 'approved'")
            mem_stats = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) as total_feedback, AVG(reward) as avg_reward FROM feedback_logs")
            fb_stats = cursor.fetchone()
            return {
                "active_memories": mem_stats["total"] or 0,
                "average_q_value": round(mem_stats["avg_q"] or 0.0, 2),
                "total_feedbacks": fb_stats["total_feedback"] or 0,
                "average_reward": round(fb_stats["avg_reward"] or 0.0, 2)
            }
