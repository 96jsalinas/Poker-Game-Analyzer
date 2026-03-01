"""Statistical calculation functions for the analysis layer.

All functions accept a pandas DataFrame (as returned by queries.py) and
return a single scalar value. They are pure functions with no side effects
and no database access.

Formulas are defined in AnalysisLogic.MD as the single source of truth.
"""

import functools
import sqlite3
from datetime import UTC

import pandas as pd


def vpip_pct(hp_df: pd.DataFrame) -> float:
    """Fraction of hands where hero voluntarily put money in preflop.

    VPIP = COUNT(vpip=1) / total_hands
    Excludes posting blinds (handled at parse time via the vpip flag).

    Args:
        hp_df: DataFrame with a 'vpip' column (integer 0/1).

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 for empty input.
    """
    if hp_df.empty:
        return 0.0
    return float(hp_df["vpip"].mean())


def pfr_pct(hp_df: pd.DataFrame) -> float:
    """Fraction of hands where hero raised preflop.

    PFR = COUNT(pfr=1) / total_hands

    Args:
        hp_df: DataFrame with a 'pfr' column (integer 0/1).

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 for empty input.
    """
    if hp_df.empty:
        return 0.0
    return float(hp_df["pfr"].mean())


def win_rate_bb100(hp_df: pd.DataFrame) -> float:
    """Win rate expressed in big blinds won per 100 hands (bb/100).

    win_rate = (sum(net_result / big_blind) / n_hands) * 100

    Args:
        hp_df: DataFrame with 'net_result' (float) and 'big_blind' (float) columns.

    Returns:
        Float. Positive = winning, negative = losing. Returns 0.0 for empty input.
    """
    if hp_df.empty:
        return 0.0
    bb_results = hp_df["net_result"] / hp_df["big_blind"]
    return float(bb_results.mean() * 100)


def aggression_factor(actions_df: pd.DataFrame) -> float:
    """Post-flop aggression factor: (bets + raises) / calls.

    AF = (total BETs + total RAISEs) / total CALLs  — post-flop only.
    Preflop actions, folds, and checks are excluded.
    When there are zero post-flop calls, returns float('inf') per
    AnalysisLogic.MD fallback rule.

    Args:
        actions_df: DataFrame with 'action_type' and 'street' columns.

    Returns:
        Float >= 0. Returns float('inf') when denominator is zero.
    """
    postflop = actions_df[actions_df["street"].isin(["FLOP", "TURN", "RIVER"])]
    aggressive = postflop["action_type"].isin(["BET", "RAISE"]).sum()
    calls = (postflop["action_type"] == "CALL").sum()
    if calls == 0:
        return float("inf")
    return float(aggressive / calls)


def wtsd_pct(hp_df: pd.DataFrame) -> float:
    """Fraction of flop-seen hands that reached showdown (WTSD%).

    WTSD% = COUNT(went_to_showdown=1) / COUNT(saw_flop=1)

    Args:
        hp_df: DataFrame with 'went_to_showdown' (int 0/1) and
               'saw_flop' (int 0/1) columns.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if no flops seen.
    """
    flop_hands = hp_df[hp_df["saw_flop"] == 1]
    if flop_hands.empty:
        return 0.0
    return float(flop_hands["went_to_showdown"].mean())


def total_profit(hp_df: pd.DataFrame) -> float:
    """Total net profit across all hands.

    Args:
        hp_df: DataFrame with a 'net_result' (float) column.

    Returns:
        Float. Returns 0.0 for empty input.
    """
    if hp_df.empty:
        return 0.0
    return float(hp_df["net_result"].sum())


