"""Statistical calculation functions for the analysis layer.

All functions accept a pandas DataFrame (as returned by queries.py) and
return a single scalar value. They are pure functions with no side effects
and no database access.

Formulas are defined in AnalysisLogic.MD as the single source of truth.
"""

import functools

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

    An opportunity exists when a non-hero player has raised before hero's
    first preflop action. Hero making a 3-bet means hero raised after that.

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
        if pre_hero["action_type"].eq("RAISE").any():
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

    EV = (equity × pot_to_win) − ((1 − equity) × amount_risked)

    Equity is calculated via Monte Carlo simulation using PokerKit's
    calculate_equities function (see compute_equity). Results are cached
    by card and board combination so repeated page loads are instant.

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
    ev = equity * pot_to_win - (1.0 - equity) * amount_risked
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
