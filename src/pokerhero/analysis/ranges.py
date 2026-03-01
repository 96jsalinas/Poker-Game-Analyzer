"""Pre-flop range building and Bayesian blending for villain range estimation.

Pure functions only — no database access.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# HAND_RANKING — 169 canonical pre-flop hands in descending strength order
#
# Source: Standard equity/playability ranking based on hand strength vs. a
# random opponent hand and overall playability (position, implied odds).
# Suited connectors 76s, 65s, 54s, 43s, 32s were absent from the original
# source; they are inserted after 87s in descending connector order.
# ---------------------------------------------------------------------------

HAND_RANKING: list[str] = [
    # Premium / High Pairs / Strong Broadways
    "AA",
    "KK",
    "QQ",
    "JJ",
    "AKs",
    "AQs",
    "TT",
    "AKo",
    "AJs",
    "KQs",
    "99",
    "ATs",
    "AQo",
    "KJs",
    "88",
    "QJs",
    "KTs",
    "AJo",
    "77",
    "QTs",
    "ATo",
    "KQo",
    "JTs",
    "66",
    "KJo",
    # Medium Pairs / Medium Suited Broadways / Strong Suited Connectors
    "Q9s",
    "A9s",
    "A8s",
    "K9s",
    "55",
    "A7s",
    "A5s",
    "A6s",
    "A4s",
    "A3s",
    "A2s",
    "J9s",
    "T9s",
    "KTo",
    "QJo",
    "44",
    "98s",
    "T8s",
    "J8s",
    "Q8s",
    "K8s",
    "33",
    "22",
    "87s",
    "76s",
    "65s",
    "54s",
    "43s",
    "32s",
    # Weak Broadways / Suited Gappers / Medium Suited Connectors
    "QTo",
    "JTo",
    "97s",
    "T7s",
    "J7s",
    "Q7s",
    "K7s",
    "86s",
    "96s",
    "T6s",
    "J6s",
    "Q6s",
    "K6s",
    "75s",
    "85s",
    "95s",
    "T5s",
    "J5s",
    "Q5s",
    "K5s",
    "64s",
    "74s",
    "84s",
    "94s",
    "T4s",
    "J4s",
    "Q4s",
    "K4s",
    # Low Suited Connectors / Baby Suited Hands
    "53s",
    "63s",
    "73s",
    "83s",
    "93s",
    "T3s",
    "J3s",
    "Q3s",
    "K3s",
    "42s",
    "52s",
    "62s",
    "72s",
    "82s",
    "92s",
    "T2s",
    "J2s",
    "Q2s",
    "K2s",
    # Weak Offsuit Aces and Kings
    "A9o",
    "A8o",
    "A7o",
    "A6o",
    "A5o",
    "A4o",
    "A3o",
    "A2o",
    "K9o",
    "K8o",
    "K7o",
    "K6o",
    "K5o",
    "K4o",
    "K3o",
    "K2o",
    # Weak Offsuit Queens and Jacks
    "Q9o",
    "Q8o",
    "Q7o",
    "Q6o",
    "Q5o",
    "Q4o",
    "Q3o",
    "Q2o",
    "J9o",
    "J8o",
    "J7o",
    "J6o",
    "J5o",
    "J4o",
    "J3o",
    "J2o",
    # Pure Trash (Unplayable offsuit gappers and low cards)
    "T9o",
    "T8o",
    "T7o",
    "T6o",
    "T5o",
    "T4o",
    "T3o",
    "T2o",
    "98o",
    "97o",
    "96o",
    "95o",
    "94o",
    "93o",
    "92o",
    "87o",
    "86o",
    "85o",
    "84o",
    "83o",
    "82o",
    "76o",
    "75o",
    "74o",
    "73o",
    "72o",
    "65o",
    "64o",
    "63o",
    "62o",
    "54o",
    "53o",
    "52o",
    "43o",
    "42o",
    "32o",
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
    hand_ranking: list[str] | None = None,
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
        hand_ranking: Custom hand ranking list to use instead of the module
            default ``HAND_RANKING``. Pass ``None`` to use the default.

    Returns:
        List of hand strings from the ranking (e.g. ``['AA', 'KK', 'AKs']``).

    Raises:
        ValueError: If ``villain_preflop_action`` is not a recognised value.
    """
    ranking = hand_ranking if hand_ranking is not None else HAND_RANKING
    n = len(ranking)

    if villain_preflop_action == "2bet":
        top_n = max(1, round(n * pfr_pct / 100))
        return ranking[:top_n]

    if villain_preflop_action == "3bet":
        top_n = max(1, round(n * three_bet_pct / 100))
        return ranking[:top_n]

    if villain_preflop_action == "4bet+":
        top_n = max(1, round(n * four_bet_prior / 100))
        return ranking[:top_n]

    if villain_preflop_action == "call":
        lo = max(0, round(n * pfr_pct / 100))
        hi = max(lo, round(n * vpip_pct / 100))
        return ranking[lo:hi]

    raise ValueError(
        f"Unknown villain_preflop_action: {villain_preflop_action!r}. "
        "Expected one of: 'call', '2bet', '3bet', '4bet+'"
    )


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