def three_bet_pct(opp_df: pd.DataFrame) -> float:
    """Fraction of 3-bet opportunities where hero re-raised preflop.

    An opportunity exists when exactly one non-hero raise has occurred
    before hero's first voluntary preflop action. If two or more raises
    preceded hero (pot already 3-bet), it is a 4-bet+ opportunity and
    is excluded from this statistic.

    3Bet% = COUNT(hands where hero raised vs prior raiser)
            / COUNT(opportunities)

    Args:
        opp_df: DataFrame from get_hero_opportunity_actions with columns
                hand_id, saw_flop, sequence, is_hero, street, action_type.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 when no opportunities exist.
    """
    if opp_df.empty:
        return 0.0
    preflop = opp_df[opp_df["street"] == "PREFLOP"]
    opportunities = 0
    made = 0
    for _, hand in preflop.groupby("hand_id"):
        hand = hand.sort_values("sequence")
        hero_rows = hand[hand["is_hero"] == 1]
        if hero_rows.empty:
            continue
        hero_voluntary = hero_rows[
            ~hero_rows["action_type"].isin({"POST_BLIND", "POST_ANTE"})
        ]
        if hero_voluntary.empty:
            continue
        hero_first_seq = int(hero_voluntary["sequence"].iloc[0])
        pre_hero = hand[(hand["is_hero"] == 0) & (hand["sequence"] < hero_first_seq)]
        raise_count = int(pre_hero["action_type"].eq("RAISE").sum())
        if raise_count == 1:
            opportunities += 1
            if (hero_rows["action_type"] == "RAISE").any():
                made += 1
    if opportunities == 0:
        return 0.0
    return made / opportunities


def cbet_pct(opp_df: pd.DataFrame) -> float:
    """Fraction of c-bet opportunities where hero bet the flop.

    An opportunity exists when hero was the last pre-flop raiser and the
    hand reached the flop. Hero c-bets by placing the first BET action on
    the flop.

    CBet% = COUNT(hero bet flop as first aggressor)
            / COUNT(opportunities)

    Args:
        opp_df: DataFrame from get_hero_opportunity_actions with columns
                hand_id, saw_flop, sequence, is_hero, street, action_type.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 when no opportunities exist.
    """
    if opp_df.empty:
        return 0.0
    opportunities = 0
    made = 0
    for _, hand in opp_df.groupby("hand_id"):
        saw_flop = hand["saw_flop"].iloc[0] == 1
        preflop = hand[hand["street"] == "PREFLOP"].sort_values("sequence")
        flop = hand[hand["street"] == "FLOP"].sort_values("sequence")
        pf_raises = preflop[preflop["action_type"] == "RAISE"]
        if pf_raises.empty:
            continue
        if int(pf_raises.iloc[-1]["is_hero"]) != 1:
            continue
        if saw_flop and not flop.empty:
            opportunities += 1
            first_bets = flop[flop["action_type"] == "BET"]
            if not first_bets.empty and int(first_bets.iloc[0]["is_hero"]) == 1:
                made += 1
    if opportunities == 0:
        return 0.0
    return made / opportunities


@functools.lru_cache(maxsize=512)
def compute_equity(
    hero_cards: str,
    villain_cards: str,
    board: str,
    sample_count: int,
) -> float:
    """Compute hero's equity via PokerKit Monte Carlo simulation.

    Results are cached by (hero_cards, villain_cards, board, sample_count) so
    repeated calls for the same hand — e.g. navigating away and back — are
    instant after the first computation.

    Args:
        hero_cards: Hero hole cards, space-separated (e.g. "Ah Kh"). Must be
                    a non-empty, stripped string.
        villain_cards: Villain hole cards, space-separated (e.g. "2c 3d").
                       Must be a non-empty, stripped string.
        board: Space-separated board cards seen so far (e.g. "Qh Jh Th").
               Pass empty string "" for preflop all-ins.
        sample_count: Number of Monte Carlo samples.

    Returns:
        Float equity in [0.0, 1.0] representing hero's win probability.
    """
    from pokerkit import Card, Deck, StandardHighHand, calculate_equities, parse_range

    hero_range = parse_range(hero_cards.replace(" ", ""))
    villain_range = parse_range(villain_cards.replace(" ", ""))
    board_cards = list(Card.parse(board)) if board else []

    equities = calculate_equities(
        (hero_range, villain_range),
        board_cards,
        hole_dealing_count=2,
        board_dealing_count=5,
        deck=Deck.STANDARD,
        hand_types=(StandardHighHand,),
        sample_count=sample_count,
    )
    return float(equities[0])


