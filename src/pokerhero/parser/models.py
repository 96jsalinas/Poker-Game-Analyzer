"""Data models for parsed PokerStars hand history records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class SessionData:
    """Metadata that describes the table/game context for a hand."""

    table_name: str
    game_type: str  # e.g. "NLHE"
    limit_type: str  # e.g. "NL"
    small_blind: Decimal
    big_blind: Decimal
    ante: Decimal
    max_seats: int
    is_tournament: bool
    tournament_id: str | None = None
    tournament_level: str | None = None  # e.g. "Level I"
    currency: str = "PLAY"  # "USD", "EUR", or "PLAY" (play money / tournament chips)


@dataclass
class HandData:
    """Hand-level metadata: identifiers, board, pot, rake."""

    hand_id: str
    timestamp: datetime
    button_seat: int
    board_flop: str | None
    board_turn: str | None
    board_river: str | None
    total_pot: Decimal
    rake: Decimal
    uncalled_bet_returned: Decimal = Decimal("0")


@dataclass
class HandPlayerData:
    """Per-player record for a single hand."""

    username: str
    seat: int
    starting_stack: Decimal
    position: str  # BTN / SB / BB / UTG / UTG+1 / MP / MP+1 / CO
    hole_cards: str | None  # "Ad Qs" or None
    net_result: Decimal
    vpip: bool
    pfr: bool
    three_bet: bool
    went_to_showdown: bool
    is_hero: bool


@dataclass
class ActionData:
    """A single in-hand action (post, fold, call, bet, raise, check)."""

    sequence: int
    player: str
    is_hero: bool
    street: str  # PREFLOP / FLOP / TURN / RIVER
    action_type: str  # POST_BLIND / POST_ANTE / FOLD / CHECK / CALL / BET / RAISE
    amount: Decimal  # total bet/raise size on street; 0 for FOLD/CHECK
    amount_to_call: Decimal  # facing bet size; 0 for BET/CHECK/FOLD/POST_*
    pot_before: Decimal  # running pot before this action
    is_all_in: bool = False
    spr: Decimal | None = None  # set only on first hero FLOP action
    mdf: Decimal | None = None  # set only when is_hero and amount_to_call > 0


@dataclass
class ParsedHand:
    """Container returned by HandParser.parse()."""

    session: SessionData
    hand: HandData
    players: list[HandPlayerData] = field(default_factory=list)
    actions: list[ActionData] = field(default_factory=list)
