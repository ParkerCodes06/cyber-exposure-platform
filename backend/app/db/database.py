import os
import sqlite3
from backend.app.utils.logger import get_logger

logger = get_logger("database")

DB_PATH = os.getenv("DB_PATH", "assets.db")


def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                os TEXT NOT NULL,
                ip_address TEXT,
                open_ports TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN agent_id TEXT")
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                agent_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                risk_score REAL DEFAULT 0,
                vulnerability_count INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'LOW'
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
