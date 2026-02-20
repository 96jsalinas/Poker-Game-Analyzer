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
