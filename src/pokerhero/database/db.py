import logging
import sqlite3
from decimal import Decimal
from pathlib import Path

from pokerhero.parser.models import (
    ActionData,
    HandData,
    HandPlayerData,
    ParsedHand,
    SessionData,
)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
logger = logging.getLogger(__name__)


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return a sqlite3 connection with foreign keys enabled
    and row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create the database schema if it doesn't exist. Returns an open connection."""
    conn = get_connection(db_path)
    conn.executescript(_SCHEMA_PATH.read_text())
    # Migrate existing databases: add is_favorite if not present
    for table in ("sessions", "hands"):
        try:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass  # column already exists
    # Migrate existing databases: add currency if not present
    try:
        conn.execute(
            "ALTER TABLE sessions ADD COLUMN currency TEXT NOT NULL DEFAULT 'PLAY'"
        )
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    return conn


def upsert_player(conn: sqlite3.Connection, username: str) -> int:
    """Insert player if not exists, return their id.
    preferred_name defaults to username."""
    conn.execute(
        "INSERT INTO players (username, preferred_name) VALUES (?, ?)"
        " ON CONFLICT(username) DO NOTHING",
        (username, username),
    )
    row = conn.execute(
        "SELECT id FROM players WHERE username = ?", (username,)
    ).fetchone()
    assert row is not None  # guaranteed: INSERT above ensures the row exists
    return int(row[0])


def insert_session(
    conn: sqlite3.Connection,
    session: SessionData,
    start_time: str | None = None,
    hero_buy_in: Decimal | None = None,
    hero_cash_out: Decimal | None = None,
) -> int:
    """Insert a session row and return its id."""
    logger.debug(
        "Inserting session: hero_buy_in=%s, hero_cash_out=%s",
        hero_buy_in,
        hero_cash_out,
    )
    cur = conn.execute(
        """INSERT INTO sessions
           (game_type, limit_type, max_seats, small_blind, big_blind,
            ante, start_time, hero_buy_in, hero_cash_out, currency)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
            session.currency,
        ),
    )
    assert cur.lastrowid is not None
    return cur.lastrowid


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    """Return the value for a settings key, or default if not set.

    Args:
        conn: An open SQLite connection.
        key: The settings key to look up.
        default: Value to return if the key does not exist.

    Returns:
        Stored value as a string, or default.
    """
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row is not None else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Persist a key/value pair in the settings table (upsert).

    Args:
        conn: An open SQLite connection.
        key: The settings key.
        value: The value to store.
    """
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def update_session_financials(
    conn: sqlite3.Connection,
    session_id: int,
    hero_buy_in: Decimal,
    hero_cash_out: Decimal,
) -> None:
    """Update hero_buy_in and hero_cash_out on an existing session row.

    Args:
        conn: An open SQLite connection.
        session_id: The session to update.
        hero_buy_in: Hero's starting stack at the beginning of the session.
        hero_cash_out: Hero's final stack at the end of the session.
    """
    conn.execute(
        "UPDATE sessions SET hero_buy_in = ?, hero_cash_out = ? WHERE id = ?",
        (float(hero_buy_in), float(hero_cash_out), session_id),
    )


def insert_hand(conn: sqlite3.Connection, hand: HandData, session_id: int) -> int:
    """Insert a hand row. Returns the autoincrement integer id."""
    cur = conn.execute(
        """INSERT INTO hands
           (source_hand_id, session_id, board_flop, board_turn, board_river,
            total_pot, uncalled_bet_returned, rake, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            hand.hand_id,
            session_id,
            hand.board_flop,
            hand.board_turn,
            hand.board_river,
            float(hand.total_pot),
            float(hand.uncalled_bet_returned),
            float(hand.rake),
            hand.timestamp.isoformat(),
        ),
    )
    assert cur.lastrowid is not None
    return cur.lastrowid


def insert_hand_players(
    conn: sqlite3.Connection,
    hand_id: int,
    players: list[HandPlayerData],
    player_id_map: dict[str, int],
) -> None:
    """Insert rows into hand_players for all players in the hand."""
    conn.executemany(
        """INSERT INTO hand_players
           (hand_id, player_id, position, starting_stack, hole_cards,
            vpip, pfr, went_to_showdown, net_result)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                hand_id,
                player_id_map[p.username],
                p.position,
                float(p.starting_stack),
                p.hole_cards,
                int(p.vpip),
                int(p.pfr),
                int(p.went_to_showdown),
                float(p.net_result),
            )
            for p in players
        ],
    )


