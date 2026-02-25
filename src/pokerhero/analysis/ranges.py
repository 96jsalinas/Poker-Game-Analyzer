"""Pre-flop range building and Bayesian blending for villain range estimation.

Pure functions only — no database access.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# HAND_RANKING — 169 canonical pre-flop hands in descending strength order
#
# Derived from the Chen Formula (Bill Chen, "The Mathematics of Poker").
# Hands are sorted by their Chen score (descending); ties preserve Python
# sort stability (suited before offsuit, higher rank first).
# Chen score is shown in comments for each tier.
# ---------------------------------------------------------------------------

HAND_RANKING: list[str] = [
    # Chen score: 20
    "AA",
    # Chen score: 16
    "KK",
    # Chen score: 14
    "QQ",
    # Chen score: 12
    "AKs",
    "JJ",
    # Chen score: 11
    "AQs",
    # Chen score: 10
    "AKo",
    "AJs",
    "KQs",
    "TT",
    # Chen score: 9
    "AQo",
    "KJs",
    "QJs",
    "JTs",
    "99",
    # Chen score: 8
    "AJo",
    "ATs",
    "KQo",
    "KTs",
    "QTs",
    "J9s",
    "T9s",
    "88",
    # Chen score: 7.5
    "98s",
    # Chen score: 7
    "A9s",
    "A8s",
    "A7s",
    "A6s",
    "A5s",
    "A4s",
    "A3s",
    "A2s",
    "KJo",
    "QJo",
    "Q9s",
    "JTo",
    "T8s",
    "87s",
    "77",
    # Chen score: 6.5
    "97s",
    "76s",
    # Chen score: 6
    "ATo",
    "KTo",
    "K9s",
    "QTo",
    "J9o",
    "J8s",
    "T9o",
    "86s",
    "65s",
    "66",
    # Chen score: 5.5
    "98o",
    "75s",
    "54s",
    # Chen score: 5
    "A9o",
    "A8o",
    "A7o",
    "A6o",
    "A5o",
    "A4o",
    "A3o",
    "A2o",
    "K8s",
    "K7s",
    "K6s",
    "K5s",
    "K4s",
    "K3s",
    "K2s",
    "Q9o",
    "Q8s",
    "T8o",
    "T7s",
    "87o",
    "64s",
    "55",
    "43s",
    "44",
    "33",
    "22",
    # Chen score: 4.5
    "97o",
    "96s",
    "76o",
    "53s",
    "32s",
    # Chen score: 4
    "K9o",
    "Q7s",
    "Q6s",
    "Q5s",
    "Q4s",
    "Q3s",
    "Q2s",
    "J8o",
    "J7s",
    "86o",
    "85s",
    "65o",
    "42s",
    # Chen score: 3.5
    "75o",
    "74s",
    "54o",
    # Chen score: 3
    "K8o",
    "K7o",
    "K6o",
    "K5o",
    "K4o",
    "K3o",
    "K2o",
    "Q8o",
    "J6s",
    "J5s",
    "J4s",
    "J3s",
    "J2s",
    "T7o",
    "T6s",
    "64o",
    "63s",
    "43o",
    # Chen score: 2.5
    "96o",
    "95s",
    "53o",
    "52s",
    "32o",
    # Chen score: 2
    "Q7o",
    "Q6o",
    "Q5o",
    "Q4o",
    "Q3o",
    "Q2o",
    "J7o",
    "T5s",
    "T4s",
    "T3s",
    "T2s",
    "85o",
    "84s",
    "42o",
    # Chen score: 1.5
    "94s",
    "93s",
    "92s",
    "74o",
    "73s",
    # Chen score: 1
    "J6o",
    "J5o",
    "J4o",
    "J3o",
    "J2o",
    "T6o",
    "83s",
    "82s",
    "63o",
    "62s",
    # Chen score: 0.5
    "95o",
    "72s",
    "52o",
    # Chen score: 0
    "T5o",
    "T4o",
    "T3o",
    "T2o",
    "84o",
    # Chen score: -0.5
    "94o",
    "93o",
    "92o",
    "73o",
    # Chen score: -1
    "83o",
    "82o",
    "62o",
    # Chen score: -1.5
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


# ---------------------------------------------------------------------------
# Combo expansion
# ---------------------------------------------------------------------------

_SUITS = "cdhs"
_RANKS = "AKQJT98765432"


def expand_combos(range_hands: list[str], dead_cards: set[str]) -> list[str]:
    """Expand shorthand hands to specific two-card combos, filtering dead cards.

    Args:
        range_hands: List of canonical hand strings, e.g. ``['AA', 'AKs', 'AKo']``.
        dead_cards: Set of individual card strings to exclude (e.g. ``{'Ah', 'Kd'}``).
            Typically hero's hole cards plus all board cards seen so far.

    Returns:
        List of space-separated combo strings, e.g. ``['Ac Kc', 'Ad Kd', ...]``,
        with every combo containing a dead card removed.
    """
    combos: list[str] = []
    for hand in range_hands:
        if len(hand) == 2:
            # Pocket pair: e.g. "AA"
            r = hand[0]
            suited_cards = [r + s for s in _SUITS]
            for i in range(4):
                for j in range(i + 1, 4):
                    c1, c2 = suited_cards[i], suited_cards[j]
                    if c1 not in dead_cards and c2 not in dead_cards:
                        combos.append(f"{c1} {c2}")
        elif hand.endswith("s"):
            # Suited: e.g. "AKs"
            r1, r2 = hand[0], hand[1]
            for s in _SUITS:
                c1, c2 = r1 + s, r2 + s
                if c1 not in dead_cards and c2 not in dead_cards:
                    combos.append(f"{c1} {c2}")
        else:
            # Offsuit: e.g. "AKo"
            r1, r2 = hand[0], hand[1]
            for s1 in _SUITS:
                for s2 in _SUITS:
                    if s1 == s2:
                        continue
                    c1, c2 = r1 + s1, r2 + s2
                    if c1 not in dead_cards and c2 not in dead_cards:
                        combos.append(f"{c1} {c2}")
    return combos