@functools.lru_cache(maxsize=512)
def compute_equity_multiway(
    hero_cards: str,
    villain_cards_str: str,
    board: str,
    sample_count: int,
) -> float:
    """Compute hero's equity in a multiway pot via PokerKit Monte Carlo simulation.

    Accepts one or more villain hands as a pipe-separated string so the result
    can be LRU-cached (all arguments must be hashable).  For a heads-up hand
    pass villain cards without a pipe, e.g. ``"Ah Kh"``.  For a multiway hand
    separate each villain's hole cards with ``|``, e.g. ``"Ah Kh|2c 3d"``.

    Args:
        hero_cards: Hero hole cards, space-separated (e.g. ``"Tc Jd"``).
        villain_cards_str: One or more villain hole-card pairs, separated by
            ``|`` (e.g. ``"Kh Qd"`` or ``"Kh Qd|9c 8c"``).
        board: Space-separated board cards seen so far.  Pass ``""`` for
            preflop all-ins.
        sample_count: Number of Monte Carlo samples.

    Returns:
        Float equity in [0.0, 1.0] representing hero's win probability.
    """
    from pokerkit import Card, Deck, StandardHighHand, calculate_equities, parse_range

    hero_range = parse_range(hero_cards.replace(" ", ""))
    villain_ranges = tuple(
        parse_range(vc.strip().replace(" ", ""))
        for vc in villain_cards_str.split("|")
        if vc.strip()
    )
    board_cards = list(Card.parse(board)) if board else []

    equities = calculate_equities(
        (hero_range, *villain_ranges),
        board_cards,
        hole_dealing_count=2,
        board_dealing_count=5,
        deck=Deck.STANDARD,
        hand_types=(StandardHighHand,),
        sample_count=sample_count,
    )
    return float(equities[0])


def compute_ev(
    hero_cards: str,
    villain_cards: str | None,
    board: str,
    amount_risked: float,
    pot_to_win: float,
    sample_count: int = 5000,
) -> tuple[float, float] | None:
    """Compute Expected Value of hero's all-in action using PokerKit equity.

    EV = (equity × pot_to_win) − amount_risked

    This yields the net expected profit: Hero wins the full pot (including
    their own wager) with probability ``equity``, and loses their wager
    with probability ``(1 − equity)``.  Equivalently:
    ``EV = equity × (pot_before + wager) − wager``.

    Args:
        hero_cards: Hero hole cards as stored in DB (e.g. "Ah Kh").
        villain_cards: Villain hole cards as stored in DB (e.g. "2c 3d"),
                       or None / empty string if unknown.
        board: Space-separated board cards seen so far (e.g. "Qh Jh Th").
               Pass empty string for preflop all-ins.
        amount_risked: The amount hero is wagering in this action.
        pot_to_win: The total pot hero wins if they win the hand.
        sample_count: Monte Carlo samples for equity estimation.

    Returns:
        (ev, equity) tuple, or None when villain cards are unknown.
    """
    if not villain_cards or not villain_cards.strip():
        return None

    equity = compute_equity(
        hero_cards.strip(),
        villain_cards.strip(),
        board.strip(),
        sample_count,
    )
    ev = equity * pot_to_win - amount_risked
    return ev, equity


