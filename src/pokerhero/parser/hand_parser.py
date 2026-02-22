"""PokerStars hand history parser."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from pokerhero.parser.models import (
    ActionData,
    HandData,
    HandPlayerData,
    ParsedHand,
    SessionData,
)

# ---------------------------------------------------------------------------
# Internal TypedDicts — private to this module
# ---------------------------------------------------------------------------


class _SeatInfo(TypedDict):
    seat: int
    starting_stack: Decimal
    hole_cards: str | None
    sitting_out: bool


class _HandMeta(TypedDict):
    hand_id: str
    timestamp: datetime
    button_seat: int
    uncalled_bet: Decimal


class _RawAction(TypedDict):
    seq: int
    player: str
    street: str
    action_type: str
    amount: Decimal
    amount_to_call: Decimal
    pot_before: Decimal
    is_all_in: bool


class _SummaryData(TypedDict):
    total_pot: Decimal
    rake: Decimal
    board_flop: str | None
    board_turn: str | None
    board_river: str | None
    collected: dict[str, Decimal]
    shown_cards: dict[str, str]


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_RE_CASH_HEADER = re.compile(
    r"PokerStars Hand #(\d+):\s+Hold'em No Limit"
    r" \([€$]?([\d.]+)/[€$]?([\d.]+)(?:\s+[A-Z]+)?\)"
    r" - (\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"
)
_RE_TOURN_HEADER = re.compile(
    r"PokerStars Hand #(\d+): Tournament #(\d+), [\d+]+ Hold'em No Limit"
    r" - (Level [IVX]+) \((\d+)/(\d+)\)"
    r" - (\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"
)
_RE_TABLE = re.compile(r"Table '(.+?)' (\d+)-max.*Seat #(\d+) is the button")
_RE_SEAT = re.compile(r"Seat (\d+): (.+?) \(([\d.]+) in chips\)(.*)")
_RE_POST_BLIND = re.compile(
    r"^(.+?): posts (?:small blind|big blind|small & big blinds) ([\d.]+)"
)
_RE_POST_ANTE = re.compile(r"^(.+?): posts the ante ([\d.]+)")
_RE_DEALT = re.compile(r"Dealt to (.+?) \[(.+?)\]")
_RE_ACTION = re.compile(
    r"^(.+?): (folds|checks|calls|bets|raises)"
    r"(?: ([\d.]+))?(?: to ([\d.]+))?(?: and is all-in)?"
)
_RE_ALLIN = re.compile(r"and is all-in")
_RE_UNCALLED = re.compile(r"Uncalled bet \(([\d.]+)\) returned to (.+)")
_RE_COLLECTED = re.compile(r"^(.+?) collected ([\d.]+) from (?:pot|main pot|side pot)")
_RE_SUMMARY_POT = re.compile(r"Total pot ([\d.]+).*\| Rake ([\d.]+)")
_RE_BOARD = re.compile(r"Board \[(.+?)\]")
_RE_SUMMARY_SEAT = re.compile(
    r"Seat \d+: (.+?) (?:showed \[(.+?)\] and (won|lost)"
    r"|mucked \[(.+?)\]|collected \(([\d.]+)\)|(folded|didn't))"
)
_RE_SUMMARY_WON = re.compile(r"showed \[.+?\] and won \(([\d.]+)\)")
_RE_SUMMARY_COLLECTED = re.compile(r"collected \(([\d.]+)\)")
_RE_MUCKS_SHOWDOWN = re.compile(r"^(.+?): mucks hand")
_RE_SHOWS_SHOWDOWN = re.compile(r"^(.+?): shows \[(.+?)\]")
_RE_MUCKED_SUMMARY = re.compile(r"mucked \[(.+?)\]")
_RE_TIMESTAMP = re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})")

# Lines that should be silently ignored (produce no action)
_NOISE_PATTERNS = [
    re.compile(p)
    for p in [
        r"^.+ is disconnected",
        r"^.+ has timed out(?: while disconnected)?$",
        r"^.+ leaves the table",
        r"^.+ joins the table at seat #\d+",
        r"^.+ will be allowed to play after the button",
        r"^.+ out of hand \(",
        r"^.+: doesn't show hand",
        r"^\*\*\*",
    ]
]

_STREET_MARKERS = {
    "*** HOLE CARDS ***": "PREFLOP",
    "*** FLOP ***": "FLOP",
    "*** TURN ***": "TURN",
    "*** RIVER ***": "RIVER",
    "*** SHOW DOWN ***": "SHOWDOWN",
    "*** SUMMARY ***": "SUMMARY",
}


def _is_noise(line: str) -> bool:
    return any(p.match(line) for p in _NOISE_PATTERNS)


def _parse_timestamp(ts_str: str) -> datetime:
    return datetime.strptime(ts_str, "%Y/%m/%d %H:%M:%S")


def _positions_for_seats(seat_order: list[int], btn_seat: int) -> dict[int, str]:
    """Assign position labels clockwise from BTN for the given seat list."""
    n = len(seat_order)
    if n == 0:
        return {}

    btn_idx = seat_order.index(btn_seat) if btn_seat in seat_order else 0
    # Rotate so BTN is first
    rotated = seat_order[btn_idx:] + seat_order[:btn_idx]

    labels_by_count = {
        2: ["BTN", "BB"],
        3: ["BTN", "SB", "BB"],
        4: ["BTN", "SB", "BB", "UTG"],
        5: ["BTN", "SB", "BB", "UTG", "CO"],
        6: ["BTN", "SB", "BB", "UTG", "MP", "CO"],
        7: ["BTN", "SB", "BB", "UTG", "MP", "MP+1", "CO"],
        8: ["BTN", "SB", "BB", "UTG", "UTG+1", "MP", "MP+1", "CO"],
        9: ["BTN", "SB", "BB", "UTG", "UTG+1", "MP", "MP+1", "CO", "HJ"],
    }
    labels = labels_by_count.get(n, [f"P{i}" for i in range(n)])
    return {seat: labels[i] for i, seat in enumerate(rotated)}


class HandParser:
    """Parse a single PokerStars hand history text block."""

    def __init__(self, hero_username: str) -> None:
        self.hero = hero_username

    def parse(self, text: str) -> ParsedHand:
        lines = [ln.rstrip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]  # drop blank lines

        session, hand_meta = self._parse_headers(lines)
        seats = self._parse_seats(lines)
        (
            actions_raw,
            showdown_cards,
            showdown_players,
            total_committed,
            uncalled_bet_total,
        ) = self._parse_body(lines, session, seats)
        summary = self._parse_summary(lines)

        # Merge showdown cards into seats
        for username, cards in showdown_cards.items():
            if username in seats and seats[username]["hole_cards"] is None:
                seats[username]["hole_cards"] = cards

        players = self._build_players(
            seats, session, hand_meta, summary, showdown_players, total_committed
        )
        actions = self._build_actions(actions_raw, players)

        hand = HandData(
            hand_id=hand_meta["hand_id"],
            timestamp=hand_meta["timestamp"],
            button_seat=hand_meta["button_seat"],
            board_flop=summary.get("board_flop"),
            board_turn=summary.get("board_turn"),
            board_river=summary.get("board_river"),
            total_pot=summary["total_pot"],
            rake=summary["rake"],
            uncalled_bet_returned=uncalled_bet_total,
        )

        return ParsedHand(session=session, hand=hand, players=players, actions=actions)

    # ------------------------------------------------------------------
    # Header parsing
    # ------------------------------------------------------------------

    def _parse_headers(self, lines: list[str]) -> tuple[SessionData, _HandMeta]:
        hand_line = lines[0]
        table_line = lines[1]

        # Tournament?
        m_tourn = _RE_TOURN_HEADER.search(hand_line)
        if m_tourn:
            hand_id = m_tourn.group(1)
            tourn_id = m_tourn.group(2)
            level = m_tourn.group(3)
            sb = Decimal(m_tourn.group(4))
            bb = Decimal(m_tourn.group(5))
            ts = _parse_timestamp(m_tourn.group(6))
            is_tournament = True
            tournament_id = tourn_id
            tournament_level = level
        else:
            m_cash = _RE_CASH_HEADER.search(hand_line)
            if not m_cash:
                raise ValueError(f"Cannot parse hand header: {hand_line!r}")
            hand_id = m_cash.group(1)
            sb = Decimal(m_cash.group(2))
            bb = Decimal(m_cash.group(3))
            ts = _parse_timestamp(m_cash.group(4))
            is_tournament = False
            tournament_id = None
            tournament_level = None

        m_table = _RE_TABLE.search(table_line)
        if not m_table:
            raise ValueError(f"Cannot parse table line: {table_line!r}")
        table_name = m_table.group(1)
        max_seats = int(m_table.group(2))
        button_seat = int(m_table.group(3))

        session = SessionData(
            table_name=table_name,
            game_type="NLHE",
            limit_type="NL",
            small_blind=sb,
            big_blind=bb,
            ante=Decimal("0"),  # updated later from ante posts
            max_seats=max_seats,
            is_tournament=is_tournament,
            tournament_id=tournament_id,
            tournament_level=tournament_level,
        )

        hand_meta: _HandMeta = {
            "hand_id": hand_id,
            "timestamp": ts,
            "button_seat": button_seat,
            "uncalled_bet": Decimal("0"),
        }
        return session, hand_meta

    # ------------------------------------------------------------------
    # Seat parsing
    # ------------------------------------------------------------------

    def _parse_seats(self, lines: list[str]) -> dict[str, _SeatInfo]:
        """Return {username: {seat, starting_stack, hole_cards, sitting_out}}."""
        seats: dict[str, _SeatInfo] = {}
        for line in lines:
            m = _RE_SEAT.match(line)
            if m:
                seat_num = int(m.group(1))
                username = m.group(2).strip()
                stack = Decimal(m.group(3))
                flags = m.group(4)
                sitting_out = "sitting out" in flags or "out of hand" in flags
                seats[username] = {
                    "seat": seat_num,
                    "starting_stack": stack,
                    "hole_cards": None,
                    "sitting_out": sitting_out,
                }
        return seats

    # ------------------------------------------------------------------
    # Body parsing
    # ------------------------------------------------------------------

    def _parse_body(
        self,
        lines: list[str],
        session: SessionData,
        seats: dict[str, _SeatInfo],
    ) -> tuple[list[_RawAction], dict[str, str], set[str], dict[str, Decimal], Decimal]:
        """
        Walk the hand body and collect:
        - actions_raw: list of raw action dicts
        - showdown_cards: {username: cards_str} for cards revealed at showdown
        - showdown_players: set of usernames that reached showdown
        - total_committed: {username: total chips invested}
        - uncalled_bet_total: total uncalled bet returned
        """
        actions_raw: list[_RawAction] = []
        showdown_cards: dict[str, str] = {}
        showdown_players: set[str] = set()

        current_street = "PREFLOP"
        seq = 0
        pot = Decimal("0")
        # Track per-street facing bet (for amount_to_call)
        street_bet: Decimal = Decimal("0")
        # Track each player's total committed this street (for is_all_in detection)
        street_committed: dict[str, Decimal] = {}
        # Track each player's total stack committed across all streets
        total_committed: dict[str, Decimal] = {}
        # Track uncalled bets returned
        uncalled_bet_total: Decimal = Decimal("0")
        # Track whether current street has an all-in bet/raise pending
        facing_allin: bool = False

        # Natural SB/BB posters (first two blind posts)
        blind_posters: list[str] = []
        ante_amount: Decimal = Decimal("0")

        in_summary = False

        for line in lines[2:]:  # skip hand + table header lines
            stripped = line.strip()

            # --- Street transitions ---
            for marker, street in _STREET_MARKERS.items():
                if stripped.startswith(marker):
                    if street == "SUMMARY":
                        in_summary = True
                    elif street != current_street:
                        current_street = street
                        street_bet = Decimal("0")
                        street_committed = {}
                        facing_allin = False
                    break

            if in_summary:
                continue

            if _is_noise(stripped):
                continue

            # --- Dealt to hero ---
            m_dealt = _RE_DEALT.match(stripped)
            if m_dealt:
                username = m_dealt.group(1)
                if username in seats:
                    seats[username]["hole_cards"] = m_dealt.group(2)
                continue

            # --- Uncalled bet ---
            m_unc = _RE_UNCALLED.match(stripped)
            if m_unc:
                unc_amount = Decimal(m_unc.group(1))
                unc_player = m_unc.group(2).strip()
                pot -= unc_amount
                uncalled_bet_total += unc_amount
                total_committed[unc_player] = (
                    total_committed.get(unc_player, Decimal("0")) - unc_amount
                )
                continue

            # --- Collected (non-summary) ---
            m_coll = _RE_COLLECTED.match(stripped)
            if m_coll:
                continue  # ignore mid-hand collected lines

            # --- Showdown ---
            m_shows = _RE_SHOWS_SHOWDOWN.match(stripped)
            if m_shows:
                username = m_shows.group(1).strip()
                showdown_players.add(username)
                showdown_cards[username] = m_shows.group(2)
                continue

            m_mucks = _RE_MUCKS_SHOWDOWN.match(stripped)
            if m_mucks:
                showdown_players.add(m_mucks.group(1).strip())
                continue

            # --- Ante posts ---
            m_ante = _RE_POST_ANTE.match(stripped)
            if m_ante:
                username = m_ante.group(1).strip()
                amount = Decimal(m_ante.group(2))
                if ante_amount == Decimal("0"):
                    ante_amount = amount
                    session.ante = amount
                seq += 1
                pot += amount
                total_committed[username] = (
                    total_committed.get(username, Decimal("0")) + amount
                )
                actions_raw.append(
                    {
                        "seq": seq,
                        "player": username,
                        "street": "PREFLOP",
                        "action_type": "POST_ANTE",
                        "amount": amount,
                        "amount_to_call": Decimal("0"),
                        "pot_before": pot - amount,
                        "is_all_in": False,
                    }
                )
                continue

            # --- Blind posts ---
            m_blind = _RE_POST_BLIND.match(stripped)
            if m_blind:
                username = m_blind.group(1).strip()
                amount = Decimal(m_blind.group(2))
                if len(blind_posters) < 2:
                    blind_posters.append(username)
                seq += 1
                pot += amount
                total_committed[username] = (
                    total_committed.get(username, Decimal("0")) + amount
                )
                street_committed[username] = (
                    street_committed.get(username, Decimal("0")) + amount
                )
                # Update street_bet (BB sets the facing bet)
                if amount > street_bet:
                    street_bet = amount
                actions_raw.append(
                    {
                        "seq": seq,
                        "player": username,
                        "street": "PREFLOP",
                        "action_type": "POST_BLIND",
                        "amount": amount,
                        "amount_to_call": Decimal("0"),
                        "pot_before": pot - amount,
                        "is_all_in": False,
                    }
                )
                continue

            # --- Regular actions ---
            m_act = _RE_ACTION.match(stripped)
            if not m_act:
                continue

            username = m_act.group(1).strip()
            verb = m_act.group(2)
            num1 = Decimal(m_act.group(3)) if m_act.group(3) else None
            num2 = Decimal(m_act.group(4)) if m_act.group(4) else None
            is_all_in = bool(_RE_ALLIN.search(stripped))

            # If calling into an all-in bet/raise, mark as all-in too
            if verb == "calls" and facing_allin:
                is_all_in = True

            # Compute action type and amount
            if verb == "folds":
                action_type = "FOLD"
                amount = Decimal("0")
                atc = Decimal("0")
            elif verb == "checks":
                action_type = "CHECK"
                amount = Decimal("0")
                atc = Decimal("0")
            elif verb == "calls":
                action_type = "CALL"
                amount = num1 if num1 is not None else Decimal("0")
                atc = street_bet - street_committed.get(username, Decimal("0"))
                if atc < Decimal("0"):
                    atc = Decimal("0")
                pot += amount
                total_committed[username] = (
                    total_committed.get(username, Decimal("0")) + amount
                )
                street_committed[username] = (
                    street_committed.get(username, Decimal("0")) + amount
                )
            elif verb == "bets":
                action_type = "BET"
                amount = num1 if num1 is not None else Decimal("0")
                atc = Decimal("0")
                street_bet = amount
                pot += amount
                total_committed[username] = (
                    total_committed.get(username, Decimal("0")) + amount
                )
                street_committed[username] = (
                    street_committed.get(username, Decimal("0")) + amount
                )
            elif verb == "raises":
                action_type = "RAISE"
                # "raises X to Y" → amount=Y (total size)
                amount = (
                    num2
                    if num2 is not None
                    else (num1 if num1 is not None else Decimal("0"))
                )
                atc = street_bet - street_committed.get(username, Decimal("0"))
                if atc < Decimal("0"):
                    atc = Decimal("0")
                incremental = amount - street_committed.get(username, Decimal("0"))
                if incremental < Decimal("0"):
                    incremental = Decimal("0")
                pot += incremental
                total_committed[username] = (
                    total_committed.get(username, Decimal("0")) + incremental
                )
                street_committed[username] = amount
                street_bet = amount
            else:
                continue

            # Track if current bet/raise is all-in (affects subsequent callers)
            if is_all_in and action_type in ("BET", "RAISE"):
                facing_allin = True

            if verb == "calls":
                pot_before = pot - amount
            elif verb == "raises":
                pot_before = pot - incremental
            elif verb == "bets":
                pot_before = pot - amount
            else:
                pot_before = pot

            seq += 1
            actions_raw.append(
                {
                    "seq": seq,
                    "player": username,
                    "street": current_street,
                    "action_type": action_type,
                    "amount": amount,
                    "amount_to_call": atc,
                    "pot_before": pot_before,
                    "is_all_in": is_all_in,
                }
            )

        return (
            actions_raw,
            showdown_cards,
            showdown_players,
            total_committed,
            uncalled_bet_total,
        )

    # ------------------------------------------------------------------
    # Summary parsing
    # ------------------------------------------------------------------

    def _parse_summary(self, lines: list[str]) -> _SummaryData:
        result: _SummaryData = {
            "total_pot": Decimal("0"),
            "rake": Decimal("0"),
            "board_flop": None,
            "board_turn": None,
            "board_river": None,
            "collected": {},  # {username: total_won}
            "shown_cards": {},  # {username: cards}
        }

        in_summary = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("*** SUMMARY ***"):
                in_summary = True
                continue
            if not in_summary:
                continue

            m_pot = _RE_SUMMARY_POT.search(stripped)
            if m_pot:
                result["total_pot"] = Decimal(m_pot.group(1))
                result["rake"] = Decimal(m_pot.group(2))
                continue

            m_board = _RE_BOARD.search(stripped)
            if m_board:
                cards = m_board.group(1).split()
                if len(cards) >= 3:
                    result["board_flop"] = " ".join(cards[:3])
                if len(cards) >= 4:
                    result["board_turn"] = cards[3]
                if len(cards) >= 5:
                    result["board_river"] = cards[4]
                continue

            # Seat lines: parse winnings and shown cards
            if stripped.startswith("Seat "):
                # won via showed + won
                m_won = _RE_SUMMARY_WON.search(stripped)
                if m_won:
                    # extract username (between "Seat N: " and " showed")
                    after_seat = re.sub(r"^Seat \d+: ", "", stripped)
                    # username is everything before " showed"
                    uname = after_seat.split(" showed ")[0].strip()
                    # strip position tags like "(button)", "(small blind)"
                    uname = re.sub(r"\s*\([^)]+\)\s*$", "", uname).strip()
                    result["collected"][uname] = result["collected"].get(
                        uname, Decimal("0")
                    ) + Decimal(m_won.group(1))
                    # cards shown
                    m_cards = re.search(r"showed \[(.+?)\]", stripped)
                    if m_cards:
                        result["shown_cards"][uname] = m_cards.group(1)
                    continue

                # won via collected (X)
                m_coll = _RE_SUMMARY_COLLECTED.search(stripped)
                if m_coll:
                    after_seat = re.sub(r"^Seat \d+: ", "", stripped)
                    uname = after_seat.split(" collected")[0].strip()
                    uname = re.sub(r"\s*\([^)]+\)\s*$", "", uname).strip()
                    result["collected"][uname] = result["collected"].get(
                        uname, Decimal("0")
                    ) + Decimal(m_coll.group(1))
                    continue

                # mucked cards
                m_mucked = _RE_MUCKED_SUMMARY.search(stripped)
                if m_mucked:
                    after_seat = re.sub(r"^Seat \d+: ", "", stripped)
                    uname = after_seat.split(" mucked")[0].strip()
                    uname = re.sub(r"\s*\([^)]+\)\s*$", "", uname).strip()
                    result["shown_cards"][uname] = m_mucked.group(1)

        return result

    # ------------------------------------------------------------------
    # Build player records
    # ------------------------------------------------------------------

    def _build_players(
        self,
        seats: dict[str, _SeatInfo],
        session: SessionData,
        hand_meta: _HandMeta,
        summary: _SummaryData,
        showdown_players: set[str],
        total_committed: dict[str, Decimal],
    ) -> list[HandPlayerData]:
        # Active seats (have a seat number)
        seat_numbers = [info["seat"] for info in seats.values()]
        seat_numbers.sort()

        # Find button seat
        btn_seat = hand_meta["button_seat"]

        # Position assignment using active seat numbers
        positions = _positions_for_seats(seat_numbers, btn_seat)

        players = []
        for username, info in seats.items():
            seat = info["seat"]
            position = positions.get(seat, "?")
            won = summary["collected"].get(username, Decimal("0"))
            invested = total_committed.get(username, Decimal("0"))
            net_result = won - invested
            hole_cards = info["hole_cards"]
            if hole_cards is None:
                hole_cards = summary["shown_cards"].get(username)

            players.append(
                HandPlayerData(
                    username=username,
                    seat=seat,
                    starting_stack=info["starting_stack"],
                    position=position,
                    hole_cards=hole_cards,
                    net_result=net_result,
                    vpip=False,  # computed in _build_actions
                    pfr=False,
                    went_to_showdown=username in showdown_players,
                    is_hero=username == self.hero,
                )
            )

        return players

    # ------------------------------------------------------------------
    # Build action records + derive VPIP/PFR/net_result/SPR/MDF
    # ------------------------------------------------------------------

    def _build_actions(
        self,
        actions_raw: list[_RawAction],
        players: list[HandPlayerData],
    ) -> list[ActionData]:
        # net_result is already correctly set in _build_players via total_committed.
        # This method only needs to build ActionData, compute SPR/MDF, and set VPIP/PFR.

        # VPIP / PFR
        vpip_set: set[str] = set()
        pfr_set: set[str] = set()

        # Find natural BB (second blind poster)
        natural_blind_posters: list[str] = []
        for raw in actions_raw:
            if raw["action_type"] == "POST_BLIND" and raw["street"] == "PREFLOP":
                if raw["player"] not in natural_blind_posters:
                    natural_blind_posters.append(raw["player"])
        natural_bb = (
            natural_blind_posters[1] if len(natural_blind_posters) >= 2 else None
        )

        for raw in actions_raw:
            if raw["street"] != "PREFLOP":
                continue
            atype = raw["action_type"]
            username = raw["player"]
            if atype == "CALL":
                vpip_set.add(username)
            elif atype == "RAISE":
                vpip_set.add(username)
                pfr_set.add(username)
            elif atype == "CHECK" and username == natural_bb:
                pass  # BB checks — not VPIP

        # SPR / MDF tracking
        hero_first_flop_done = False
        stacks_at_flop: dict[str, Decimal] = {}

        # Compute stacks at flop start: starting_stack - invested_preflop.
        # Track street_committed_pf to correctly compute incremental cost for raises.
        preflop_invested: dict[str, Decimal] = {}
        preflop_folders: set[str] = set()
        street_committed_pf: dict[str, Decimal] = {}
        for raw in actions_raw:
            if raw["street"] != "PREFLOP":
                break
            atype = raw["action_type"]
            username = raw["player"]
            amount = raw["amount"]
            if atype == "FOLD":
                preflop_folders.add(username)
            elif atype in ("POST_BLIND", "POST_ANTE", "CALL", "BET"):
                preflop_invested[username] = (
                    preflop_invested.get(username, Decimal("0")) + amount
                )
                street_committed_pf[username] = (
                    street_committed_pf.get(username, Decimal("0")) + amount
                )
            elif atype == "RAISE":
                # amount = total raise; incremental = amount - already committed
                prior = street_committed_pf.get(username, Decimal("0"))
                inc = amount - prior
                preflop_invested[username] = (
                    preflop_invested.get(username, Decimal("0")) + inc
                )
                street_committed_pf[username] = amount

        for p in players:
            stacks_at_flop[p.username] = p.starting_stack - preflop_invested.get(
                p.username, Decimal("0")
            )

        # Build ActionData list
        result: list[ActionData] = []
        for raw in actions_raw:
            username = raw["player"]
            is_hero = username == self.hero
            atype = raw["action_type"]
            street = raw["street"]
            amount = raw["amount"]
            atc = raw["amount_to_call"]
            pot_before = raw["pot_before"]
            is_all_in = raw["is_all_in"]

            # SPR: only on first hero FLOP action
            spr: Decimal | None = None
            if is_hero and street == "FLOP" and not hero_first_flop_done:
                hero_first_flop_done = True
                hero_stack = stacks_at_flop.get(self.hero, Decimal("0"))
                # Effective stack = min of hero and active villain stacks
                active_stacks = [
                    stacks_at_flop[u]
                    for u in stacks_at_flop
                    if u != self.hero
                    and stacks_at_flop[u] > Decimal("0")
                    and u not in preflop_folders
                ]
                if active_stacks and pot_before > Decimal("0"):
                    effective = min(hero_stack, min(active_stacks))
                    spr = effective / pot_before

            # MDF: only when hero faces a bet
            mdf: Decimal | None = None
            if is_hero and atc > Decimal("0"):
                mdf = pot_before / (pot_before + atc)

            result.append(
                ActionData(
                    sequence=raw["seq"],
                    player=username,
                    is_hero=is_hero,
                    street=street,
                    action_type=atype,
                    amount=amount,
                    amount_to_call=atc,
                    pot_before=pot_before,
                    is_all_in=is_all_in,
                    spr=spr,
                    mdf=mdf,
                )
            )

        # Apply VPIP/PFR to players
        for p in players:
            p.vpip = p.username in vpip_set
            p.pfr = p.username in pfr_set

        return result
