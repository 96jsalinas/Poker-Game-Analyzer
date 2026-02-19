import sqlite3
from decimal import Decimal
from pathlib import Path

from pokerhero.parser.models import SessionData

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

def upsert_player(conn: sqlite3.Connection, username: str) -> int:
    """Insert player if not exists, return their id. preferred_name defaults to username."""
    conn.execute(
        "INSERT INTO players (username, preferred_name) VALUES (?, ?) ON CONFLICT(username) DO NOTHING",
        (username, username),
    )
    row = conn.execute("SELECT id FROM players WHERE username = ?", (username,)).fetchone()
    return row[0]

def insert_session(
    conn: sqlite3.Connection,
    session: SessionData,
    start_time: str | None = None,
    hero_buy_in: Decimal | None = None,
    hero_cash_out: Decimal | None = None,
) -> int:
    """Insert a session row and return its id."""
    cur = conn.execute(
        """INSERT INTO sessions
           (game_type, limit_type, max_seats, small_blind, big_blind, ante, start_time, hero_buy_in, hero_cash_out)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session.game_type,
            session.limit_type,
            session.max_seats,
            float(session.small_blind),
            float(session.big_blind),
            float(session.ante),
            start_time,
            float(hero_buy_in) if hero_buy_in is not None else None,
            float(hero_cash_out) if hero_cash_out is not None else None,
        ),
    )
    return cur.lastrowid