def compute_equity_vs_range(
    hero_cards: str,
    board: str,
    vpip_pct: float,
    pfr_pct: float,
    three_bet_pct: float,
    villain_preflop_action: str,
    villain_street_history: list[tuple[str, str]],
    four_bet_prior: float = 3.0,
    sample_count: int = 1000,
    continue_pct_passive: float = 65.0,
    continue_pct_aggressive: float = 40.0,
) -> tuple[float, int]:
    """Estimate hero equity against a range derived from villain's action history.

    Pipeline:
      1. build_range(vpip, pfr, three_bet_pct, villain_preflop_action)
      2. expand_combos dead-card filtered against hero cards + full board
      3. contract_range per intermediate street in villain_street_history
      4. Monte Carlo sampling of equity against contracted combos

    Args:
        hero_cards: Hero hole cards, space-separated (e.g. ``"Ah Kh"``).
        board: Full board at the current action's street, space-separated.
        vpip_pct: Villain VPIP percentage (0–100).
        pfr_pct: Villain PFR percentage (0–100).
        three_bet_pct: Villain 3-bet percentage (0–100).
        villain_preflop_action: One of ``'call'``, ``'2bet'``, ``'3bet'``,
            ``'4bet+'``.
        villain_street_history: Ordered list of ``(board_at_street,
            villain_action)`` tuples for streets before the current one.
            Empty for FLOP actions.
        four_bet_prior: Fixed prior % for 4-bet+ ranges.
        sample_count: Number of Monte Carlo samples.
        continue_pct_passive: % of combos retained for passive villain actions.
        continue_pct_aggressive: % of combos retained for aggressive actions.

    Returns:
        ``(equity, contracted_range_size)``.  Returns ``(0.0, 0)`` when fewer
        than 5 combos survive range contraction.
    """
    import random
    from collections import Counter

    from pokerhero.analysis.ranges import build_range, contract_range, expand_combos

    range_hands = build_range(
        vpip_pct, pfr_pct, three_bet_pct, villain_preflop_action, four_bet_prior
    )
    dead = set(hero_cards.split()) | (set(board.split()) if board else set())
    combos = expand_combos(range_hands, dead)

    for board_at_street, villain_action in villain_street_history:
        combos = contract_range(
            combos,
            board_at_street,
            villain_action.lower(),
            continue_pct_passive=continue_pct_passive,
            continue_pct_aggressive=continue_pct_aggressive,
        )

    if len(combos) < 5:
        return (0.0, 0)

    contracted_size = len(combos)
    sampled = random.choices(combos, k=sample_count)
    combo_counts = Counter(sampled)

    total_eq = 0.0
    total_n = 0
    for combo, n in combo_counts.items():
        eq = compute_equity(hero_cards.strip(), combo, board.strip(), n)
        total_eq += eq * n
        total_n += n

    return (total_eq / total_n, contracted_size)


_MIN_HANDS_FOR_CLASSIFICATION = 15
_PRELIMINARY_HANDS_THRESHOLD = 50
_CONFIRMED_HANDS_THRESHOLD = 100
_VPIP_LOOSE_THRESHOLD = 25.0  # % — at or above this → Loose
_AGG_RATIO_THRESHOLD = 0.5  # PFR / VPIP — at or above this → Aggressive


def classify_player(
    vpip_pct: float,
    pfr_pct: float,
    hands_played: int,
    min_hands: int = _MIN_HANDS_FOR_CLASSIFICATION,
) -> str | None:
    """Classify an opponent into a playing-style archetype.

    Uses a 2×2 matrix of VPIP (Tight/Loose) and aggression ratio
    (PFR / VPIP; Passive/Aggressive):

    | VPIP \\ Agg | Passive  | Aggressive |
    |------------|----------|------------|
    | Tight      | Nit      | TAG        |
    | Loose      | Fish     | LAG        |

    Aggression ratio is PFR / VPIP.  When VPIP is 0 the player never
    entered the pot, so they are always Tight-Passive (Nit).

    Args:
        vpip_pct: VPIP expressed as a percentage (0–100).
        pfr_pct: PFR expressed as a percentage (0–100).
        hands_played: Total hands observed for this player in the session.
        min_hands: Minimum hands required before an archetype is assigned.
            Defaults to the module-level ``_MIN_HANDS_FOR_CLASSIFICATION``
            (15). Pass a different value to override via the Settings UI.

    Returns:
        One of ``"TAG"``, ``"LAG"``, ``"Nit"``, ``"Fish"``, or ``None``
        when *hands_played* is below *min_hands*.
    """
    if hands_played < min_hands:
        return None

    is_loose = vpip_pct >= _VPIP_LOOSE_THRESHOLD
    agg_ratio = pfr_pct / vpip_pct if vpip_pct > 0 else 0.0
    is_aggressive = agg_ratio >= _AGG_RATIO_THRESHOLD

    if is_loose and is_aggressive:
        return "LAG"
    if is_loose:
        return "Fish"
    if is_aggressive:
        return "TAG"
    return "Nit"


