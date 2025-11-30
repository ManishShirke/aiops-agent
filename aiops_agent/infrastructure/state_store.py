import sqlite3
from aiops_agent import config
from aiops_agent.observability.engine import TELEMETRY

class StateStore:
    def __init__(self, db_name=config.DB_NAME):
        self.db_name = db_name
        self._init_db()

    def _get_conn(self): return sqlite3.connect(self.db_name)
    
    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY, summary TEXT, resolution TEXT)")

    def save_fact(self, key, value):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO facts (key, value) VALUES (?, ?)", (key, str(value)))
        TELEMETRY.log("INFO", "STATE_STORE", f"Persisted Fact", {"key": key})
    
    def search_history(self, keyword):
        """RAG-Lite: Simple keyword search for context retrieval"""
        results = []
        with self._get_conn() as conn:
            rows = conn.execute("SELECT summary, resolution FROM incidents WHERE summary LIKE ?", (f'%{keyword}%',))
            for s, r in rows: results.append(f"Issue: {s} | Resolution: {r}")
        
        if results:
            TELEMETRY.log("INFO", "RAG_RECALL", f"Found {len(results)} historical matches")
        return "\n".join(results) if results else "No matches found."

    def archive_incident(self, summary, resolution):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO incidents (summary, resolution) VALUES (?, ?)", (summary, resolution))
        TELEMETRY.log("SUCCESS", "ARCHIVE", "Incident saved to history.")
        
        # Trigger compaction check
        self.compact_memory()

    def compact_memory(self):
        """Reduces token usage by summarizing old rows"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT count(*) FROM incidents")
            count = cursor.fetchone()[0]
            
            if count > config.MEMORY_LIMIT:
                TELEMETRY.log("WARN", "CONTEXT_ENG", f"Memory limit exceeded ({count}/{config.MEMORY_LIMIT}). Compacting...")
                
                # Fetch oldest 2 rows
                old_rows = conn.execute(f"SELECT id FROM incidents ORDER BY id ASC LIMIT 2").fetchall()
                old_ids = [row[0] for row in old_rows]
                
                # Delete oldest
                conn.execute(f"DELETE FROM incidents WHERE id IN ({','.join(map(str, old_ids))})")
                
                # Insert summary placeholder
                conn.execute("INSERT INTO incidents (summary, resolution) VALUES (?, ?)", 
                             ("Compacted Summary of older incidents", "See archived logs"))
                
                TELEMETRY.log("SUCCESS", "CONTEXT_ENG", "Compaction Complete.")

# Singleton
STATE = StateStore()
