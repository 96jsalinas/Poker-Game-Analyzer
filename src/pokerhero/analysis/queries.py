"""Database query functions for the analysis layer.

Each function executes a SQL query against an open SQLite connection and
returns the result as a pandas DataFrame. These are the only functions
that touch the database; stat calculations live in stats.py and operate
purely on the returned DataFrames.
"""

import sqlite3

import pandas as pd


def get_sessions(
    conn: sqlite3.Connection,
    player_id: int,
    since_date: str | None = None,
    currency_type: str | None = None,
) -> pd.DataFrame:
    """Return all sessions with aggregated hand count and hero net profit.

    Columns: id, start_time, game_type, limit_type, small_blind, big_blind,
             currency, hands_played, net_profit.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string (e.g. '2026-01-01').
            When provided, only sessions whose start_time >= since_date
            are returned.
        currency_type: Optional filter — 'real' returns only USD/EUR sessions,
            'play' returns only PLAY sessions. None returns all.

    Returns:
        DataFrame with one row per session, sorted by start_time ascending.
    """
    date_clause = "AND s.start_time >= :since" if since_date else ""
    if currency_type == "real":
        currency_clause = "AND s.currency IN ('USD', 'EUR')"
    elif currency_type == "play":
        currency_clause = "AND s.currency = 'PLAY'"
    else:
        currency_clause = ""
    sql = f"""
        SELECT
            s.id,
            s.start_time,
            s.game_type,
            s.limit_type,
            s.small_blind,
            s.big_blind,
            s.currency,
            s.is_favorite,
            COUNT(h.id)                     AS hands_played,
            COALESCE(SUM(hp.net_result), 0) AS net_profit
        FROM sessions s
        LEFT JOIN hands h  ON h.session_id = s.id
        LEFT JOIN hand_players hp ON hp.hand_id = h.id AND hp.player_id = :pid
        WHERE 1=1 {date_clause} {currency_clause}
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
             board_river, total_pot, net_result, hole_cards, position,
             went_to_showdown, saw_flop.

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
            h.is_favorite,
            hp.net_result,
            hp.hole_cards,
            hp.position,
            hp.went_to_showdown,
            CASE WHEN EXISTS (
                SELECT 1 FROM actions a
                WHERE a.hand_id = h.id
                  AND a.player_id = hp.player_id
                  AND a.street = 'FLOP'
            ) THEN 1 ELSE 0 END AS saw_flop
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
    conn: sqlite3.Connection,
    player_id: int,
    since_date: str | None = None,
    currency_type: str | None = None,
) -> pd.DataFrame:
    """Return one row per hand with timestamp and net_result for the bankroll graph.

    Columns: timestamp, net_result.

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).
        currency_type: Optional filter — 'real' for USD/EUR, 'play' for PLAY,
            None for all.

    Returns:
        DataFrame ordered by timestamp ascending, one row per hand.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    if currency_type == "real":
        currency_clause = "AND s.currency IN ('USD', 'EUR')"
    elif currency_type == "play":
        currency_clause = "AND s.currency = 'PLAY'"
    else:
        currency_clause = ""
    sql = f"""
        SELECT
            h.timestamp,
            hp.net_result
        FROM hand_players hp
        JOIN hands h ON h.id = hp.hand_id
        JOIN sessions s ON s.id = h.session_id
        WHERE hp.player_id = :pid {date_clause} {currency_clause}
        ORDER BY h.timestamp ASC
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_actions(
    conn: sqlite3.Connection,
    player_id: int,
    since_date: str | None = None,
    currency_type: str | None = None,
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
        currency_type: Optional filter — 'real' for USD/EUR, 'play' for PLAY,
            None for all.

    Returns:
        DataFrame of hero's post-flop actions across all hands.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    if currency_type == "real":
        currency_clause = "AND s.currency IN ('USD', 'EUR')"
    elif currency_type == "play":
        currency_clause = "AND s.currency = 'PLAY'"
    else:
        currency_clause = ""
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
        JOIN sessions s ON s.id = h.session_id
        WHERE a.player_id = :pid
          AND a.street IN ('FLOP', 'TURN', 'RIVER')
          {date_clause} {currency_clause}
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_hand_players(
    conn: sqlite3.Connection,
    player_id: int,
    since_date: str | None = None,
    currency_type: str | None = None,
) -> pd.DataFrame:
    """Return all hand_player rows for hero with session context and saw_flop flag.

    Columns: hand_id, session_id, vpip, pfr, went_to_showdown, net_result,
             position, hole_cards, big_blind, saw_flop.

    `saw_flop` is 1 if hero had at least one action on the FLOP street,
    0 otherwise (i.e. folded or sat out preflop).

    Args:
        conn: Open SQLite connection.
        player_id: Internal integer id of the hero player row.
        since_date: Optional ISO-format date string. Filters to hands after
            this date (inclusive).
        currency_type: Optional filter — 'real' for USD/EUR, 'play' for PLAY,
            None for all.

    Returns:
        DataFrame with one row per hand hero participated in.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    if currency_type == "real":
        currency_clause = "AND s.currency IN ('USD', 'EUR')"
    elif currency_type == "play":
        currency_clause = "AND s.currency = 'PLAY'"
    else:
        currency_clause = ""
    sql = f"""
        SELECT
            hp.hand_id,
            h.session_id,
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
        WHERE hp.player_id = :pid {date_clause} {currency_clause}
        ORDER BY h.timestamp ASC
    """
    params: dict[str, int | str] = {"pid": int(player_id)}
    if since_date:
        params["since"] = since_date
    return pd.read_sql_query(sql, conn, params=params)