# ---------------------------------------------------------------------------
# Draw detection constants (subtracted from treys score; lower = stronger)
# ---------------------------------------------------------------------------

_FLUSH_DRAW_BONUS: int = 3000
_OESD_BONUS: int = 2000
_GUTSHOT_BONUS: int = 800
_OVERCARD_BONUS: int = 400

# Rank index map: higher index = lower rank (A=0, 2=12)
_RANK_IDX: dict[str, int] = {r: i for i, r in enumerate(_RANKS)}


def _suit(card: str) -> str:
    return card[1]


def _rank_idx(card: str) -> int:
    return _RANK_IDX[card[0]]


def _detect_flush_draw(c1: str, c2: str, board_cards: list[str]) -> bool:
    """Return True if the combo has a flush draw against board_cards.

    Covers:
    - Standard: combo has 2 cards of suit S AND board has 2 of suit S
    - Monotone: combo has 1 card of suit S AND board has 3 of suit S
    """
    from collections import Counter

    board_suits = Counter(_suit(c) for c in board_cards)
    combo_suits = Counter([_suit(c1), _suit(c2)])

    for suit, board_count in board_suits.items():
        combo_count = combo_suits.get(suit, 0)
        if (combo_count == 2 and board_count >= 2) or (
            combo_count == 1 and board_count >= 3
        ):
            return True
    return False


def _detect_straight_draw(
    c1: str, c2: str, board_cards: list[str]
) -> tuple[bool, bool]:
    """Return (is_oesd, is_gutshot) for the combo against the board.

    Uses rank indices (A=0 … 2=12). Also considers Ace-low straights
    by appending rank index 13 for aces (treating A as both high and low).

    Boundary draws (A-K-Q-J, A-2-3-4) are classified as gutshot (4 outs)
    since only one end can complete the straight.

    A gutshot requires 4 of 5 consecutive ranks present (one internal gap),
    AND at least one of the combo cards must contribute to the draw.
    """
    combo_ranks = {_rank_idx(c) for c in [c1, c2]}
    board_ranks = {_rank_idx(c) for c in board_cards}
    all_ranks = combo_ranks | board_ranks
    # Add ace-low duplicate (idx 13) if any ace (idx 0) is present
    if 0 in all_ranks:
        all_ranks = all_ranks | {13}
    if 0 in combo_ranks:
        combo_ranks = combo_ranks | {13}

    is_oesd = False
    is_gutshot = False

    # Check for 4 consecutive ranks (potential OESD or boundary draw)
    for low in range(11):  # max window {10,11,12,13}
        window = {low, low + 1, low + 2, low + 3}
        if len(window & all_ranks) == 4:
            # True OESD requires both ends completable
            if low - 1 >= 0 and low + 4 <= 13:
                is_oesd = True
                break
            else:
                # Boundary draw (A-K-Q-J or A-2-3-4): only 4 outs
                is_gutshot = True

    # Check for gutshot: 4 of 5 consecutive ranks with 1 internal gap,
    # and at least one combo card is part of the 5-card window
    if not is_oesd and not is_gutshot:
        for low in range(10):  # max window {9,10,11,12,13}
            window = {low, low + 1, low + 2, low + 3, low + 4}
            if len(window & all_ranks) == 4 and (window & combo_ranks):
                is_gutshot = True
                break

    return is_oesd, is_gutshot