def insert_actions(
    conn: sqlite3.Connection,
    hand_id: int,
    actions: list[ActionData],
    player_id_map: dict[str, int],
) -> None:
    """Insert all action rows for a hand."""
    conn.executemany(
        """INSERT INTO actions
           (hand_id, player_id, is_hero, street, action_type, amount,
            amount_to_call, pot_before, is_all_in, sequence, spr, mdf)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                hand_id,
                player_id_map[a.player],
                int(a.is_hero),
                a.street,
                a.action_type,
                float(a.amount),
                float(a.amount_to_call),
                float(a.pot_before),
                int(a.is_all_in),
                a.sequence,
                float(a.spr) if a.spr is not None else None,
                float(a.mdf) if a.mdf is not None else None,
            )
            for a in actions
        ],
    )


def clear_all_data(conn: sqlite3.Connection) -> None:
    """Delete all poker data while preserving the settings table.

    Removes all rows from actions, hand_players, hands, sessions, and players.
    The settings table (hero_username etc.) is left intact.

    Args:
        conn: An open SQLite connection.
    """
    conn.executescript(
        """
        DELETE FROM actions;
        DELETE FROM hand_players;
        DELETE FROM hands;
        DELETE FROM sessions;
        DELETE FROM players;
        """
    )
    conn.commit()


def toggle_session_favorite(conn: sqlite3.Connection, session_id: int) -> None:
    """Toggle the is_favorite flag on a session (0→1 or 1→0).

    Args:
        conn: An open SQLite connection.
        session_id: Primary key of the session to toggle.
    """
    conn.execute(
        "UPDATE sessions SET is_favorite = 1 - is_favorite WHERE id = ?",
        (session_id,),
    )


def toggle_hand_favorite(conn: sqlite3.Connection, hand_id: int) -> None:
    """Toggle the is_favorite flag on a hand (0→1 or 1→0).

    Args:
        conn: An open SQLite connection.
        hand_id: Primary key of the hand to toggle.
    """
    conn.execute(
        "UPDATE hands SET is_favorite = 1 - is_favorite WHERE id = ?",
        (hand_id,),
    )


def get_hand_equity(
    conn: sqlite3.Connection,
    hand_id: int,
    hero_id: int,
    sample_count: int,
) -> float | None:
    """Return cached equity for a hand if sample_count matches, else None.

    Args:
        conn: An open SQLite connection.
        hand_id: Internal hand id.
        hero_id: Internal player id for the hero.
        sample_count: Monte Carlo sample count the equity was computed with.

    Returns:
        Cached equity float (0.0–1.0), or None on miss or stale sample_count.
    """
    row = conn.execute(
        "SELECT equity FROM hand_equity"
        " WHERE hand_id = ? AND hero_id = ? AND sample_count = ?",
        (hand_id, hero_id, sample_count),
    ).fetchone()
    return float(row[0]) if row is not None else None


def set_hand_equity(
    conn: sqlite3.Connection,
    hand_id: int,
    hero_id: int,
    equity: float,
    sample_count: int,
) -> None:
    """Persist equity for a hand (upsert — replaces any existing row).

    Args:
        conn: An open SQLite connection.
        hand_id: Internal hand id.
        hero_id: Internal player id for the hero.
        equity: Computed equity value (0.0–1.0).
        sample_count: Monte Carlo sample count used for this computation.
    """
    conn.execute(
        "INSERT OR REPLACE INTO hand_equity (hand_id, hero_id, equity, sample_count)"
        " VALUES (?, ?, ?, ?)",
        (hand_id, hero_id, equity, sample_count),
    )


def save_parsed_hand(
    conn: sqlite3.Connection,
    parsed: ParsedHand,
    session_id: int,
) -> None:
    """Persist a fully parsed hand to the database within an existing session.

    All inserts are wrapped in a single transaction; caller is responsible
    for calling conn.commit() or using this inside a transaction block.
    """
    # Upsert all players and build the id map
    player_id_map = {
        p.username: upsert_player(conn, p.username) for p in parsed.players
    }

    # Insert hand and get its autoincrement id
    hand_id = insert_hand(conn, parsed.hand, session_id)

    # Insert hand_players
    insert_hand_players(conn, hand_id, parsed.players, player_id_map)

    # Insert actions
    insert_actions(conn, hand_id, parsed.actions, player_id_map)
