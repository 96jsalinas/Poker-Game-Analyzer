"""Database query functions for the analysis layer.

Each function executes a SQL query against an open SQLite connection and
returns the result as a pandas DataFrame. These are the only functions
that touch the database; stat calculations live in stats.py and operate
purely on the returned DataFrames.
"""

import sqlite3

import pandas as pd


def get_sessions(conn: sqlite3.Connection, player_id: int) -> pd.DataFrame:
    """Return all sessions with aggregated hand count and hero net profit.

    Columns: id, start_time, game_type, limit_type, small_blind, big_blind,
             hands_played, net_profit.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per session, sorted by start_time ascending.
    """
    sql = """
        SELECT
            s.id,
            s.start_time,
            s.game_type,
            s.limit_type,
            s.small_blind,
            s.big_blind,
            COUNT(h.id)                     AS hands_played,
            COALESCE(SUM(hp.net_result), 0) AS net_profit
        FROM sessions s
        LEFT JOIN hands h  ON h.session_id = s.id
        LEFT JOIN hand_players hp ON hp.hand_id = h.id AND hp.player_id = ?
        GROUP BY s.id
        ORDER BY s.start_time ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(player_id),))


def get_hands(
    conn: sqlite3.Connection, session_id: int, player_id: int
) -> pd.DataFrame:
    """Return all hands for a session with hero net result and hole cards.

    Columns: id, source_hand_id, timestamp, board_flop, board_turn,
             board_river, total_pot, net_result, hole_cards.

    Args:
        conn: Open SQLite connection.
        session_id: Primary key of the session row.
        player_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per hand, sorted by timestamp ascending.
    """
    sql = """
        SELECT
            h.id,
            h.source_hand_id,
            h.timestamp,
            h.board_flop,
            h.board_turn,
            h.board_river,
            h.total_pot,
            hp.net_result,
            hp.hole_cards
        FROM hands h
        LEFT JOIN hand_players hp ON hp.hand_id = h.id AND hp.player_id = ?
        WHERE h.session_id = ?
        ORDER BY h.timestamp ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(player_id), int(session_id)))


def get_actions(conn: sqlite3.Connection, hand_id: int) -> pd.DataFrame:
    """Return all actions for a hand ordered by sequence.

    Columns: sequence, player_id, is_hero, street, action_type, amount,
             amount_to_call, pot_before, is_all_in, spr, mdf.

    Args:
        conn: Open SQLite connection.
        hand_id: Primary key of the hand row (internal integer id).

    Returns:
        DataFrame with one row per action, sorted by sequence ascending.
    """
    sql = """
        SELECT
            sequence,
            player_id,
            is_hero,
            street,
            action_type,
            amount,
            amount_to_call,
            pot_before,
            is_all_in,
            spr,
            mdf
        FROM actions
        WHERE hand_id = ?
        ORDER BY sequence ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(hand_id),))


def get_hero_hand_players(conn: sqlite3.Connection, player_id: int) -> pd.DataFrame:
    """Return all hand_player rows for hero with session context and saw_flop flag.

    Columns: hand_id, vpip, pfr, went_to_showdown, net_result, position,
             hole_cards, big_blind, saw_flop.

    `saw_flop` is 1 if hero had at least one action on the FLOP street,
    0 otherwise (i.e. folded or sat out preflop).

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per hand hero participated in.
    """
    sql = """
        SELECT
            hp.hand_id,
            hp.vpip,
            hp.pfr,
            hp.went_to_showdown,
            hp.net_result,
            hp.position,
            hp.hole_cards,
            s.big_blind,
            CASE WHEN EXISTS (
                SELECT 1 FROM actions a
                WHERE a.hand_id = hp.hand_id
                  AND a.player_id = hp.player_id
                  AND a.street = 'FLOP'
            ) THEN 1 ELSE 0 END AS saw_flop
        FROM hand_players hp
        JOIN hands h ON h.id = hp.hand_id
        JOIN sessions s ON s.id = h.session_id
        WHERE hp.player_id = ?
        ORDER BY h.timestamp ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(player_id),))