def confidence_tier(hands_played: int) -> str:
    """Return the confidence tier for an opponent read based on hands observed.

    Tiers:
    - ``"preliminary"`` — fewer than 50 hands; read is tentative.
    - ``"standard"``    — 50–99 hands; reasonable sample.
    - ``"confirmed"``   — 100 or more hands; high-confidence read.

    Args:
        hands_played: Number of hands observed against this opponent.

    Returns:
        One of ``"preliminary"``, ``"standard"``, or ``"confirmed"``.
    """
    if hands_played >= _CONFIRMED_HANDS_THRESHOLD:
        return "confirmed"
    if hands_played >= _PRELIMINARY_HANDS_THRESHOLD:
        return "standard"
    return "preliminary"


# ---------------------------------------------------------------------------
# Private helpers for identify_primary_villain / calculate_session_evs
# ---------------------------------------------------------------------------


def _get_villain_preflop_action(
    conn: sqlite3.Connection,
    hand_id: int,
    villain_id: int,
) -> str | None:
    """Return villain's pre-flop action type for range building.

    Logic:
    - three_bet = 1 → '3bet'
    - pfr = 1 AND three_bet = 0, AND another player 3-bet in this hand → '4bet+'
    - pfr = 1 AND three_bet = 0, AND no 3-bettor → '2bet'
    - vpip = 1 AND pfr = 0 → 'call'
    - vpip = 0 → None (villain folded / didn't play)
    """
    row = conn.execute(
        "SELECT vpip, pfr, three_bet FROM hand_players"
        " WHERE hand_id = ? AND player_id = ?",
        (hand_id, villain_id),
    ).fetchone()
    if row is None:
        return None
    vpip, pfr, three_bet = int(row[0]), int(row[1]), int(row[2])
    if not vpip:
        return None
    if three_bet:
        return "3bet"
    if pfr:
        has_three_bettor = conn.execute(
            "SELECT 1 FROM hand_players WHERE hand_id = ? AND three_bet = 1 LIMIT 1",
            (hand_id,),
        ).fetchone()
        return "4bet+" if has_three_bettor else "2bet"
    return "call"


def _get_villain_session_stats(
    conn: sqlite3.Connection,
    session_id: int,
    villain_id: int,
) -> tuple[int, float, float, float]:
    """Return (n_hands, vpip_pct, pfr_pct, three_bet_pct) for villain in session.

    Used to compute Bayesian-blended range parameters.
    Returns (0, 0.0, 0.0, 0.0) when villain has no session history.
    """
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                  AS n_hands,
            100.0 * SUM(hp.vpip)    / COUNT(*)        AS vpip_pct,
            100.0 * SUM(hp.pfr)     / COUNT(*)        AS pfr_pct,
            100.0 * SUM(hp.three_bet) / COUNT(*)      AS three_bet_pct
        FROM hand_players hp
        JOIN hands h ON h.id = hp.hand_id
        WHERE h.session_id = ? AND hp.player_id = ?
        """,
        (session_id, villain_id),
    ).fetchone()
    if row is None or row[0] == 0:
        return 0, 0.0, 0.0, 0.0
    return (
        int(row[0]),
        float(row[1] or 0.0),
        float(row[2] or 0.0),
        float(row[3] or 0.0),
    )


def _get_villain_action_on_street(
    conn: sqlite3.Connection,
    hand_id: int,
    villain_id: int,
    street: str,
) -> str | None:
    """Return villain's last action type on the given street, or None."""
    row = conn.execute(
        "SELECT action_type FROM actions"
        " WHERE hand_id = ? AND player_id = ? AND street = ?"
        " ORDER BY sequence DESC LIMIT 1",
        (hand_id, villain_id, street),
    ).fetchone()
    return str(row[0]) if row else None


def _board_at_street(
    board_flop: str | None,
    board_turn: str | None,
    board_river: str | None,
    street: str,
) -> str:
    """Return the board string visible at the start of *street*."""
    flop = board_flop or ""
    turn = board_turn or ""
    river = board_river or ""
    if street == "FLOP":
        return flop.strip()
    if street == "TURN":
        return f"{flop} {turn}".strip()
    if street == "RIVER":
        return " ".join(x for x in [flop, turn, river] if x).strip()
    return ""