def get_hero_opportunity_actions(
    conn: sqlite3.Connection,
    player_id: int,
    since_date: str | None = None,
    currency_type: str | None = None,
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
        currency_type: Optional filter — 'real' for USD/EUR, 'play' for PLAY,
            None for all.

    Returns:
        DataFrame ordered by hand_id then sequence ascending.
    """
    date_clause = "AND h.timestamp >= :since" if since_date else ""
    if currency_type == "real":
        currency_clause = "AND s.currency IN ('USD', 'EUR')"
    elif currency_type == "play":
        currency_clause = "AND s.currency = 'PLAY'"
    else:
        currency_clause = ""
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
        JOIN sessions s ON s.id = h.session_id
        WHERE h.id IN (
            SELECT DISTINCT hand_id FROM hand_players WHERE player_id = :pid
        )
          AND a.street IN ('PREFLOP', 'FLOP')
          {date_clause} {currency_clause}
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


def get_session_kpis(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return per-hand hero rows for a single session.

    Same column structure as get_hero_hand_players but scoped to one session.
    Used to compute session-scoped VPIP%, PFR%, Win Rate, WTSD%, and hand count
    by passing the result directly to the existing stats.py helper functions.

    Columns: vpip, pfr, went_to_showdown, net_result, position, hole_cards,
             big_blind, saw_flop.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per hand hero participated in the session.
    """
    sql = """
        SELECT
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
        WHERE hp.player_id = :hero
          AND h.session_id = :sid
        ORDER BY h.timestamp ASC
    """
    return pd.read_sql_query(
        sql, conn, params={"hero": int(hero_id), "sid": int(session_id)}
    )


def get_session_hero_actions(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return hero's post-flop actions for a single session.

    Same column structure as get_hero_actions but scoped to one session.
    Only FLOP, TURN, and RIVER streets are returned.
    Used to compute session-scoped Aggression Factor (AF).

    Columns: hand_id, street, action_type, position.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row.

    Returns:
        DataFrame of hero's post-flop actions in the session.
    """
    sql = """
        SELECT
            a.hand_id,
            a.street,
            a.action_type,
            hp.position
        FROM actions a
        JOIN hand_players hp
            ON hp.hand_id = a.hand_id AND hp.player_id = a.player_id
        JOIN hands h ON h.id = a.hand_id
        WHERE a.player_id = :hero
          AND h.session_id = :sid
          AND a.street IN ('FLOP', 'TURN', 'RIVER')
        ORDER BY a.hand_id, a.sequence
    """
    return pd.read_sql_query(
        sql, conn, params={"hero": int(hero_id), "sid": int(session_id)}
    )


def get_session_showdown_hands(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return hands where hero went to showdown for a single session.

    Each row is a hero vs villain matchup where both sides showed cards
    and the hero actually reached showdown (went_to_showdown = 1).
    In multiway pots all opponents who showed cards are included.
    villain_cards is a pipe-separated string of all villain hole-card pairs
    (e.g. ``"Kh Qd"`` heads-up, ``"Kh Qd|9c 8c"`` for two opponents).
    villain_username is a comma-separated list of all villain names.
    Used to batch-compute equity via compute_equity_multiway and build the
    EV luck indicator in the Session Report.

    Columns: hand_id, source_hand_id, hero_cards, villain_username,
             villain_cards, board, net_result, total_pot.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per showdown hand (hero reached showdown).
    """
    sql = """
        SELECT
            h.id AS hand_id,
            h.source_hand_id,
            hero_hp.hole_cards AS hero_cards,
            GROUP_CONCAT(villain_p.username, ', ') AS villain_username,
            GROUP_CONCAT(villain_hp.hole_cards, '|') AS villain_cards,
            TRIM(
                COALESCE(h.board_flop, '') || ' ' ||
                COALESCE(h.board_turn, '') || ' ' ||
                COALESCE(h.board_river, '')
            ) AS board,
            hero_hp.net_result,
            h.total_pot
        FROM hands h
        JOIN hand_players hero_hp
            ON hero_hp.hand_id = h.id AND hero_hp.player_id = :hero
        JOIN hand_players villain_hp
            ON villain_hp.hand_id = h.id
           AND villain_hp.player_id != :hero
           AND villain_hp.hole_cards IS NOT NULL
           AND villain_hp.hole_cards != ''
        JOIN players villain_p ON villain_p.id = villain_hp.player_id
        WHERE h.session_id = :sid
          AND hero_hp.went_to_showdown = 1
          AND hero_hp.hole_cards IS NOT NULL
          AND hero_hp.hole_cards != ''
        GROUP BY h.id
        ORDER BY h.timestamp ASC
    """
    return pd.read_sql_query(
        sql, conn, params={"hero": int(hero_id), "sid": int(session_id)}
    )


def get_session_player_stats(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return per-opponent aggregated stats for a single session.

    Columns: username, hands_played, vpip_count, pfr_count.

    Only players other than the hero are returned. Used to characterise
    opponents (TAG / LAG / Nit / Fish) on the sessions page.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row (excluded from results).

    Returns:
        DataFrame with one row per opponent, ordered by hands_played descending.
    """
    sql = """
        SELECT
            p.username,
            COUNT(*)            AS hands_played,
            SUM(hp.vpip)        AS vpip_count,
            SUM(hp.pfr)         AS pfr_count
        FROM hand_players hp
        JOIN hands h ON h.id = hp.hand_id
        JOIN players p ON p.id = hp.player_id
        WHERE h.session_id = :sid
          AND hp.player_id != :hero
        GROUP BY hp.player_id
        ORDER BY hands_played DESC
    """
    return pd.read_sql_query(
        sql, conn, params={"sid": int(session_id), "hero": int(hero_id)}
    )


def get_session_hero_ev_actions(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return all hero CALL/BET/RAISE actions in a session for EV computation.

    Only actions where hero has hole cards are returned (NULL hole_cards rows
    are excluded at the SQL level — the orchestrator would skip them anyway).

    Columns: action_id, hand_id, street, action_type, amount, amount_to_call,
             pot_before, is_all_in, sequence, hero_cards, board_flop,
             board_turn, board_river, total_pot.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row.

    Returns:
        DataFrame ordered by hand_id, sequence ascending.
    """
    sql = """
        SELECT
            a.id           AS action_id,
            a.hand_id,
            a.street,
            a.action_type,
            a.amount,
            a.amount_to_call,
            a.pot_before,
            a.is_all_in,
            a.sequence,
            hp_hero.hole_cards AS hero_cards,
            h.board_flop,
            h.board_turn,
            h.board_river,
            h.total_pot
        FROM actions a
        JOIN hands h ON h.id = a.hand_id
        JOIN hand_players hp_hero
            ON hp_hero.hand_id = a.hand_id
           AND hp_hero.player_id = :hero
        WHERE h.session_id = :sid
          AND a.player_id  = :hero
          AND a.action_type IN ('CALL', 'BET', 'RAISE')
          AND hp_hero.hole_cards IS NOT NULL
          AND hp_hero.hole_cards != ''
        ORDER BY a.hand_id ASC, a.sequence ASC
    """
    return pd.read_sql_query(
        sql, conn, params={"hero": int(hero_id), "sid": int(session_id)}
    )


def get_session_ev_status(
    conn: sqlite3.Connection,
    session_id: int,
) -> tuple[int, str | None]:
    """Return EV cache summary for a session.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.

    Returns:
        ``(count, latest_computed_at)`` where *count* is the number of
        ``action_ev_cache`` rows belonging to the session and
        *latest_computed_at* is the ISO 8601 timestamp of the most recently
        written row, or ``None`` when no rows exist.
    """
    row = conn.execute(
        """
        SELECT COUNT(*), MAX(aec.computed_at)
        FROM action_ev_cache aec
        JOIN actions a ON aec.action_id = a.id
        JOIN hands h ON a.hand_id = h.id
        WHERE h.session_id = ?
        """,
        (session_id,),
    ).fetchone()
    count = int(row[0]) if row and row[0] else 0
    computed_at = str(row[1]) if row and row[1] else None
    return count, computed_at


def get_session_showdown_evs(
    conn: sqlite3.Connection,
    session_id: int,
    hero_id: int,
) -> pd.DataFrame:
    """Return one exact-EV row per hand for Lucky/Unlucky classification.

    Queries ``action_ev_cache`` for ``ev_type = 'exact'`` rows on all-in or
    RIVER actions.  One row per hand is returned (the earliest qualifying
    action by action id).

    Columns: hand_id, source_hand_id, equity, net_result.

    Args:
        conn: Open SQLite connection.
        session_id: Internal integer id of the session row.
        hero_id: Internal integer id of the hero player row.

    Returns:
        DataFrame with one row per hand that has an exact EV cached.
    """
    sql = """
        SELECT
            h.id          AS hand_id,
            h.source_hand_id,
            aec.equity,
            hero_hp.net_result
        FROM action_ev_cache aec
        JOIN actions a ON aec.action_id = a.id
        JOIN hands h ON h.id = a.hand_id
        JOIN hand_players hero_hp
            ON hero_hp.hand_id = h.id
           AND hero_hp.player_id = :hero
        WHERE h.session_id = :sid
          AND aec.hero_id  = :hero
          AND aec.ev_type  = 'exact'
          AND (a.is_all_in = 1 OR a.street = 'RIVER')
          AND a.id = (
              SELECT MIN(a2.id)
              FROM action_ev_cache aec2
              JOIN actions a2 ON aec2.action_id = a2.id
              WHERE a2.hand_id = h.id
                AND aec2.hero_id = :hero
                AND aec2.ev_type = 'exact'
                AND (a2.is_all_in = 1 OR a2.street = 'RIVER')
          )
        ORDER BY h.id ASC
    """
    return pd.read_sql_query(
        sql, conn, params={"hero": int(hero_id), "sid": int(session_id)}
    )
