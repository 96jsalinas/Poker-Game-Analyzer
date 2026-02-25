"""Pre-flop range building and Bayesian blending for villain range estimation.

Pure functions only — no database access.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# HAND_RANKING — 169 canonical pre-flop hands in descending strength order
# ---------------------------------------------------------------------------

HAND_RANKING: list[str] = [
    # Tier: premium / near-premium pairs and Broadway
    "AA",
    "KK",
    "QQ",
    "JJ",
    "TT",
    "99",
    "AKs",
    "88",
    "AQs",
    "AJs",
    "KQs",
    "ATs",
    "77",
    "KJs",
    "AKo",
    "QJs",
    "KTs",
    "AQo",
    "66",
    "JTs",
    "A9s",
    "AJo",
    "KQo",
    "A8s",
    "QTs",
    "KJo",
    "55",
    "K9s",
    "A7s",
    "JTo",
    "QJo",
    "ATo",
    "A6s",
    "KTo",
    "44",
    "T9s",
    "A5s",
    "Q9s",
    "A4s",
    "J9s",
    "K8s",
    "A3s",
    "33",
    "A2s",
    "QTo",
    "T8s",
    "98s",
    "K7s",
    "J8s",
    "Q8s",
    "22",
    "K6s",
    "A9o",
    "87s",
    "T7s",
    "K5s",
    "J9o",
    "Q9o",
    "97s",
    "76s",
    "K4s",
    "T9o",
    "K3s",
    "A8o",
    "Q7s",
    "86s",
    "K2s",
    "J7s",
    "75s",
    "T8o",
    "65s",
    "K9o",
    "J8o",
    "96s",
    "A7o",
    "Q6s",
    "98o",
    "85s",
    "T7o",
    "64s",
    "Q5s",
    "J6s",
    "A6o",
    "87o",
    "K8o",
    "54s",
    "Q4s",
    "74s",
    "97o",
    "J5s",
    "A5o",
    "76o",
    "Q3s",
    "63s",
    "86o",
    "J4s",
    "A4o",
    "Q2s",
    "53s",
    "65o",
    "75o",
    "J3s",
    "K7o",
    "96o",
    "43s",
    "T6s",
    "A3o",
    "J2s",
    "52s",
    "85o",
    "T5s",
    "64o",
    "A2o",
    "K6o",
    "T4s",
    "J7o",
    "42s",
    "74o",
    "95s",
    "54o",
    "Q7o",
    "T3s",
    "K5o",
    "63o",
    "T2s",
    "J6o",
    "84s",
    "K4o",
    "Q6o",
    "32s",
    "53o",
    "J5o",
    "94s",
    "73s",
    "43o",
    "K3o",
    "Q5o",
    "T6o",
    "62s",
    "84o",
    "J4o",
    "93s",
    "K2o",
    "52o",
    "Q4o",
    "T5o",
    "83s",
    "J3o",
    "Q3o",
    "42o",
    "T4o",
    "Q2o",
    "72s",
    "J2o",
    "95o",
    "T3o",
    "82s",
    "94o",
    "T2o",
    "93o",
    "73o",
    "Q8o",
    "62o",
    "83o",
    "92s",
    "82o",
    "92o",
    "32o",
    "72o",
]

_N = len(HAND_RANKING)  # 169


# ---------------------------------------------------------------------------
# Bayesian blend helpers
# ---------------------------------------------------------------------------


def blend_vpip(
    observed: float | None,
    n_hands: int,
    prior: float = 26.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed VPIP% with population prior.

    Formula: (n × observed + k × prior) / (n + k)

    Args:
        observed: Villain's observed VPIP as a percentage (0–100), or None.
        n_hands: Number of hands observed for this villain.
        prior: Population-average VPIP prior (%).
        k: Prior weight — higher = more regression to prior on small samples.

    Returns:
        Blended VPIP percentage (0–100).
    """
    if observed is None or n_hands == 0:
        return prior
    return (n_hands * observed + k * prior) / (n_hands + k)


def blend_pfr(
    observed: float | None,
    n_hands: int,
    prior: float = 14.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed PFR% with population prior.

    Args:
        observed: Villain's observed PFR as a percentage (0–100), or None.
        n_hands: Number of hands observed for this villain.
        prior: Population-average PFR prior (%).
        k: Prior weight.

    Returns:
        Blended PFR percentage (0–100).
    """
    if observed is None or n_hands == 0:
        return prior
    return (n_hands * observed + k * prior) / (n_hands + k)


def blend_3bet(
    observed: float | None,
    n_hands: int,
    prior: float = 6.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed 3-bet% with population prior.

    Falls back to prior when n_hands == 0 or observed is None, because
    3-bet samples are almost always too sparse to be informative early.

    Args:
        observed: Villain's observed 3-bet% (0–100), or None.
        n_hands: Number of hands observed for this villain.
        prior: Population-average 3-bet prior (%).
        k: Prior weight.

    Returns:
        Blended 3-bet percentage (0–100).
    """
    if observed is None or n_hands == 0:
        return prior
    return (n_hands * observed + k * prior) / (n_hands + k)


# ---------------------------------------------------------------------------
# Range builder
# ---------------------------------------------------------------------------


def build_range(
    vpip_pct: float,
    pfr_pct: float,
    three_bet_pct: float,
    villain_preflop_action: str,
    four_bet_prior: float = 3.0,
) -> list[str]:
    """Return villain's pre-flop range as a list of canonical hand strings.

    Slices HAND_RANKING based on the villain's observed action:

    - ``'call'``  → flatting range: hands at ranks [pfr_pct%, vpip_pct%)
    - ``'2bet'``  → open-raise range: top pfr_pct% of HAND_RANKING
    - ``'3bet'``  → 3-bet range: top three_bet_pct% of HAND_RANKING
    - ``'4bet+'`` → 4-bet range: top four_bet_prior% (fixed, no Bayesian blend)

    Args:
        vpip_pct: Blended VPIP percentage (0–100).
        pfr_pct: Blended PFR percentage (0–100).
        three_bet_pct: Blended 3-bet percentage (0–100).
        villain_preflop_action: One of ``'call'``, ``'2bet'``, ``'3bet'``,
            ``'4bet+'``.
        four_bet_prior: Fixed prior used for 4-bet+ ranges (%).

    Returns:
        List of hand strings from HAND_RANKING (e.g. ``['AA', 'KK', 'AKs']``).

    Raises:
        ValueError: If ``villain_preflop_action`` is not a recognised value.
    """
    if villain_preflop_action == "2bet":
        top_n = max(1, round(_N * pfr_pct / 100))
        return HAND_RANKING[:top_n]

    if villain_preflop_action == "3bet":
        top_n = max(1, round(_N * three_bet_pct / 100))
        return HAND_RANKING[:top_n]

    if villain_preflop_action == "4bet+":
        top_n = max(1, round(_N * four_bet_prior / 100))
        return HAND_RANKING[:top_n]

    if villain_preflop_action == "call":
        lo = max(0, round(_N * pfr_pct / 100))
        hi = max(lo, round(_N * vpip_pct / 100))
        return HAND_RANKING[lo:hi]

    raise ValueError(
        f"Unknown villain_preflop_action: {villain_preflop_action!r}. "
        "Expected one of: 'call', '2bet', '3bet', '4bet+'"
    )