def _build_villain_street_history(
    conn: sqlite3.Connection,
    hand_id: int,
    villain_id: int,
    current_street: str,
    board_flop: str | None,
    board_turn: str | None,
) -> list[tuple[str, str]]:
    """Build villain street history list for streets before *current_street*.

    Each entry is (board_at_street, villain_action_type).  If the villain
    has no recorded action on an intermediate street, 'check' is assumed
    (most conservative / passive assumption for range contraction).
    """
    ordered = ["FLOP", "TURN", "RIVER"]
    try:
        idx = ordered.index(current_street)
    except ValueError:
        return []
    history: list[tuple[str, str]] = []
    for street in ordered[:idx]:
        board = _board_at_street(board_flop, board_turn, None, street)
        if not board:
            continue
        action = _get_villain_action_on_street(conn, hand_id, villain_id, street)
        history.append((board, action if action else "check"))
    return history


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def identify_primary_villain(
    conn: sqlite3.Connection,
    hand_id: int,
    hero_id: int,
    hero_sequence: int,
    street: str,
) -> int | None:
    """Identify the most relevant villain for EV calculation at a hero action.

    Algorithm:
    1. Find all non-hero players in the hand who have not folded before the
       hero's action (identified by sequence number).
    2. If exactly one active player → return them.
    3. If multiple → return the player who last BET or RAISED on *street*
       before hero's action.
    4. If no aggressor on this street → return the active villain with the
       most hands observed in the session (most data for Bayesian blending).
    5. If still ambiguous → return the first active villain by player_id.

    Args:
        conn: Open SQLite connection.
        hand_id: Internal hand id.
        hero_id: Internal player id for the hero.
        hero_sequence: Sequence number of the hero's action.
        street: Street of the hero's action (``'FLOP'``, ``'TURN'``, ``'RIVER'``).

    Returns:
        Internal player_id of the primary villain, or ``None`` if the hand
        is heads-up against no active opponent.
    """
    active_rows = conn.execute(
        """
        SELECT DISTINCT hp.player_id
        FROM hand_players hp
        WHERE hp.hand_id = :hid
          AND hp.player_id != :hero
          AND hp.player_id NOT IN (
              SELECT a.player_id FROM actions a
              WHERE a.hand_id = :hid
                AND a.action_type = 'FOLD'
                AND a.sequence < :seq
          )
        """,
        {"hid": hand_id, "hero": hero_id, "seq": hero_sequence},
    ).fetchall()
    active = [int(r[0]) for r in active_rows]
    if not active:
        return None
    if len(active) == 1:
        return active[0]

    # Last aggressor on this street before hero
    aggressor_row = conn.execute(
        """
        SELECT player_id FROM actions
        WHERE hand_id = ?
          AND street = ?
          AND action_type IN ('BET', 'RAISE')
          AND sequence < ?
        ORDER BY sequence DESC
        LIMIT 1
        """,
        (hand_id, street, hero_sequence),
    ).fetchone()
    if aggressor_row and int(aggressor_row[0]) in active:
        return int(aggressor_row[0])

    # Most-observed villain in the session
    session_id_row = conn.execute(
        "SELECT session_id FROM hands WHERE id = ?", (hand_id,)
    ).fetchone()
    if session_id_row:
        sid = int(session_id_row[0])
        placeholders = ",".join("?" * len(active))
        most_obs_row = conn.execute(
            f"""
            SELECT hp.player_id
            FROM hand_players hp
            JOIN hands h ON h.id = hp.hand_id
            WHERE h.session_id = ?
              AND hp.player_id IN ({placeholders})
            GROUP BY hp.player_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """,
            [sid, *active],
        ).fetchone()
        if most_obs_row:
            return int(most_obs_row[0])

    return active[0]