def _detect_two_overcards(c1: str, c2: str, board_cards: list[str]) -> bool:
    """Return True if both combo cards outrank every board card."""
    max_board_idx = max(_rank_idx(c) for c in board_cards)  # higher idx = lower rank
    return _rank_idx(c1) < max_board_idx and _rank_idx(c2) < max_board_idx


def score_combo_vs_board(combo: str, board: str) -> int:
    """Equity-aware hand score for range contraction sorting.

    Wraps treys.Evaluator with draw-detection bonuses so flush draws and
    straight draws are not discarded during contraction.

    Lower return value = stronger / more likely to continue.

    Args:
        combo: Space-separated two-card string, e.g. ``"Kh Qh"``.
        board: Space-separated board cards (3 or 4), e.g. ``"Ah 8h 2c"``.

    Returns:
        Adjusted score (int). Lower = stronger.
    """
    from treys import Card, Evaluator  # type: ignore[import-untyped]

    evaluator = Evaluator()
    c1_str, c2_str = combo.split()
    board_strs = board.split()

    # treys uses lowercase suits, uppercase ranks e.g. "Kh" → OK as-is
    c1 = Card.new(c1_str)
    c2 = Card.new(c2_str)
    board_cards_treys = [Card.new(c) for c in board_strs]

    base_score: int = evaluator.evaluate(board_cards_treys, [c1, c2])

    bonus = 0
    board_cards = board_strs  # plain strings for draw detection

    if _detect_flush_draw(c1_str, c2_str, board_cards):
        bonus += _FLUSH_DRAW_BONUS

    is_oesd, is_gutshot = _detect_straight_draw(c1_str, c2_str, board_cards)
    if is_oesd:
        bonus += _OESD_BONUS
    elif is_gutshot:
        bonus += _GUTSHOT_BONUS

    if _detect_two_overcards(c1_str, c2_str, board_cards):
        bonus += _OVERCARD_BONUS

    return base_score - bonus


_AGGRESSIVE_ACTIONS = {"bet", "raise"}


def contract_range(
    combos: list[str],
    board: str,
    villain_action: str,
    continue_pct_passive: float = 65.0,
    continue_pct_aggressive: float = 40.0,
) -> list[str]:
    """Contract villain range based on board texture and their action on this street.

    Algorithm:
      1. Score each combo using score_combo_vs_board (equity-aware).
      2. Sort combos by score (lower = stronger / more likely to continue).
      3. Keep top continue_pct% by count:
         - passive action (check/call)   → continue_pct_passive
         - aggressive action (bet/raise) → continue_pct_aggressive
      4. Return surviving combos.

    Args:
        combos: List of space-separated two-card combo strings.
        board: Space-separated board cards (3 or 4 cards).
        villain_action: One of ``'bet'``, ``'raise'``, ``'call'``, ``'check'``.
        continue_pct_passive: % of combos kept for passive actions.
        continue_pct_aggressive: % of combos kept for aggressive actions.

    Returns:
        Contracted list of combo strings (sorted strongest-first).
        Returns ``[]`` if no combos survive.
    """
    if not combos:
        return []

    pct = (
        continue_pct_aggressive
        if villain_action in _AGGRESSIVE_ACTIONS
        else continue_pct_passive
    )
    keep_n = round(len(combos) * pct / 100)
    if keep_n == 0:
        return []

    scored = sorted(combos, key=lambda c: score_combo_vs_board(c, board))
    return scored[:keep_n]
