"""Database query functions for the analysis layer.

Each function executes a SQL query against an open SQLite connection and
returns the result as a pandas DataFrame. These are the only functions
that touch the database; stat calculations live in stats.py and operate
purely on the returned DataFrames.
"""

import sqlite3

import pandas as pd


def get_sessions(
    conn: sqlite3.Connection, player_id: int, since_date: str | None = None
) -> pd.DataFrame:
    """Return all sessions with aggregated hand count and hero net profit.

    Columns: id, start_time, game_type, limit_type, small_blind, big_blind,
             hands_played, net_profit.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string (e.g. '2026-01-01').
            When provided, only sessions whose start_time >= since_date
            are returned.

    Returns:
        DataFrame with one row per session, sorted by start_time ascending.
    """
    date_clause = "AND s.start_time >= :since" if since_date else ""
    sql = f"""
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
        LEFT JOIN hand_players hp ON hp.hand_id = h.id AND hp.player_id = :pid
        WHERE 1=1 {date_clause}
        GROUP BY s.id
        ORDER BY s.start_time ASC
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


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

    Includes player username and position via JOIN with players and hand_players.

    Columns: sequence, player_id, is_hero, street, action_type, amount,
             amount_to_call, pot_before, is_all_in, spr, mdf, username, position.

    Args:
        conn: Open SQLite connection.
        hand_id: Primary key of the hand row (internal integer id).

    Returns:
        DataFrame with one row per action, sorted by sequence ascending.
    """
    sql = """
        SELECT
            a.sequence,
            a.player_id,
            a.is_hero,
            a.street,
            a.action_type,
            a.amount,
            a.amount_to_call,
            a.pot_before,
            a.is_all_in,
            a.spr,
            a.mdf,
            p.username,
            hp.position
        FROM actions a
        JOIN players p ON p.id = a.player_id
        LEFT JOIN hand_players hp
            ON hp.hand_id = a.hand_id AND hp.player_id = a.player_id
        WHERE a.hand_id = ?
        ORDER BY a.sequence ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(hand_id),))


def get_hero_timeline(
    conn: sqlite3.Connection, player_id: int, since_date: str | None = None
) -> pd.DataFrame:
    """Return one row per hand with timestamp and net_result for the bankroll graph.

    Columns: timestamp, net_result.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).

    Returns:
        DataFrame ordered by timestamp ascending, one row per hand.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    sql = f"""
        SELECT
            h.timestamp,
            hp.net_result
        FROM hand_players hp
        JOIN hands h ON h.id = hp.hand_id
        WHERE hp.player_id = :pid {date_clause}
        ORDER BY h.timestamp ASC
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_actions(
    conn: sqlite3.Connection, player_id: int, since_date: str | None = None
) -> pd.DataFrame:
    """Return all post-flop actions by hero with position context.

    Used to compute per-position Aggression Factor (AF).
    Only FLOP, TURN, and RIVER streets are returned.

    Columns: hand_id, street, action_type, position.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).

    Returns:
        DataFrame of hero's post-flop actions across all hands.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    sql = f"""
        SELECT
            a.hand_id,
            a.street,
            a.action_type,
            hp.position
        FROM actions a
        JOIN hand_players hp
            ON hp.hand_id = a.hand_id AND hp.player_id = a.player_id
        JOIN hands h ON h.id = a.hand_id
        WHERE a.player_id = :pid
          AND a.street IN ('FLOP', 'TURN', 'RIVER')
          {date_clause}
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_hand_players(
    conn: sqlite3.Connection, player_id: int, since_date: str | None = None
) -> pd.DataFrame:
    """Return all hand_player rows for hero with session context and saw_flop flag.

    Columns: hand_id, vpip, pfr, went_to_showdown, net_result, position,
             hole_cards, big_blind, saw_flop.

    `saw_flop` is 1 if hero had at least one action on the FLOP street,
    0 otherwise (i.e. folded or sat out preflop).

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).

    Returns:
        DataFrame with one row per hand hero participated in.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    sql = f"""
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
        WHERE hp.player_id = :pid {date_clause}
        ORDER BY h.timestamp ASC
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_opportunity_actions(
    conn: sqlite3.Connection, player_id: int, since_date: str | None = None
) -> pd.DataFrame:
    """Return PREFLOP and FLOP actions for all hands hero played.

    Used to compute 3-Bet% and C-Bet%. Returns ALL players' actions (not
    just hero's) so that sequence analysis can detect raises before hero acts.

    Columns: hand_id, saw_flop, sequence, is_hero, street, action_type.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).

    Returns:
        DataFrame ordered by hand_id then sequence ascending.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    sql = f"""
        SELECT
            h.id AS hand_id,
            CASE WHEN h.board_flop IS NOT NULL THEN 1 ELSE 0 END AS saw_flop,
            a.sequence,
            a.is_hero,
            a.street,
            a.action_type
        FROM actions a
        JOIN hands h ON h.id = a.hand_id
        WHERE h.id IN (
            SELECT DISTINCT hand_id FROM hand_players WHERE player_id = :pid
        )
          AND a.street IN ('PREFLOP', 'FLOP')
          {date_clause}
        ORDER BY a.hand_id, a.sequence
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_export_data(conn: sqlite3.Connection, player_id: int) -> pd.DataFrame:
    """Return sessions and per-hand results joined for CSV export.

    Columns: session_id, date, stakes, hand_id, position, hole_cards,
             net_result.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per hand, ordered by timestamp ascending.
    """
    sql = """
        SELECT
            s.id            AS session_id,
            s.start_time    AS date,
            s.small_blind || '/' || s.big_blind AS stakes,
            h.id            AS hand_id,
            hp.position,
            hp.hole_cards,
            hp.net_result
        FROM hand_players hp
        JOIN hands h    ON h.id = hp.hand_id
        JOIN sessions s ON s.id = h.session_id
        WHERE hp.player_id = ?
        ORDER BY h.timestamp ASC
    """
    return pd.read_sql_query(sql, conn, params=(int(player_id),))
