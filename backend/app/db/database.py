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
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan_type TEXT DEFAULT 'starter',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN tenant_id TEXT DEFAULT 'default'")
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN risk_score REAL DEFAULT 0")
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE assets ADD COLUMN risk_level TEXT DEFAULT 'LOW'")
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

        try:
            cursor.execute("ALTER TABLE scan_history ADD COLUMN tenant_id TEXT DEFAULT 'default'")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT DEFAULT 'default',
                hostname TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'INFO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'viewer',
                tenant_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        default_key = "default-tenant-key"
        cursor.execute("""
            INSERT OR IGNORE INTO tenants (name, api_key, plan_type)
            VALUES ('default', ?, 'starter')
        """, (default_key,))

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
