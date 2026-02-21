"""Statistical calculation functions for the analysis layer.

All functions accept a pandas DataFrame (as returned by queries.py) and
return a single scalar value. They are pure functions with no side effects
and no database access.

Formulas are defined in AnalysisLogic.MD as the single source of truth.
"""

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
        hero_first_seq = int(hero_rows["sequence"].iloc[0])
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


def compute_ev(
    hero_cards: str,
    villain_cards: str | None,
    board: str,
    amount_risked: float,
    pot_to_win: float,
    sample_count: int = 5000,
) -> float | None:
    """Compute Expected Value of hero's all-in action using PokerKit equity.

    EV = (equity × pot_to_win) − ((1 − equity) × amount_risked)

    Equity is calculated via Monte Carlo simulation using PokerKit's
    calculate_equities function.

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
        Float EV value, or None when villain cards are unknown.
    """
    if not villain_cards or not villain_cards.strip():
        return None

    from pokerkit import Card, Deck, StandardHighHand, calculate_equities, parse_range

    hero_range = parse_range(hero_cards.replace(" ", ""))
    villain_range = parse_range(villain_cards.replace(" ", ""))
    board_cards = list(Card.parse(board)) if board.strip() else []

    equities = calculate_equities(
        (hero_range, villain_range),
        board_cards,
        hole_dealing_count=2,
        board_dealing_count=5,
        deck=Deck.STANDARD,
        hand_types=(StandardHighHand,),
        sample_count=sample_count,
    )
    equity = equities[0]
    return equity * pot_to_win - (1.0 - equity) * amount_risked
