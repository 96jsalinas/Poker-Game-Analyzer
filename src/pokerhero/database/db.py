import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return a sqlite3 connection with foreign keys enabled and row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create the database schema if it doesn't exist. Returns an open connection."""
    conn = get_connection(db_path)
    conn.executescript(_SCHEMA_PATH.read_text())
    conn.commit()
    return conn