def calculate_session_evs(
    db_path: str,
    session_id: int,
    hero_id: int,
    settings: dict[str, float],
) -> int:
    """Compute and persist EV for all hero actions in a session.

    For each hero CALL/BET/RAISE action that has hole cards recorded:

    - If the primary villain's cards are known → ``compute_ev`` (exact).
    - Otherwise → ``compute_equity_vs_range`` with Bayesian-blended villain
      stats and street-by-street range contraction.
    - Actions where the contracted range collapses below 5 combos are skipped.

    Results are written to ``action_ev_cache`` in a single transaction.

    Args:
        db_path: Path to the SQLite database file.
        session_id: Internal session id to process.
        hero_id: Internal player id for the hero.
        settings: Dict of range settings (see ``RANGE_SETTING_DEFAULTS``).

    Returns:
        Count of ``action_ev_cache`` rows written.
    """
    from datetime import datetime

    from pokerhero.analysis.queries import get_session_hero_ev_actions
    from pokerhero.analysis.ranges import blend_3bet, blend_pfr, blend_vpip
    from pokerhero.database.db import get_connection, save_action_evs

    sample_count = int(settings.get("range_sample_count", 1000))
    vpip_prior = settings.get("range_vpip_prior", 26.0)
    pfr_prior = settings.get("range_pfr_prior", 14.0)
    three_bet_prior = settings.get("range_3bet_prior", 6.0)
    four_bet_prior = settings.get("range_4bet_prior", 3.0)
    prior_weight = int(settings.get("range_prior_weight", 30))
    cont_passive = settings.get("range_continue_pct_passive", 65.0)
    cont_aggressive = settings.get("range_continue_pct_aggressive", 40.0)
    fold_equity_default = settings.get("fold_equity_default_pct", 40.0)

    conn = get_connection(db_path)
    try:
        hero_actions = get_session_hero_ev_actions(conn, session_id, hero_id)
        if hero_actions.empty:
            return 0

        now = datetime.now(UTC).isoformat()
        rows: list[dict[str, object]] = []

        for _, ar in hero_actions.iterrows():
            action_id = int(ar["action_id"])
            hand_id = int(ar["hand_id"])
            street = str(ar["street"])
            hero_cards = str(ar["hero_cards"])
            board = _board_at_street(
                ar.get("board_flop"),
                ar.get("board_turn"),
                ar.get("board_river"),
                street,
            )
            amount_to_call = float(ar["amount_to_call"])
            amount = float(ar["amount"])
            pot_before = float(ar["pot_before"])
            # For CALL/FOLD: wager = amount_to_call; for BET/RAISE: wager = amount
            action_type = str(ar["action_type"])
            wager = amount_to_call if action_type in ("CALL", "FOLD") else amount
            pot_to_win = pot_before + wager

            villain_id = identify_primary_villain(
                conn, hand_id, hero_id, int(ar["sequence"]), street
            )
            if villain_id is None:
                continue

            # Gather all active non-hero villains with known hole cards
            all_villain_cards_rows = conn.execute(
                """
                SELECT hp.player_id, hp.hole_cards
                FROM hand_players hp
                WHERE hp.hand_id = :hid
                  AND hp.player_id != :hero
                  AND hp.hole_cards IS NOT NULL
                  AND hp.hole_cards != ''
                  AND hp.player_id NOT IN (
                      SELECT a.player_id FROM actions a
                      WHERE a.hand_id = :hid
                        AND a.action_type = 'FOLD'
                        AND a.sequence < :seq
                  )
                """,
                {
                    "hid": hand_id,
                    "hero": hero_id,
                    "seq": int(ar["sequence"]),
                },
            ).fetchall()
            known_villain_cards = {int(r[0]): str(r[1]) for r in all_villain_cards_rows}

            villain_cards: str | None = known_villain_cards.get(villain_id)

            if villain_cards:
                if len(known_villain_cards) > 1:
                    # Multiway exact: use all known villain hands
                    all_cards_str = "|".join(known_villain_cards.values())
                    equity = compute_equity_multiway(
                        hero_cards, all_cards_str, board, sample_count
                    )
                    ev = equity * pot_to_win - wager
                    ev_type = "exact_multiway"
                else:
                    result = compute_ev(
                        hero_cards,
                        villain_cards,
                        board,
                        wager,
                        pot_to_win,
                        sample_count,
                    )
                    if result is None:
                        continue
                    ev, equity = result
                    ev_type = "exact"

                # Apply fold equity for BET/RAISE actions
                fold_eq_pct: float | None = None
                if action_type in ("BET", "RAISE"):
                    fold_eq_pct = fold_equity_default
                    p_fold = fold_eq_pct / 100.0
                    showdown_ev = equity * pot_to_win - wager
                    ev = p_fold * pot_before + (1.0 - p_fold) * showdown_ev

                rows.append(
                    {
                        "action_id": action_id,
                        "hero_id": hero_id,
                        "equity": equity,
                        "ev": ev,
                        "ev_type": ev_type,
                        "blended_vpip": None,
                        "blended_pfr": None,
                        "blended_3bet": None,
                        "villain_preflop_action": None,
                        "contracted_range_size": None,
                        "fold_equity_pct": fold_eq_pct,
                        "sample_count": sample_count,
                        "computed_at": now,
                    }
                )
            else:
                preflop_action = _get_villain_preflop_action(conn, hand_id, villain_id)
                if preflop_action is None:
                    continue

                n_hands, obs_vpip, obs_pfr, obs_3bet = _get_villain_session_stats(
                    conn, session_id, villain_id
                )
                blended_v = blend_vpip(
                    obs_vpip if n_hands > 0 else None, n_hands, vpip_prior, prior_weight
                )
                blended_p = blend_pfr(
                    obs_pfr if n_hands > 0 else None, n_hands, pfr_prior, prior_weight
                )
                blended_3b = blend_3bet(
                    obs_3bet if n_hands > 0 else None,
                    n_hands,
                    three_bet_prior,
                    prior_weight,
                )

                street_history = _build_villain_street_history(
                    conn,
                    hand_id,
                    villain_id,
                    street,
                    ar.get("board_flop"),
                    ar.get("board_turn"),
                )

                equity, contracted_size = compute_equity_vs_range(
                    hero_cards=hero_cards,
                    board=board,
                    vpip_pct=blended_v,
                    pfr_pct=blended_p,
                    three_bet_pct=blended_3b,
                    villain_preflop_action=preflop_action,
                    villain_street_history=street_history,
                    four_bet_prior=four_bet_prior,
                    sample_count=sample_count,
                    continue_pct_passive=cont_passive,
                    continue_pct_aggressive=cont_aggressive,
                )
                if contracted_size < 5:
                    continue

                # Count active non-hero villains to detect multiway
                active_count = conn.execute(
                    """
                    SELECT COUNT(DISTINCT hp.player_id)
                    FROM hand_players hp
                    WHERE hp.hand_id = :hid
                      AND hp.player_id != :hero
                      AND hp.player_id NOT IN (
                          SELECT a.player_id FROM actions a
                          WHERE a.hand_id = :hid
                            AND a.action_type = 'FOLD'
                            AND a.sequence < :seq
                      )
                    """,
                    {
                        "hid": hand_id,
                        "hero": hero_id,
                        "seq": int(ar["sequence"]),
                    },
                ).fetchone()[0]
                range_ev_type = "range_multiway_approx" if active_count > 1 else "range"

                ev = equity * pot_to_win - wager

                # Apply fold equity for BET/RAISE actions
                fold_eq_pct_r: float | None = None
                if action_type in ("BET", "RAISE"):
                    fold_eq_pct_r = fold_equity_default
                    p_fold = fold_eq_pct_r / 100.0
                    showdown_ev = ev
                    ev = p_fold * pot_before + (1.0 - p_fold) * showdown_ev

                rows.append(
                    {
                        "action_id": action_id,
                        "hero_id": hero_id,
                        "equity": equity,
                        "ev": ev,
                        "ev_type": range_ev_type,
                        "blended_vpip": blended_v,
                        "blended_pfr": blended_p,
                        "blended_3bet": blended_3b,
                        "villain_preflop_action": preflop_action,
                        "contracted_range_size": contracted_size,
                        "fold_equity_pct": fold_eq_pct_r,
                        "sample_count": sample_count,
                        "computed_at": now,
                    }
                )

        if rows:
            save_action_evs(conn, rows)
            conn.commit()
        return len(rows)
    finally:
        conn.close()
