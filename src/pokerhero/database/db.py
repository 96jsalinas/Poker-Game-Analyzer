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
    assert cur.lastrowid is not None
    return cur.lastrowid


def insert_hand(conn: sqlite3.Connection, hand: HandData, session_id: int) -> int:
    """Insert a hand row. Returns the autoincrement integer id."""
    cur = conn.execute(
        """INSERT INTO hands (source_hand_id, session_id, board_flop, board_turn, board_river,
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
