"""Sessions page — breadcrumb drill-down: Sessions → Hands → Actions."""

from __future__ import annotations

import json
import math
from typing import Any, NotRequired, TypedDict
from urllib.parse import parse_qs, urlparse

import dash
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html

from pokerhero.database.db import get_connection, get_setting, upsert_player

dash.register_page(__name__, path="/sessions", name="Review Sessions")  # type: ignore[no-untyped-call]


class _DrillDownState(TypedDict, total=False):
    level: str  # always present; "sessions" | "hands" | "actions"
    session_id: NotRequired[int]
    hand_id: NotRequired[int]
    session_label: NotRequired[str]


# ---------------------------------------------------------------------------
# Shared styles
# ---------------------------------------------------------------------------
_TH = {
    "background": "#0074D9",
    "color": "#fff",
    "padding": "10px 12px",
    "textAlign": "left",
    "fontWeight": "600",
    "fontSize": "13px",
}
_TD = {
    "padding": "9px 12px",
    "borderBottom": "1px solid #eee",
    "fontSize": "13px",
    "cursor": "pointer",
}
_STREET_COLOURS = {
    "PREFLOP": "#6c757d",
    "FLOP": "#0074D9",
    "TURN": "#2ECC40",
    "RIVER": "#FF4136",
}
_SUIT_SYMBOLS: dict[str, str] = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}
_SUIT_COLORS: dict[str, str] = {
    "s": "#111111",
    "h": "#cc0000",
    "d": "#cc0000",
    "c": "#111111",
}


def _action_row_style(is_hero: bool) -> dict[str, str]:
    """Return the tr style for an action row.

    Hero rows get a light-blue background and a left-border accent so they
    stand out at a glance in the action table.

    Args:
        is_hero: True when the row belongs to the hero player.

    Returns:
        A style dict to pass to html.Tr(style=...).
    """
    if is_hero:
        return {
            "backgroundColor": "#edf5ff",
            "borderLeft": "3px solid #0074D9",
        }
    return {}


def _render_card(card: str) -> html.Span:
    """Render a single PokerStars card code as a styled card element.

    Args:
        card: Card string in PokerStars format, e.g. 'As', 'Kh', 'Td'.

    Returns:
        A styled html.Span resembling a playing card face.
    """
    if not card or len(card) < 2:
        return html.Span()
    rank = card[:-1]
    suit_char = card[-1].lower()
    suit_sym = _SUIT_SYMBOLS.get(suit_char, suit_char)
    color = _SUIT_COLORS.get(suit_char, "#111111")
    return html.Span(
        f"{rank}{suit_sym}",
        style={
            "display": "inline-block",
            "background": "#fff",
            "border": "1px solid #bbb",
            "borderRadius": "4px",
            "padding": "2px 7px",
            "fontWeight": "700",
            "fontSize": "14px",
            "color": color,
            "fontFamily": "monospace",
            "boxShadow": "1px 1px 2px rgba(0,0,0,0.15)",
            "marginRight": "3px",
            "lineHeight": "1.5",
        },
    )


def _render_cards(cards_str: str | None) -> html.Span:
    """Render a space-separated card string as inline card elements.

    Args:
        cards_str: Space-separated card codes, e.g. 'As Kd' or 'Ah Kh Qh'.
                   None or empty string returns an em-dash placeholder.

    Returns:
        An html.Span containing one _render_card element per card,
        or an em-dash span when the input is absent.
    """
    if not cards_str:
        return html.Span("—")
    cards = [c.strip() for c in str(cards_str).split() if c.strip()]
    if not cards:
        return html.Span("—")
    return html.Span([_render_card(c) for c in cards])


def _format_cards_text(cards_str: str | None) -> str:
    """Format a space-separated card string as plain text with suit symbols.

    Args:
        cards_str: Space-separated card codes, e.g. 'As Kh'. None or empty
                   string returns an em-dash placeholder.

    Returns:
        Formatted string like 'A♠ K♥', or '—' when input is absent.
    """
    if not cards_str:
        return "—"
    parts = []
    for card in str(cards_str).split():
        if len(card) >= 2:
            rank = card[:-1]
            suit = _SUIT_SYMBOLS.get(card[-1].lower(), card[-1])
            parts.append(f"{rank}{suit}")
    return " ".join(parts) if parts else "—"


def _build_showdown_section(
    villain_rows: list[dict[str, Any]],
    hero_name: str | None = None,
    hero_cards: str | None = None,
    board: str = "",
    opp_stats: dict[str, dict[str, int]] | None = None,
    min_hands: int = 15,
    hero_net_result: float | None = None,
) -> html.Div | None:
    """Build a Showdown section showing all players' cards, hand descriptions,
    and a trophy badge on the winner(s).

    Args:
        villain_rows: List of dicts with keys 'username', 'position',
            'hole_cards', and optional 'net_result' (float).
        hero_name: Display name for the hero (e.g. "Hero"). If None, hero is
            not included in the section.
        hero_cards: Hero's hole cards string (e.g. "As Kd"). Required for hero
            to appear and for hand evaluation.
        board: Space-separated board cards (e.g. "Ah Kh Qs 2c 7d"). Used to
            evaluate hand descriptions and determine the winner. If empty or
            fewer than 3 cards, descriptions and winner detection are skipped.
        opp_stats: Optional mapping of username → stats dict with keys
            'hands_played', 'vpip_count', 'pfr_count'. When provided, an
            archetype badge (TAG/LAG/Nit/Fish) is shown next to each villain.
        min_hands: Minimum hands required before an archetype badge is shown.
        hero_net_result: Hero's net result for this hand (positive = won,
            negative = lost). Displayed in green/red at the end of hero's row.

    Returns:
        An html.Div or None when there are no players to display.
    """
    import itertools as _itr
    import re as _re

    from pokerkit import Card as _Card
    from pokerkit import StandardHighHand as _SHH

    if not villain_rows:
        return None

    # Build the full list of players at showdown: hero first, then villains.
    # Keep track of label → username (archetype) and label → net_result.
    players: list[tuple[str, str]] = []  # (display_label, hole_cards)
    label_to_username: dict[str, str] = {}
    label_to_result: dict[str, float] = {}
    if hero_name and hero_cards:
        players.append((hero_name, hero_cards))
        if hero_net_result is not None:
            label_to_result[hero_name] = hero_net_result
    for v in villain_rows:
        label = v["username"]
        if v.get("position"):
            label += f" ({v['position']})"
        players.append((label, v["hole_cards"]))
        label_to_username[label] = v["username"]
        raw_result = v.get("net_result")
        if raw_result is not None:
            label_to_result[label] = float(raw_result)

    # Evaluate best hands and find winner(s) when board has ≥3 cards.
    board_card_list = [c for c in board.split() if c]
    descriptions: dict[str, str | None] = {}
    winner_labels: set[str] = set()
    if len(board_card_list) >= 3:
        best_hands: dict[str, object] = {}
        for label, hole in players:
            try:
                all_cards = list(_Card.parse(hole.replace(" ", ""))) + list(
                    _Card.parse("".join(board_card_list))
                )
                best = max(
                    _SHH(list(combo)) for combo in _itr.combinations(all_cards, 5)
                )
                best_hands[label] = best
                descriptions[label] = _re.sub(r"\s*\(.*\)", "", str(best))
            except Exception:
                best_hands[label] = None
                descriptions[label] = None

        valid = {lb: h for lb, h in best_hands.items() if h is not None}
        if valid:
            top = max(valid.values())  # type: ignore[type-var]
            winner_labels = {lb for lb, h in valid.items() if h == top}

    # Render one row per player.
    rows: list[html.Div] = []
    for label, hole in players:
        desc = descriptions.get(label)
        trophy = "🏆 " if label in winner_labels else ""

        # Archetype badge — only for villains (not hero), when opp_stats given.
        archetype_badge: list[Any] = []
        username = label_to_username.get(label)
        if opp_stats and username and username in opp_stats:
            from pokerhero.analysis.stats import classify_player

            s = opp_stats[username]
            h = int(s["hands_played"])
            vp = int(s["vpip_count"]) / h * 100 if h > 0 else 0.0
            pf = int(s["pfr_count"]) / h * 100 if h > 0 else 0.0
            archetype = classify_player(vp, pf, h, min_hands=min_hands)
            if archetype is not None:
                archetype_badge = [
                    html.Span(
                        archetype,
                        style={
                            "background": _ARCHETYPE_COLORS.get(archetype, "#999"),
                            "color": "#fff",
                            "borderRadius": "4px",
                            "padding": "1px 6px",
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "marginLeft": "5px",
                            "verticalAlign": "middle",
                        },
                    )
                ]

        rows.append(
            html.Div(
                [
                    html.Span(
                        f"{trophy}{label}: ",
                        style={
                            "fontWeight": "600",
                            "fontSize": "13px",
                            "marginRight": "6px",
                            "color": "#f5a623" if trophy else "#555",
                        },
                    ),
                    *archetype_badge,
                    _render_cards(hole),
                    *(
                        [
                            html.Span(
                                f"  — {desc}",
                                style={
                                    "fontSize": "12px",
                                    "color": "#888",
                                    "marginLeft": "6px",
                                },
                            )
                        ]
                        if desc
                        else []
                    ),
                    *(
                        [
                            html.Span(
                                f"({_fmt_pnl(label_to_result[label])})",
                                style={
                                    "fontSize": "12px",
                                    "fontWeight": "600",
                                    "marginLeft": "8px",
                                    "color": (
                                        "#28a745"
                                        if label_to_result[label] >= 0
                                        else "#dc3545"
                                    ),
                                },
                            )
                        ]
                        if label in label_to_result
                        else []
                    ),
                ],
                style={"marginBottom": "4px"},
            )
        )

    return html.Div(
        [
            html.H5(
                "Showdown",
                style={
                    "color": "#a855f7",
                    "borderBottom": "2px solid #a855f7",
                    "paddingBottom": "4px",
                    "marginBottom": "8px",
                    "marginTop": "8px",
                },
            ),
            *rows,
        ]
    )


def _format_math_cell(
    spr: float | None,
    mdf: float | None,
    is_hero: bool,
    amount_to_call: float,
    pot_before: float,
) -> str:
    """Build the math/context cell text for an action row.

    Shows up to three values, separated by ' | ':
      SPR (prepended, flop-only)
      Pot odds (hero facing a bet)
      MDF (hero facing a bet)

    Args:
        spr: Stack-to-Pot Ratio, or None when not applicable.
        mdf: Minimum Defense Frequency as a decimal [0,1], or None when not applicable.
        is_hero: True when the action belongs to the hero player.
        amount_to_call: Total facing bet hero must match (0 for non-facing actions).
        pot_before: Pot size before the action.

    Returns:
        Formatted string of context values, or empty string when none apply.
    """
    parts: list[str] = []

    if is_hero and amount_to_call > 0:
        pot_odds = amount_to_call / (pot_before + amount_to_call) * 100
        parts.append(f"Pot odds: {pot_odds:.1f}%")
        if mdf is not None and not math.isnan(mdf):
            parts.append(f"MDF: {mdf * 100:.1f}%")

    result = "  |  ".join(parts)

    if spr is not None and not math.isnan(spr):
        spr_str = f"SPR: {spr:.2f}"
        result = f"{spr_str}  |  {result}" if result else spr_str

    return result


# ---------------------------------------------------------------------------
# Layout — all content lives inside drill-down-content
# ---------------------------------------------------------------------------
layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "1000px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H2("🔍 Review Sessions"),
        dcc.Link(
            "← Back to Home",
            href="/",
            style={"fontSize": "13px", "color": "#0074D9"},
        ),
        html.Hr(),
        html.Div(id="breadcrumb", style={"marginBottom": "12px"}),
        html.Hr(style={"marginTop": "0"}),
        html.Div(id="session-analysis-hint", style={"marginBottom": "8px"}),
        dcc.Loading(html.Div(id="drill-down-content")),
        dcc.Store(id="drill-down-state", data={"level": "sessions"}),
        dcc.Store(id="pending-session-report"),
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_blind(v: object) -> str:
    """Format a blind/stake value: integer if whole, else strip trailing zeros."""
    f = float(v)  # type: ignore[arg-type]
    return f"{f:g}"


def _fmt_pnl(pnl: float) -> str:
    """Format a P&L value with leading sign; no trailing decimal zeros."""
    sign = "+" if pnl >= 0 else ""
    return f"{sign}{pnl:,.6g}"


def _describe_hand(hole_cards: str, board: str) -> str | None:
    """Return a human-readable best-hand description for hole cards + board.

    Finds the best 5-card hand from all combinations of hole cards and board
    cards using PokerKit's StandardHighHand evaluator. Returns the hand name
    (e.g. "Full house", "Flush") with the card list stripped.

    Args:
        hole_cards: Space-separated hole card strings, e.g. "As Kd".
        board: Space-separated board card strings, e.g. "Ah Kh Qs 2c 7d".
            Must contain at least 3 cards for a valid evaluation.

    Returns:
        Hand name string, or None if the board has fewer than 3 cards or
        evaluation fails.
    """
    import itertools
    import re

    from pokerkit import Card, StandardHighHand

    board_cards = [c for c in board.split() if c]
    if len(board_cards) < 3:
        return None
    try:
        all_cards = list(Card.parse(hole_cards.replace(" ", ""))) + list(
            Card.parse("".join(board_cards))
        )
        best = max(
            StandardHighHand(list(combo))
            for combo in itertools.combinations(all_cards, 5)
        )
        return re.sub(r"\s*\(.*\)", "", str(best))
    except Exception:
        return None


_ARCHETYPE_COLORS: dict[str | None, str] = {
    "TAG": "#2980b9",
    "LAG": "#e67e22",
    "Nit": "#7f8c8d",
    "Fish": "#27ae60",
}


def _build_opponent_profile_card(
    username: str,
    hands_played: int,
    vpip_count: int,
    pfr_count: int,
    min_hands: int = 15,
) -> html.Div:
    """Render a small profile card for one opponent.

    Shows username, VPIP%, PFR%, hands seen, and an archetype badge
    (TAG / LAG / Nit / Fish) when at least *min_hands* hands are observed.

    Args:
        username: Opponent's display name.
        hands_played: Total hands observed this session.
        vpip_count: Hands where opponent voluntarily put money in preflop.
        pfr_count: Hands where opponent raised preflop.
        min_hands: Minimum hands required before an archetype badge is shown.

    Returns:
        A ``html.Div`` profile card component.
    """
    from pokerhero.analysis.stats import classify_player

    vpip_pct = vpip_count / hands_played * 100 if hands_played > 0 else 0.0
    pfr_pct = pfr_count / hands_played * 100 if hands_played > 0 else 0.0
    archetype = classify_player(vpip_pct, pfr_pct, hands_played, min_hands=min_hands)

    badge: list[Any] = []
    if archetype is not None:
        badge = [
            html.Span(
                archetype,
                style={
                    "background": _ARCHETYPE_COLORS.get(archetype, "#999"),
                    "color": "#fff",
                    "borderRadius": "4px",
                    "padding": "2px 7px",
                    "fontSize": "12px",
                    "fontWeight": "700",
                    "marginLeft": "6px",
                },
            )
        ]

    return html.Div(
        [
            html.Div(
                [html.Strong(username, style={"fontSize": "14px"})] + badge,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "4px",
                },
            ),
            html.Div(
                (
                    f"VPIP: {vpip_pct:.0f}%  |  PFR: {pfr_pct:.0f}%"
                    f"  |  {hands_played} hands"
                ),
                style={"fontSize": "12px", "color": "#555"},
            ),
        ],
        style={
            "border": "1px solid #ddd",
            "borderRadius": "6px",
            "padding": "8px 12px",
            "minWidth": "160px",
            "background": "#fafafa",
        },
    )


def _build_villain_summary(
    opp_stats: dict[str, dict[str, int]],
    min_hands: int = 15,
) -> html.Div | None:
    """Render a compact header line listing all opponents with archetype badges.

    Placed below the board in the action view so the hero can see who they are
    up against before reading the action sequence.

    Args:
        opp_stats: Mapping of username → stats dict with keys
            'hands_played', 'vpip_count', 'pfr_count'.
        min_hands: Minimum hands required before an archetype badge is shown.

    Returns:
        An ``html.Div`` or ``None`` when *opp_stats* is empty.
    """
    if not opp_stats:
        return None

    from pokerhero.analysis.stats import classify_player

    items: list[Any] = [
        html.Span(
            "Villains: ",
            style={"fontWeight": "600", "fontSize": "13px", "color": "#555"},
        )
    ]
    for username, s in opp_stats.items():
        h = int(s["hands_played"])
        vp = int(s["vpip_count"]) / h * 100 if h > 0 else 0.0
        pf = int(s["pfr_count"]) / h * 100 if h > 0 else 0.0
        archetype = classify_player(vp, pf, h, min_hands=min_hands)
        badge: list[Any] = (
            [
                html.Span(
                    archetype,
                    style={
                        "background": _ARCHETYPE_COLORS.get(archetype, "#999"),
                        "color": "#fff",
                        "borderRadius": "4px",
                        "padding": "1px 6px",
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "marginLeft": "4px",
                        "verticalAlign": "middle",
                    },
                )
            ]
            if archetype is not None
            else []
        )
        items.append(
            html.Span(
                [html.Span(username, style={"fontSize": "13px"})] + badge,
                style={"marginRight": "12px"},
            )
        )

    return html.Div(
        items,
        style={
            "display": "flex",
            "alignItems": "center",
            "flexWrap": "wrap",
            "gap": "4px",
            "marginBottom": "10px",
            "fontSize": "13px",
        },
    )


def _get_db_path() -> str:
    result: str = dash.get_app().server.config.get("DB_PATH", ":memory:")  # type: ignore[no-untyped-call]
    return result


def _get_hero_player_id(db_path: str) -> int | None:
    if db_path == ":memory:":
        return None
    conn = get_connection(db_path)
    try:
        username = get_setting(conn, "hero_username", default="")
        return upsert_player(conn, username) if username else None
    finally:
        conn.close()


def _pnl_style(value: float) -> dict[str, str]:
    return {"color": "green" if value >= 0 else "red", "fontWeight": "600"}


def _fav_button_label(is_favorite: bool) -> str:
    """Return the star character for a favourite toggle button.

    Args:
        is_favorite: True when the item is currently marked as favourite.

    Returns:
        '★' when favourite, '☆' otherwise.
    """
    return "★" if is_favorite else "☆"


def _breadcrumb(
    level: str, session_label: str = "", hand_label: str = "", session_id: int = 0
) -> html.Div:
    sep = html.Span(" › ", style={"color": "#aaa", "margin": "0 6px"})
    btn_style = {
        "background": "none",
        "border": "none",
        "color": "#0074D9",
        "cursor": "pointer",
        "fontSize": "14px",
        "padding": "0",
    }
    plain_style = {"fontSize": "14px", "color": "#333", "fontWeight": "600"}

    if level == "sessions":
        return html.Div(html.Span("Sessions", style=plain_style))
    if level == "report":
        return html.Div(
            [
                html.Button(
                    "Sessions",
                    id={
                        "type": "breadcrumb-btn",
                        "level": "sessions",
                        "session_id": 0,
                    },
                    style=btn_style,
                    n_clicks=0,
                ),
                sep,
                html.Span(session_label or f"Session #{session_id}", style=plain_style),
            ]
        )
    if level == "hands":
        return html.Div(
            [
                html.Button(
                    "Sessions",
                    id={
                        "type": "breadcrumb-btn",
                        "level": "sessions",
                        "session_id": 0,
                    },
                    style=btn_style,
                    n_clicks=0,
                ),
                sep,
                html.Button(
                    session_label or f"Session #{session_id}",
                    id={
                        "type": "breadcrumb-btn",
                        "level": "report",
                        "session_id": session_id,
                    },
                    style=btn_style,
                    n_clicks=0,
                ),
                sep,
                html.Span("All Hands", style=plain_style),
            ]
        )
    # actions level
    return html.Div(
        [
            html.Button(
                "Sessions",
                id={
                    "type": "breadcrumb-btn",
                    "level": "sessions",
                    "session_id": 0,
                },
                style=btn_style,
                n_clicks=0,
            ),
            sep,
            html.Button(
                session_label or f"Session #{session_id}",
                id={
                    "type": "breadcrumb-btn",
                    "level": "report",
                    "session_id": session_id,
                },
                style=btn_style,
                n_clicks=0,
            ),
            sep,
            html.Span(hand_label, style=plain_style),
        ]
    )


# ---------------------------------------------------------------------------
# State updater — row/breadcrumb clicks funnel into drill-down-state
#
# Split into three callbacks with allow_duplicate=True so each only registers
# the inputs that exist in the current view (session-table and hand-table are
# never in the DOM at the same time).
# ---------------------------------------------------------------------------
def _compute_state_from_cell(
    session_cell: dict[str, Any] | None,
    hand_cell: dict[str, Any] | None,
    session_data: list[dict[str, Any]] | None,
    hand_data: list[dict[str, Any]] | None,
    current_state: _DrillDownState,
) -> _DrillDownState:
    """Pure helper: derive new drill-down state from a DataTable cell click.

    Args:
        session_cell: active_cell from session-table, or None.
        hand_cell: active_cell from hand-table, or None.
        session_data: derived_viewport_data for session-table, or None.
        hand_data: derived_viewport_data for hand-table, or None.
        current_state: current drill-down state (for session_id carry-through).

    Returns:
        New _DrillDownState navigating to 'hands' or 'actions'.

    Raises:
        dash.exceptions.PreventUpdate: when no cell was clicked.
    """
    if session_cell is not None and session_data:
        row = session_data[session_cell["row"]]
        return _DrillDownState(level="report", session_id=int(row["id"]))
    if hand_cell is not None and hand_data:
        row = hand_data[hand_cell["row"]]
        return _DrillDownState(
            level="actions",
            session_id=int(current_state.get("session_id") or 0),
            hand_id=int(row["id"]),
        )
    raise dash.exceptions.PreventUpdate


@callback(
    Output("drill-down-state", "data", allow_duplicate=True),
    Input("session-table", "active_cell"),
    State("session-table", "derived_viewport_data"),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _navigate_from_session_table(
    cell: dict[str, Any] | None,
    data: list[dict[str, Any]] | None,
    current_state: _DrillDownState,
) -> _DrillDownState:
    return _compute_state_from_cell(cell, None, data, None, current_state)


@callback(
    Output("drill-down-state", "data", allow_duplicate=True),
    Input("hand-table", "active_cell"),
    State("hand-table", "derived_viewport_data"),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _navigate_from_hand_table(
    cell: dict[str, Any] | None,
    data: list[dict[str, Any]] | None,
    current_state: _DrillDownState,
) -> _DrillDownState:
    return _compute_state_from_cell(None, cell, None, data, current_state)


@callback(
    Output("drill-down-state", "data"),
    Input(
        {"type": "breadcrumb-btn", "level": dash.ALL, "session_id": dash.ALL},
        "n_clicks",
    ),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _update_state(
    _breadcrumb_clicks: list[int | None],
    current_state: _DrillDownState,
) -> _DrillDownState:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    trigger = ctx.triggered[0]
    if not trigger.get("value"):
        raise dash.exceptions.PreventUpdate
    tid = trigger["prop_id"].split(".")[0]
    try:
        parsed = json.loads(tid)
    except (json.JSONDecodeError, ValueError):
        raise dash.exceptions.PreventUpdate
    if parsed.get("type") == "breadcrumb-btn":
        if parsed["level"] == "sessions":
            return _DrillDownState(level="sessions")
        if parsed["level"] == "report":
            return _DrillDownState(
                level="report",
                session_id=int(parsed["session_id"]),
            )
        if parsed["level"] == "hands":
            return _DrillDownState(
                level="hands",
                session_id=int(parsed["session_id"]),
            )
    raise dash.exceptions.PreventUpdate


# ---------------------------------------------------------------------------
# URL-based navigation initialiser
# ---------------------------------------------------------------------------
def _parse_nav_search(search: str) -> _DrillDownState | None:
    """Parse a URL query string into a drill-down state for deep linking.

    Handles two URL patterns produced by the dashboard highlight cards:
      - ``?session_id=X``              → report level for that session
      - ``?session_id=X&hand_id=Y``    → actions level for that hand

    Args:
        search: The URL search string including the leading ``?``,
                e.g. ``"?session_id=5&hand_id=12"``. Empty string or
                strings with no recognised params return ``None``.

    Returns:
        A _DrillDownState dict, or None when no navigation intent is found.
    """
    if not search:
        return None
    params = parse_qs(urlparse(search).query)
    if "hand_id" in params:
        return _DrillDownState(
            level="actions",
            hand_id=int(params["hand_id"][0]),
            session_id=int(params.get("session_id", ["0"])[0]),
        )
    if "session_id" in params:
        return _DrillDownState(level="report", session_id=int(params["session_id"][0]))
    return None


def _count_session_showdown_hands(db_path: str, session_id: int, player_id: int) -> int:
    """Count villain showdown hands with known cards — used for the loading estimate.

    Used only for the loading-time estimate shown in the analysis hint banner.
    Runs a single COUNT query — very fast.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT hp.hand_id)
            FROM hand_players hp
            JOIN hands h ON h.id = hp.hand_id
            WHERE h.session_id = ?
              AND hp.player_id = ?
              AND hp.went_to_showdown = 1
              AND hp.hole_cards IS NOT NULL
            """,
            (session_id, player_id),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


# ---------------------------------------------------------------------------
# Renderer — reacts to state + page navigation
# ---------------------------------------------------------------------------
@callback(
    Output("drill-down-content", "children"),
    Output("breadcrumb", "children"),
    Output("session-analysis-hint", "children"),
    Output("pending-session-report", "data"),
    Input("drill-down-state", "data"),
    Input("_pages_location", "pathname"),
    State("_pages_location", "search"),
    prevent_initial_call=False,
)
def _render(
    state: _DrillDownState | None,
    pathname: str,
    search: str,
) -> tuple[html.Div | str, html.Div, html.Div | None, int | None]:
    if pathname != "/sessions":
        raise dash.exceptions.PreventUpdate

    if state is None:
        state = _DrillDownState(level="sessions")

    # When arriving via page navigation (pathname change or initial app load),
    # URL query params take priority over the store's default value so that
    # dashboard highlight-card links land on the correct drill-down level.
    ctx = dash.callback_context
    triggered_props = {t["prop_id"] for t in (ctx.triggered or [])}
    if not triggered_props or any("pathname" in p for p in triggered_props):
        nav_state = _parse_nav_search(search)
        if nav_state is not None:
            state = nav_state

    level = state.get("level", "sessions")

    db_path = _get_db_path()

    if level == "sessions":
        return _render_sessions(db_path), _breadcrumb("sessions"), None, None

    session_id = int(state.get("session_id") or 0)
    if level == "report":
        player_id = _get_hero_player_id(db_path)
        n_showdown = (
            _count_session_showdown_hands(db_path, session_id, player_id)
            if player_id is not None
            else 0
        )
        est_secs = max(5, n_showdown * 2)
        if n_showdown > 0:
            hand_word = "hand" if n_showdown == 1 else "hands"
            hint_body = (
                f"Computing equity for {n_showdown} showdown {hand_word}"
                f" — estimated ~{est_secs}s."
            )
        else:
            hint_body = "Loading session data…"
        hint = html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            "⏳ Analysing session  ", style={"fontWeight": "600"}
                        ),
                        html.Span(
                            hint_body, style={"color": "#888", "fontSize": "13px"}
                        ),
                    ]
                ),
                html.Div(
                    html.Div(
                        className="session-report-progress-fill",
                        style={"animationDuration": f"{est_secs}s"},
                    ),
                    style={
                        "background": "#ffe5b0",
                        "borderRadius": "3px",
                        "height": "6px",
                        "marginTop": "8px",
                        "overflow": "hidden",
                    },
                ),
            ],
            style={
                "background": "#fffbe6",
                "border": "1px solid #ffe066",
                "borderRadius": "6px",
                "padding": "8px 14px",
                "fontSize": "14px",
            },
        )
        label = _get_session_label(db_path, session_id)
        placeholder = html.Div(style={"minHeight": "120px"})
        return (
            placeholder,
            _breadcrumb("report", session_label=label, session_id=session_id),
            hint,
            session_id,
        )

    if level == "hands":
        content, label = _render_hands(db_path, session_id)
        return (
            content,
            _breadcrumb("hands", session_label=label, session_id=session_id),
            None,
            None,
        )

    hand_id = int(state.get("hand_id") or 0)
    session_label = _get_session_label(db_path, session_id)
    content, hand_label = _render_actions(db_path, hand_id)
    return (
        content,
        _breadcrumb(
            "actions",
            session_label=session_label,
            session_id=session_id,
            hand_label=hand_label,
        ),
        None,
        None,
    )


@callback(
    Output("drill-down-content", "children", allow_duplicate=True),
    Output("session-analysis-hint", "children", allow_duplicate=True),
    Input("pending-session-report", "data"),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _load_session_report(
    session_id: int | None,
    state: _DrillDownState | None,
) -> tuple[html.Div | str, None]:
    """Phase 2: compute Session Report after the hint banner is shown.

    Triggered by pending-session-report store. Guards against stale triggers
    (e.g. user navigated away before computation finished).
    """
    if session_id is None:
        raise dash.exceptions.PreventUpdate
    if not state or state.get("level") != "report":
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
    content, _ = _render_session_report(db_path, int(session_id))
    return content, None


def _filter_sessions_data(
    df: pd.DataFrame,
    date_from: str | None,
    date_to: str | None,
    stakes: list[str] | None,
    pnl_min: float | None,
    pnl_max: float | None,
    min_hands: int | None,
    favorites_only: bool = False,
    currency_type: str | None = None,
) -> pd.DataFrame:
    """Filter a sessions DataFrame based on user-selected criteria.

    All parameters are optional; None means no constraint on that axis.

    Args:
        df: DataFrame from get_sessions (columns: start_time, small_blind,
            big_blind, hands_played, net_profit, currency).
        date_from: ISO date string lower bound for start_time (inclusive).
        date_to: ISO date string upper bound for start_time (inclusive).
        stakes: List of 'SB/BB' labels to keep; None keeps all.
        pnl_min: Minimum net_profit (inclusive); None keeps all.
        pnl_max: Maximum net_profit (inclusive); None keeps all.
        min_hands: Minimum hands_played (inclusive); None keeps all.
        currency_type: 'real' keeps USD/EUR, 'play' keeps PLAY, None keeps all.

    Returns:
        Filtered copy of df.
    """

    result = df.copy()
    if date_from:
        result = result[result["start_time"].astype(str) >= date_from]
    if date_to:
        result = result[result["start_time"].astype(str) <= date_to]
    if stakes:
        labels = result.apply(
            lambda r: f"{_fmt_blind(r['small_blind'])}/{_fmt_blind(r['big_blind'])}",
            axis=1,
        )
        result = result[labels.isin(stakes)]
    if pnl_min is not None:
        result = result[result["net_profit"].astype(float) >= float(pnl_min)]
    if pnl_max is not None:
        result = result[result["net_profit"].astype(float) <= float(pnl_max)]
    if min_hands is not None:
        result = result[result["hands_played"].astype(int) >= int(min_hands)]
    if favorites_only and "is_favorite" in result.columns:
        result = result[result["is_favorite"].astype(int) == 1]
    if currency_type == "real" and "currency" in result.columns:
        result = result[result["currency"].isin(["USD", "EUR"])]
    elif currency_type == "play" and "currency" in result.columns:
        result = result[result["currency"] == "PLAY"]
    return result


def _filter_hands_data(
    df: pd.DataFrame,
    pnl_min: float | None,
    pnl_max: float | None,
    positions: list[str] | None,
    saw_flop_only: bool,
    showdown_only: bool,
    favorites_only: bool = False,
) -> pd.DataFrame:
    """Filter a hands DataFrame based on user-selected criteria.

    Args:
        df: DataFrame from get_hands (columns: net_result, position,
            saw_flop, went_to_showdown).
        pnl_min: Minimum net_result (inclusive); None keeps all.
        pnl_max: Maximum net_result (inclusive); None keeps all.
        positions: List of position strings to keep; None keeps all.
        saw_flop_only: When True, keep only hands where hero saw the flop.
        showdown_only: When True, keep only hands that went to showdown.

    Returns:
        Filtered copy of df.
    """
    result = df.copy()
    if pnl_min is not None:
        result = result[result["net_result"].astype(float) >= float(pnl_min)]
    if pnl_max is not None:
        result = result[result["net_result"].astype(float) <= float(pnl_max)]
    if positions:
        result = result[result["position"].isin(positions)]
    if saw_flop_only:
        result = result[result["saw_flop"].astype(int) == 1]
    if showdown_only:
        result = result[result["went_to_showdown"].astype(int) == 1]
    if favorites_only and "is_favorite" in result.columns:
        result = result[result["is_favorite"].astype(int) == 1]
    return result


# ---------------------------------------------------------------------------
# Table builder helpers
# ---------------------------------------------------------------------------
def _build_session_table(df: pd.DataFrame) -> Any:  # dash_table has no mypy stubs
    """Render a filtered sessions DataFrame as a sortable DataTable."""
    _col_style = {"textAlign": "left", "padding": "8px 12px", "fontSize": "14px"}
    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_profit"])
        rows.append(
            {
                "id": int(row["id"]),
                "date": str(row["start_time"])[:10] if row["start_time"] else "—",
                "stakes": (
                    f"{_fmt_blind(row['small_blind'])}/{_fmt_blind(row['big_blind'])}"
                ),
                "hands": int(row["hands_played"]),
                "_pnl_raw": pnl,
            }
        )
    return dash_table.DataTable(  # type: ignore[attr-defined]
        id="session-table",
        columns=[
            {"name": "Date", "id": "date"},
            {"name": "Stakes", "id": "stakes"},
            {"name": "Hands", "id": "hands"},
            {"name": "Net P&L", "id": "_pnl_raw", "type": "numeric"},
        ],
        data=rows,
        sort_action="native",
        style_table={"width": "100%", "overflowX": "auto"},
        style_header={
            "backgroundColor": "#0074D9",
            "color": "white",
            "fontWeight": "bold",
            "padding": "8px 12px",
            "fontSize": "13px",
            "textAlign": "left",
        },
        style_cell=_col_style,
        style_data_conditional=[
            {
                "if": {"filter_query": "{_pnl_raw} >= 0", "column_id": "_pnl_raw"},
                "color": "#2ecc71",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": "{_pnl_raw} < 0", "column_id": "_pnl_raw"},
                "color": "#e74c3c",
                "fontWeight": "600",
            },
            {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"},
        ],
        style_as_list_view=True,
        row_selectable=False,
        cell_selectable=True,
        page_action="none",
    )


def _build_hand_table(df: pd.DataFrame) -> Any:  # dash_table has no mypy stubs
    """Render a filtered hands DataFrame as a sortable DataTable."""
    _col_style = {"textAlign": "left", "padding": "8px 12px", "fontSize": "14px"}
    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_result"]) if row["net_result"] is not None else 0.0
        rows.append(
            {
                "id": int(row["id"]),
                "hand_num": str(row["source_hand_id"]),
                "hole_cards": _format_cards_text(row["hole_cards"]),
                "pot": f"{float(row['total_pot']):,.6g}",
                "_pnl_raw": pnl,
            }
        )
    return dash_table.DataTable(  # type: ignore[attr-defined]
        id="hand-table",
        columns=[
            {"name": "Hand #", "id": "hand_num"},
            {"name": "Hole Cards", "id": "hole_cards"},
            {"name": "Pot", "id": "pot"},
            {"name": "Net Result", "id": "_pnl_raw", "type": "numeric"},
        ],
        data=rows,
        sort_action="native",
        style_table={"width": "100%", "overflowX": "auto"},
        style_header={
            "backgroundColor": "#0074D9",
            "color": "white",
            "fontWeight": "bold",
            "padding": "8px 12px",
            "fontSize": "13px",
            "textAlign": "left",
        },
        style_cell=_col_style,
        style_data_conditional=[
            {
                "if": {"filter_query": "{_pnl_raw} >= 0", "column_id": "_pnl_raw"},
                "color": "#2ecc71",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": "{_pnl_raw} < 0", "column_id": "_pnl_raw"},
                "color": "#e74c3c",
                "fontWeight": "600",
            },
            {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"},
        ],
        style_as_list_view=True,
        row_selectable=False,
        cell_selectable=True,
        page_action="none",
    )


# ---------------------------------------------------------------------------
# Level renderers
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "equity_sample_count": 2000,
    "lucky_equity_threshold": 40,  # stored as integer percentage
    "unlucky_equity_threshold": 60,
    "min_hands_classification": 15,
}


def _read_analysis_settings(db_path: str) -> dict[str, int]:
    """Read the four analysis settings from the settings table.

    Returns a dict with integer values:
        equity_sample_count, lucky_equity_threshold (0-100),
        unlucky_equity_threshold (0-100), min_hands_classification.

    Falls back to module-level defaults when the setting is absent or the
    database is in-memory.
    """
    if db_path == ":memory:":
        return dict(_DEFAULTS)
    conn = get_connection(db_path)
    try:
        return {
            key: int(get_setting(conn, key, default=str(default)))
            for key, default in _DEFAULTS.items()
        }
    finally:
        conn.close()


def _render_sessions(db_path: str) -> html.Div | str:
    if db_path == ":memory:":
        return html.Div("⚠️ No database connected.", style={"color": "orange"})
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return html.Div(
            "⚠️ No hero username set. Please set it on the Upload page first.",
            style={"color": "orange"},
        )

    from pokerhero.analysis.queries import get_sessions

    conn = get_connection(db_path)
    try:
        df = get_sessions(conn, player_id)
    finally:
        conn.close()

    if df.empty:
        return html.Div("No sessions found. Upload a hand history file to get started.")

    stakes_options = sorted(
        {
            f"{_fmt_blind(r['small_blind'])}/{_fmt_blind(r['big_blind'])}"
            for _, r in df.iterrows()
        }
    )

    _input_style = {
        "border": "1px solid #ddd",
        "borderRadius": "4px",
        "padding": "4px 8px",
        "fontSize": "13px",
        "height": "30px",
    }
    filter_bar = html.Div(
        [
            html.Span("From", style={"fontSize": "12px", "color": "#666"}),
            dcc.Input(
                id="session-filter-date-from",
                type="text",
                placeholder="YYYY-MM-DD",
                debounce=True,
                style=_input_style,
            ),
            html.Span("To", style={"fontSize": "12px", "color": "#666"}),
            dcc.Input(
                id="session-filter-date-to",
                type="text",
                placeholder="YYYY-MM-DD",
                debounce=True,
                style=_input_style,
            ),
            dcc.Dropdown(
                id="session-filter-stakes",
                options=[{"label": s, "value": s} for s in stakes_options],
                multi=True,
                placeholder="Stakes…",
                style={**_input_style, "minWidth": "120px", "height": "auto"},
                clearable=True,
            ),
            dcc.Input(
                id="session-filter-pnl-min",
                type="number",
                placeholder="P&L min",
                debounce=True,
                style={**_input_style, "width": "90px"},
            ),
            dcc.Input(
                id="session-filter-pnl-max",
                type="number",
                placeholder="P&L max",
                debounce=True,
                style={**_input_style, "width": "90px"},
            ),
            dcc.Input(
                id="session-filter-min-hands",
                type="number",
                placeholder="Min hands",
                debounce=True,
                style={**_input_style, "width": "90px"},
            ),
            dcc.Checklist(
                id="session-filter-favorites",
                options=[{"label": " ★ Favourites only", "value": "favorites"}],
                value=[],
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"fontSize": "13px"},
            ),
            dcc.RadioItems(
                id="session-filter-currency",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Real Money", "value": "real"},
                    {"label": "Play Money", "value": "play"},
                ],
                value="all",
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "13px"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "flexWrap": "wrap",
            "marginBottom": "12px",
            "padding": "8px 10px",
            "background": "#f8f9fa",
            "borderRadius": "6px",
            "border": "1px solid #e0e0e0",
        },
    )

    return html.Div(
        [
            filter_bar,
            _build_session_table(df),
            dcc.Store(id="session-data-store", data=df.to_dict("records")),
        ]
    )


def _get_session_label(db_path: str, session_id: int) -> str:
    """Return a human-readable session label, e.g. '2026-01-29  100/200'."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT start_time, small_blind, big_blind FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return f"Session #{session_id}"
    date = str(row[0])[:10] if row[0] else "—"
    return f"{date}  {_fmt_blind(row[1])}/{_fmt_blind(row[2])}"


# ---------------------------------------------------------------------------
# Session Report helpers
# ---------------------------------------------------------------------------

_KPI_CARD_STYLE: dict[str, str] = {
    "textAlign": "center",
    "minWidth": "80px",
    "padding": "12px 16px",
    "background": "#f8f9fa",
    "borderRadius": "8px",
    "border": "1px solid #e0e0e0",
}


def _build_session_kpi_strip(
    kpis_df: pd.DataFrame,
    actions_df: pd.DataFrame,
) -> html.Div:
    """Return a strip of session KPI cards: Hands, VPIP%, PFR%, AF, Win Rate.

    Args:
        kpis_df: DataFrame from get_session_kpis (per-hand hero rows).
        actions_df: DataFrame from get_session_hero_actions (post-flop actions).

    Returns:
        html.Div containing one card per KPI.
    """
    from pokerhero.analysis.stats import (
        aggression_factor,
        pfr_pct,
        vpip_pct,
        win_rate_bb100,
    )

    n = len(kpis_df)
    v = vpip_pct(kpis_df) * 100 if not kpis_df.empty else 0.0
    p = pfr_pct(kpis_df) * 100 if not kpis_df.empty else 0.0
    af = aggression_factor(actions_df) if not actions_df.empty else float("inf")
    wr = win_rate_bb100(kpis_df) if not kpis_df.empty else 0.0
    af_str = f"{af:.2f}" if af != float("inf") else "∞"
    wr_color = "#28a745" if wr >= 0 else "#dc3545"

    def _kpi(label: str, value: str, color: str = "#222") -> html.Div:
        return html.Div(
            [
                html.Div(
                    label,
                    style={
                        "fontSize": "11px",
                        "color": "#888",
                        "textTransform": "uppercase",
                        "marginBottom": "4px",
                    },
                ),
                html.Div(
                    value,
                    style={
                        "fontSize": "22px",
                        "fontWeight": "700",
                        "color": color,
                    },
                ),
            ],
            style=_KPI_CARD_STYLE,
        )

    return html.Div(
        [
            _kpi("Hands", str(n)),
            _kpi("VPIP", f"{v:.1f}%"),
            _kpi("PFR", f"{p:.1f}%"),
            _kpi("AF", af_str),
            _kpi("Win Rate", f"{wr:+.1f} bb/100", color=wr_color),
        ],
        style={
            "display": "flex",
            "gap": "12px",
            "flexWrap": "wrap",
            "marginBottom": "20px",
        },
    )


def _build_session_narrative(
    kpis_df: pd.DataFrame,
    actions_df: pd.DataFrame,
    session_label: str,
) -> html.Div:
    """Return a template-driven narrative paragraph summarising the session.

    Args:
        kpis_df: DataFrame from get_session_kpis (per-hand hero rows).
        actions_df: DataFrame from get_session_hero_actions (post-flop actions).
        session_label: Human-readable label e.g. '2026-01-29  100/200'.

    Returns:
        html.Div containing a single paragraph of narrative text.
    """
    from pokerhero.analysis.stats import (
        aggression_factor,
        pfr_pct,
        vpip_pct,
        win_rate_bb100,
    )

    n = len(kpis_df)
    if n == 0:
        return html.Div(
            "No hands found in this session.",
            style={"color": "#888", "fontSize": "13px"},
        )

    v = vpip_pct(kpis_df) * 100
    p = pfr_pct(kpis_df) * 100
    af = aggression_factor(actions_df) if not actions_df.empty else float("inf")
    wr = win_rate_bb100(kpis_df)
    af_str = f"{af:.2f}" if af != float("inf") else "∞"
    direction = "won" if wr >= 0 else "lost"
    wr_abs = f"{abs(wr):.1f}"

    text = (
        f"In your {n}-hand session ({session_label}), you played {v:.0f}% of "
        f"hands (VPIP) and raised preflop {p:.0f}% of the time (PFR). "
        f"Post-flop your aggression factor was {af_str}. "
        f"Overall you {direction} at a rate of {wr_abs} bb/100."
    )
    return html.Div(
        html.P(
            text,
            style={"fontSize": "14px", "lineHeight": "1.6", "color": "#444"},
        ),
        style={"marginBottom": "16px"},
    )


def _build_ev_summary(
    showdown_df: pd.DataFrame,
    *,
    sample_count: int = 2000,
    lucky_threshold: float = 0.4,
    unlucky_threshold: float = 0.6,
) -> html.Div:
    """Return an EV luck indicator based on showdown/all-in hands.

    Computes equity for each hand via the LRU-cached compute_equity and
    classifies the session as above/below/near equity.

    Args:
        showdown_df: DataFrame from get_session_showdown_hands.
        sample_count: Monte Carlo samples passed to compute_equity_multiway.
        lucky_threshold: Hero wins with equity below this fraction → Lucky.
        unlucky_threshold: Hero loses with equity above this fraction → Unlucky.

    Returns:
        html.Div with a luck verdict and showdown hand count.
    """
    if showdown_df.empty:
        return html.Div(
            "No showdown hands with known villain cards in this session.",
            style={"color": "#888", "fontSize": "13px"},
        )

    from pokerhero.analysis.stats import compute_equity_multiway

    n = len(showdown_df)
    lucky = 0
    unlucky = 0
    errors = 0

    for _, row in showdown_df.iterrows():
        try:
            eq = compute_equity_multiway(
                str(row["hero_cards"]).strip(),
                str(row["villain_cards"]).strip(),
                str(row["board"]).strip(),
                sample_count,
            )
        except Exception:
            errors += 1
            continue
        hero_won = float(row["net_result"]) > 0
        if hero_won and eq < lucky_threshold:
            lucky += 1
        elif not hero_won and eq > unlucky_threshold:
            unlucky += 1

    if lucky > 0 and unlucky == 0:
        verdict, vcolor = "👍 Ran above equity", "#28a745"
    elif unlucky > 0 and lucky == 0:
        verdict, vcolor = "👎 Ran below equity", "#dc3545"
    elif lucky > unlucky:
        verdict, vcolor = "👍 Slightly above equity", "#28a745"
    elif unlucky > lucky:
        verdict, vcolor = "👎 Slightly below equity", "#dc3545"
    else:
        verdict, vcolor = "~ Ran near equity", "#888"

    hand_word = "hand" if n == 1 else "hands"
    children: list[html.H5 | html.P | html.Div] = [
        html.H5(
            "EV Summary",
            style={"marginBottom": "6px", "color": "#333"},
        ),
        html.P(
            f"{n} showdown {hand_word} with known villain cards.",
            style={"fontSize": "13px", "color": "#555", "marginBottom": "6px"},
        ),
        html.Div(
            verdict,
            style={
                "fontSize": "16px",
                "fontWeight": "600",
                "color": vcolor,
            },
        ),
    ]
    if errors:
        err_word = "hand" if errors == 1 else "hands"
        children.append(
            html.P(
                f"⚠️ {errors} {err_word} — equity unavailable"
                " (unrecognised card format).",
                style={"fontSize": "12px", "color": "#888", "marginTop": "6px"},
            )
        )
    return html.Div(children, style={"marginBottom": "20px"})


def _build_flagged_hands_list(
    showdown_df: pd.DataFrame,
    *,
    sample_count: int = 2000,
    lucky_threshold: float = 0.4,
    unlucky_threshold: float = 0.6,
) -> html.Div:
    """Return a list of notably lucky or unlucky hands.

    A hand is flagged as Lucky when hero won with equity < *lucky_threshold*,
    or Unlucky when hero lost with equity > *unlucky_threshold*.

    Args:
        showdown_df: DataFrame from get_session_showdown_hands.
        sample_count: Monte Carlo samples passed to compute_equity_multiway.
        lucky_threshold: Hero wins with equity below this fraction → Lucky.
        unlucky_threshold: Hero loses with equity above this fraction → Unlucky.

    Returns:
        html.Div listing flagged hands, or an empty-state message.
    """
    if showdown_df.empty:
        return html.Div(
            "No showdown data available for analysis.",
            style={"color": "#888", "fontSize": "13px"},
        )

    from pokerhero.analysis.stats import compute_equity_multiway

    flagged: list[html.Div] = []
    for _, row in showdown_df.iterrows():
        try:
            eq = compute_equity_multiway(
                str(row["hero_cards"]).strip(),
                str(row["villain_cards"]).strip(),
                str(row["board"]).strip(),
                sample_count,
            )
        except Exception:
            flagged.append(
                html.Div(
                    [
                        html.Span(
                            "⚠️ Equity unavailable",
                            style={
                                "marginRight": "10px",
                                "color": "#888",
                                "fontWeight": "600",
                            },
                        ),
                        html.Span(
                            f"Hand #{row['source_hand_id']}",
                            style={"fontSize": "13px", "color": "#aaa"},
                        ),
                    ],
                    style={"padding": "6px 0", "borderBottom": "1px solid #f0f0f0"},
                )
            )
            continue
        hero_won = float(row["net_result"]) > 0
        if hero_won and eq < lucky_threshold:
            flag, fcolor = "🍀 Lucky", "#28a745"
        elif not hero_won and eq > unlucky_threshold:
            flag, fcolor = "😞 Unlucky", "#dc3545"
        else:
            continue
        flagged.append(
            html.Div(
                [
                    html.Span(
                        flag,
                        style={
                            "marginRight": "10px",
                            "color": fcolor,
                            "fontWeight": "600",
                        },
                    ),
                    html.Span(
                        f"Hand #{row['source_hand_id']}",
                        style={"marginRight": "10px", "fontSize": "13px"},
                    ),
                    html.Span(
                        f"Equity: {eq * 100:.0f}%",
                        style={"color": "#888", "fontSize": "12px"},
                    ),
                ],
                style={"padding": "6px 0", "borderBottom": "1px solid #f0f0f0"},
            )
        )

    if not flagged:
        return html.Div(
            "No significantly lucky or unlucky spots detected.",
            style={"color": "#888", "fontSize": "13px"},
        )
    return html.Div(
        [
            html.H5("Notable Hands", style={"marginBottom": "8px", "color": "#333"}),
            *flagged,
        ],
        style={"marginBottom": "20px"},
    )


def _render_session_report(db_path: str, session_id: int) -> tuple[html.Div | str, str]:
    """Render the Session Report intermediate view for a single session.

    Shows a narrative paragraph, KPI strip, EV luck summary, and a list of
    notable hands, plus a button to browse all hands in this session.

    Args:
        db_path: Path to the SQLite database file.
        session_id: Internal integer id of the session row.

    Returns:
        Tuple of (content Div, session label string).
    """
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return (
            html.Div(
                "⚠️ No hero username set. Please set it on the Upload page first.",
                style={"color": "orange"},
            ),
            "",
        )

    from pokerhero.analysis.queries import (
        get_session_hero_actions,
        get_session_kpis,
        get_session_showdown_hands,
    )

    conn = get_connection(db_path)
    try:
        kpis_df = get_session_kpis(conn, session_id, player_id)
        actions_df = get_session_hero_actions(conn, session_id, player_id)
        showdown_df = get_session_showdown_hands(conn, session_id, player_id)
    finally:
        conn.close()

    s = _read_analysis_settings(db_path)
    sample_count = s["equity_sample_count"]
    lucky_threshold = s["lucky_equity_threshold"] / 100.0
    unlucky_threshold = s["unlucky_equity_threshold"] / 100.0

    session_label = _get_session_label(db_path, session_id)
    n_hands = len(kpis_df)

    content = html.Div(
        [
            _build_session_narrative(kpis_df, actions_df, session_label),
            _build_session_kpi_strip(kpis_df, actions_df),
            _build_ev_summary(
                showdown_df,
                sample_count=sample_count,
                lucky_threshold=lucky_threshold,
                unlucky_threshold=unlucky_threshold,
            ),
            _build_flagged_hands_list(
                showdown_df,
                sample_count=sample_count,
                lucky_threshold=lucky_threshold,
                unlucky_threshold=unlucky_threshold,
            ),
            html.Button(
                f"Browse all {n_hands} hands",
                id="session-report-browse-btn",
                n_clicks=0,
                style={
                    "marginTop": "16px",
                    "padding": "8px 20px",
                    "background": "#0074D9",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "14px",
                },
            ),
        ],
        style={"maxWidth": "900px"},
    )
    return content, session_label


def _render_hands(db_path: str, session_id: int) -> tuple[html.Div | str, str]:
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return "", ""

    from pokerhero.analysis.queries import get_hands, get_session_player_stats

    conn = get_connection(db_path)
    try:
        df = get_hands(conn, session_id, player_id)
        fav_row = conn.execute(
            "SELECT is_favorite FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        opp_df = get_session_player_stats(conn, session_id, player_id)
    finally:
        conn.close()

    is_fav: bool = bool(fav_row and fav_row[0])
    session_label = _get_session_label(db_path, session_id)

    min_hands = _read_analysis_settings(db_path)["min_hands_classification"]

    if df.empty:
        return html.Div("No hands found for this session."), session_label

    positions = sorted(df["position"].dropna().unique().tolist())
    _input_style = {
        "border": "1px solid #ddd",
        "borderRadius": "4px",
        "padding": "4px 8px",
        "fontSize": "13px",
        "height": "30px",
    }
    filter_bar = html.Div(
        [
            dcc.Input(
                id="hand-filter-pnl-min",
                type="number",
                placeholder="P&L min",
                debounce=True,
                style={**_input_style, "width": "90px"},
            ),
            dcc.Input(
                id="hand-filter-pnl-max",
                type="number",
                placeholder="P&L max",
                debounce=True,
                style={**_input_style, "width": "90px"},
            ),
            dcc.Dropdown(
                id="hand-filter-position",
                options=[{"label": p, "value": p} for p in positions],
                multi=True,
                placeholder="Position…",
                style={**_input_style, "minWidth": "130px", "height": "auto"},
                clearable=True,
            ),
            dcc.Checklist(
                id="hand-filter-flags",
                options=[
                    {"label": " Saw flop", "value": "saw_flop"},
                    {"label": " Showdown", "value": "showdown"},
                ],
                value=[],
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px", "fontSize": "13px"},
            ),
            dcc.Checklist(
                id="hand-filter-favorites",
                options=[{"label": " ★ Favourites only", "value": "favorites"}],
                value=[],
                inline=True,
                inputStyle={"marginRight": "4px"},
                labelStyle={"fontSize": "13px"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "flexWrap": "wrap",
            "marginBottom": "12px",
            "padding": "8px 10px",
            "background": "#f8f9fa",
            "borderRadius": "6px",
            "border": "1px solid #e0e0e0",
        },
    )

    _fav_btn_style = {
        "display": "flex",
        "alignItems": "center",
        "gap": "6px",
        "background": "#fff8ec" if is_fav else "#f5f5f5",
        "border": "1px solid #f5a623" if is_fav else "1px solid #ccc",
        "borderRadius": "20px",
        "padding": "4px 12px",
        "fontSize": "15px",
        "cursor": "pointer",
        "color": "#f5a623" if is_fav else "#888",
        "fontWeight": "600",
        "lineHeight": "1.4",
    }

    profile_cards = [
        _build_opponent_profile_card(
            row["username"],
            int(row["hands_played"]),
            int(row["vpip_count"]),
            int(row["pfr_count"]),
            min_hands=min_hands,
        )
        for _, row in opp_df.iterrows()
    ]
    profiles_panel = html.Div(
        profile_cards,
        id="opponent-profiles-panel",
        style={
            "display": "none",
            "flexWrap": "wrap",
            "gap": "10px",
            "padding": "10px 0",
        },
    )
    profiles_btn = html.Button(
        "👥 Opponent Profiles",
        id="opponent-profiles-btn",
        n_clicks=0,
        style={
            "background": "#f0f4ff",
            "border": "1px solid #aac",
            "borderRadius": "20px",
            "padding": "4px 12px",
            "fontSize": "13px",
            "cursor": "pointer",
        },
    )

    return (
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            [
                                _fav_button_label(is_fav),
                                " Favourite session",
                            ],
                            id="session-fav-btn",
                            n_clicks=0,
                            style=_fav_btn_style,
                        ),
                        profiles_btn,
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "flex-end",
                        "gap": "8px",
                        "marginBottom": "8px",
                    },
                ),
                profiles_panel,
                filter_bar,
                _build_hand_table(df),
                dcc.Store(id="hand-data-store", data=df.to_dict("records")),
                dcc.Store(id="session-fav-id-store", data=session_id),
            ]
        ),
        session_label,
    )


def _render_actions(db_path: str, hand_id: int) -> tuple[html.Div | str, str]:
    from pokerhero.analysis.queries import get_actions, get_session_player_stats
    from pokerhero.analysis.stats import compute_ev

    hero_id = _get_hero_player_id(db_path)
    min_hands = _read_analysis_settings(db_path)["min_hands_classification"]

    conn = get_connection(db_path)
    try:
        df = get_actions(conn, hand_id)
        hand_row = conn.execute(
            "SELECT source_hand_id, board_flop, board_turn, board_river,"
            " is_favorite, session_id FROM hands WHERE id = ?",
            (hand_id,),
        ).fetchone()
        hero_cards: str | None = None
        hero_net_result: float | None = None
        # Map player_id → hole_cards for EV calculation at all-in spots
        all_hole_cards: dict[int, str] = {}
        villain_showdown: list[dict[str, Any]] = []
        opp_stats_map: dict[str, dict[str, int]] = {}
        if hero_id is not None:
            hole_row = conn.execute(
                "SELECT hole_cards, net_result FROM hand_players"
                " WHERE hand_id = ? AND player_id = ?",
                (hand_id, hero_id),
            ).fetchone()
            if hole_row:
                hero_cards = hole_row[0]
                if hole_row[1] is not None:
                    hero_net_result = float(hole_row[1])
        for row in conn.execute(
            "SELECT player_id, hole_cards FROM hand_players"
            " WHERE hand_id = ? AND hole_cards IS NOT NULL",
            (hand_id,),
        ).fetchall():
            all_hole_cards[int(row[0])] = row[1]
        # Fetch villain cards + names for the showdown display
        villain_rows = conn.execute(
            "SELECT p.username, hp.position, hp.hole_cards, hp.net_result"
            " FROM hand_players hp"
            " JOIN players p ON hp.player_id = p.id"
            " WHERE hp.hand_id = ? AND hp.hole_cards IS NOT NULL"
            "   AND hp.player_id != ?",
            (hand_id, hero_id if hero_id is not None else -1),
        ).fetchall()
        villain_showdown = [
            {
                "username": r[0],
                "position": r[1] or "",
                "hole_cards": r[2],
                "net_result": float(r[3]) if r[3] is not None else None,
            }
            for r in villain_rows
        ]
        # Fetch session-level opponent stats for archetype badges at showdown.
        if hand_row is not None and hero_id is not None:
            session_id_val = hand_row[5]
            opp_df = get_session_player_stats(conn, session_id_val, hero_id)
            for _, opp_row in opp_df.iterrows():
                opp_stats_map[opp_row["username"]] = {
                    "hands_played": int(opp_row["hands_played"]),
                    "vpip_count": int(opp_row["vpip_count"]),
                    "pfr_count": int(opp_row["pfr_count"]),
                }
    finally:
        conn.close()

    if df.empty or hand_row is None:
        return html.Div("No actions found for this hand."), ""

    source_id, flop, turn, river, hand_is_fav_raw, _session_id = hand_row
    hand_label = f"Hand #{source_id}"
    hand_is_fav: bool = bool(hand_is_fav_raw)

    # --- Hero hole cards row ---
    hero_row: html.Div | None = None
    if hero_cards:
        hero_row = html.Div(
            [
                html.Span(
                    "Hero: ",
                    style={
                        "fontWeight": "600",
                        "fontSize": "13px",
                        "marginRight": "6px",
                        "color": "#555",
                    },
                ),
                _render_cards(hero_cards),
            ],
            style={"marginBottom": "8px"},
        )

    # --- Board row ---
    _sep = html.Span(
        "│",
        style={"color": "#ccc", "margin": "0 8px", "fontWeight": "300"},
    )
    board_elems: list[html.Span] = [
        html.Span(
            "Board: ",
            style={
                "fontWeight": "600",
                "color": "#555",
                "fontSize": "13px",
                "marginRight": "6px",
            },
        )
    ]
    if flop:
        board_elems.append(_render_cards(flop))
        if turn:
            board_elems.append(_sep)
            board_elems.append(_render_cards(turn))
            if river:
                board_elems.append(_sep)
                board_elems.append(_render_cards(river))
    else:
        board_elems.append(html.Span("—", style={"color": "#888"}))
    board_div = html.Div(
        board_elems,
        style={
            "display": "flex",
            "alignItems": "center",
            "marginBottom": "12px",
        },
    )

    sections: list[html.Div] = []
    current_street: str | None = None
    street_rows: list[html.Tr] = []
    seen_villains: set[str] = set()  # track first-appearance badge per villain

    def _flush(street: str, rows: list[html.Tr]) -> html.Div:
        colour = _STREET_COLOURS.get(street, "#333")
        return html.Div(
            [
                html.H5(
                    street,
                    style={
                        "color": colour,
                        "borderBottom": f"2px solid {colour}",
                        "paddingBottom": "4px",
                        "marginBottom": "4px",
                    },
                ),
                html.Table(
                    rows,
                    style={
                        "width": "100%",
                        "borderCollapse": "collapse",
                        "marginBottom": "12px",
                    },
                ),
            ]
        )

    for _, action in df.iterrows():
        street = str(action["street"])
        if street != current_street:
            if current_street is not None:
                sections.append(_flush(current_street, street_rows))
            current_street = street
            street_rows = []

        username = str(action["username"])
        position = str(action["position"]) if action["position"] else ""
        actor_str = f"{username} ({position})" if position else username
        if action["is_hero"]:
            actor_str = f"🦸 {actor_str}"

        # Show archetype badge on the villain's very first action in this hand.
        actor_badge: list[Any] = []
        if (
            not action["is_hero"]
            and opp_stats_map
            and username in opp_stats_map
            and username not in seen_villains
        ):
            from pokerhero.analysis.stats import classify_player as _cp

            s = opp_stats_map[username]
            h = int(s["hands_played"])
            vp = int(s["vpip_count"]) / h * 100 if h > 0 else 0.0
            pf = int(s["pfr_count"]) / h * 100 if h > 0 else 0.0
            arch = _cp(vp, pf, h, min_hands=min_hands)
            if arch is not None:
                actor_badge = [
                    html.Span(
                        arch,
                        style={
                            "background": _ARCHETYPE_COLORS.get(arch, "#999"),
                            "color": "#fff",
                            "borderRadius": "4px",
                            "padding": "1px 5px",
                            "fontSize": "10px",
                            "fontWeight": "700",
                            "marginLeft": "5px",
                            "verticalAlign": "middle",
                        },
                    )
                ]
            seen_villains.add(username)

        action_type = str(action["action_type"])
        amount = float(action["amount"])
        pot_before = float(action["pot_before"])
        amount_to_call = float(action["amount_to_call"])

        label = action_type
        if amount > 0:
            label += f"  {amount:,.6g}"
        if action["is_all_in"]:
            label += "  🚨 ALL-IN"

        raw_spr = action["spr"]
        raw_mdf = action["mdf"]
        spr_val = (
            float(raw_spr)
            if raw_spr is not None and not math.isnan(float(raw_spr))
            else None
        )
        mdf_val = (
            float(raw_mdf)
            if raw_mdf is not None and not math.isnan(float(raw_mdf))
            else None
        )
        extra = _format_math_cell(
            spr=spr_val,
            mdf=mdf_val,
            is_hero=bool(action["is_hero"]),
            amount_to_call=amount_to_call,
            pot_before=pot_before,
        )

        # EV for hero all-in actions when villain cards are known
        ev_cell: str = "—"
        if action["is_hero"] and action["is_all_in"] and hero_cards:
            board_so_far = " ".join(
                filter(
                    None,
                    [
                        flop if street in ("FLOP", "TURN", "RIVER") else None,
                        turn if street in ("TURN", "RIVER") else None,
                        river if street == "RIVER" else None,
                    ],
                )
            )
            villain_hole: str | None = next(
                (v for pid, v in all_hole_cards.items() if pid != hero_id),
                None,
            )
            ev_val = None
            try:
                ev_val = compute_ev(
                    hero_cards, villain_hole, board_so_far, amount, pot_before + amount
                )
            except Exception:
                pass
            if ev_val is not None:
                ev_cell = f"EV: {_fmt_pnl(ev_val)}"

        street_rows.append(
            html.Tr(
                [
                    html.Td(
                        [actor_str, *actor_badge],
                        style={**_TD, "width": "200px", "fontWeight": "600"},
                    ),
                    html.Td(label, style=_TD),
                    html.Td(
                        f"Pot: {pot_before:,.6g}",
                        style={**_TD, "color": "#888", "fontSize": "12px"},
                    ),
                    html.Td(extra, style={**_TD, "color": "#555", "fontSize": "12px"}),
                    html.Td(
                        ev_cell,
                        style={
                            **_TD,
                            "fontSize": "12px",
                            "color": (
                                "green"
                                if ev_cell.startswith("EV: +")
                                else ("red" if ev_cell.startswith("EV: -") else "#bbb")
                            ),
                        },
                    ),
                ],
                style=_action_row_style(bool(action["is_hero"])),
            )
        )

    if current_street is not None:
        sections.append(_flush(current_street, street_rows))

    board_str = " ".join(p for p in [flop, turn, river] if p)
    showdown_div = _build_showdown_section(
        villain_showdown,
        hero_name="Hero",
        hero_cards=hero_cards,
        board=board_str,
        opp_stats=opp_stats_map if opp_stats_map else None,
        min_hands=min_hands,
        hero_net_result=hero_net_result,
    )
    if showdown_div is not None:
        sections.append(showdown_div)

    header_children: list[Any] = [
        html.Div(
            [
                html.H3(hand_label, style={"marginTop": "0", "marginBottom": "0"}),
                html.Button(
                    [
                        _fav_button_label(hand_is_fav),
                        " Favourite hand",
                    ],
                    id="hand-fav-btn",
                    n_clicks=0,
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "6px",
                        "background": "#fff8ec" if hand_is_fav else "#f5f5f5",
                        "border": "1px solid #f5a623"
                        if hand_is_fav
                        else "1px solid #ccc",
                        "borderRadius": "20px",
                        "padding": "4px 12px",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "color": "#f5a623" if hand_is_fav else "#888",
                        "fontWeight": "600",
                        "lineHeight": "1.4",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "8px",
            },
        ),
        dcc.Store(id="hand-fav-id-store", data=hand_id),
        *([] if hero_row is None else [hero_row]),
        board_div,
        *(
            [vs]
            if (vs := _build_villain_summary(opp_stats_map, min_hands=min_hands))
            is not None
            else []
        ),
    ]
    return (
        html.Div([*header_children, *sections]),
        hand_label,
    )


# ---------------------------------------------------------------------------
# Filter callbacks — update DataTable data when filter inputs change
# ---------------------------------------------------------------------------
@callback(
    Output("session-table", "data"),
    Input("session-filter-date-from", "value"),
    Input("session-filter-date-to", "value"),
    Input("session-filter-stakes", "value"),
    Input("session-filter-pnl-min", "value"),
    Input("session-filter-pnl-max", "value"),
    Input("session-filter-min-hands", "value"),
    Input("session-filter-favorites", "value"),
    Input("session-filter-currency", "value"),
    State("session-data-store", "data"),
    prevent_initial_call=True,
)
def _apply_session_filters(
    date_from: str | None,
    date_to: str | None,
    stakes: list[str] | None,
    pnl_min: float | None,
    pnl_max: float | None,
    min_hands: float | None,
    fav_filter: list[str] | None,
    currency: str | None,
    data: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(data)
    currency_type = None if (currency is None or currency == "all") else currency
    filtered = _filter_sessions_data(
        df,
        date_from,
        date_to,
        stakes,
        pnl_min,
        pnl_max,
        int(min_hands) if min_hands is not None else None,
        favorites_only="favorites" in (fav_filter or []),
        currency_type=currency_type,
    )
    return list(_build_session_table(filtered).data)


@callback(
    Output("hand-table", "data"),
    Input("hand-filter-pnl-min", "value"),
    Input("hand-filter-pnl-max", "value"),
    Input("hand-filter-position", "value"),
    Input("hand-filter-flags", "value"),
    Input("hand-filter-favorites", "value"),
    State("hand-data-store", "data"),
    prevent_initial_call=True,
)
def _apply_hand_filters(
    pnl_min: float | None,
    pnl_max: float | None,
    positions: list[str] | None,
    flags: list[str] | None,
    fav_filter: list[str] | None,
    data: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(data)
    flags = flags or []
    filtered = _filter_hands_data(
        df,
        pnl_min,
        pnl_max,
        positions or None,
        "saw_flop" in flags,
        "showdown" in flags,
        favorites_only="favorites" in (fav_filter or []),
    )
    return list(_build_hand_table(filtered).data)


@callback(
    Output("session-fav-btn", "children"),
    Output("session-fav-btn", "style"),
    Input("session-fav-btn", "n_clicks"),
    State("session-fav-id-store", "data"),
    prevent_initial_call=True,
)
def _toggle_session_fav(
    n_clicks: int | None,
    session_id: int | None,
) -> tuple[list[str], dict[str, str]]:
    if not n_clicks or session_id is None:
        raise dash.exceptions.PreventUpdate
    from pokerhero.database.db import toggle_session_favorite

    db_path = _get_db_path()
    conn = get_connection(db_path)
    try:
        toggle_session_favorite(conn, int(session_id))
        conn.commit()
        row = conn.execute(
            "SELECT is_favorite FROM sessions WHERE id = ?", (int(session_id),)
        ).fetchone()
    finally:
        conn.close()
    is_fav = bool(row and row[0])
    style: dict[str, str] = {
        "display": "flex",
        "alignItems": "center",
        "gap": "6px",
        "background": "#fff8ec" if is_fav else "#f5f5f5",
        "border": "1px solid #f5a623" if is_fav else "1px solid #ccc",
        "borderRadius": "20px",
        "padding": "4px 12px",
        "fontSize": "15px",
        "cursor": "pointer",
        "color": "#f5a623" if is_fav else "#888",
        "fontWeight": "600",
        "lineHeight": "1.4",
    }
    return [_fav_button_label(is_fav), " Favourite session"], style


@callback(
    Output("hand-fav-btn", "children"),
    Output("hand-fav-btn", "style"),
    Input("hand-fav-btn", "n_clicks"),
    State("hand-fav-id-store", "data"),
    prevent_initial_call=True,
)
def _toggle_hand_fav(
    n_clicks: int | None,
    hand_id: int | None,
) -> tuple[list[str], dict[str, str]]:
    if not n_clicks or hand_id is None:
        raise dash.exceptions.PreventUpdate
    from pokerhero.database.db import toggle_hand_favorite

    db_path = _get_db_path()
    conn = get_connection(db_path)
    try:
        toggle_hand_favorite(conn, int(hand_id))
        conn.commit()
        row = conn.execute(
            "SELECT is_favorite FROM hands WHERE id = ?", (int(hand_id),)
        ).fetchone()
    finally:
        conn.close()
    is_fav = bool(row and row[0])
    style: dict[str, str] = {
        "display": "flex",
        "alignItems": "center",
        "gap": "6px",
        "background": "#fff8ec" if is_fav else "#f5f5f5",
        "border": "1px solid #f5a623" if is_fav else "1px solid #ccc",
        "borderRadius": "20px",
        "padding": "4px 12px",
        "fontSize": "15px",
        "cursor": "pointer",
        "color": "#f5a623" if is_fav else "#888",
        "fontWeight": "600",
        "lineHeight": "1.4",
    }
    return [_fav_button_label(is_fav), " Favourite hand"], style


@callback(
    Output("opponent-profiles-panel", "style"),
    Input("opponent-profiles-btn", "n_clicks"),
    prevent_initial_call=True,
)
def _toggle_opponent_profiles(n_clicks: int | None) -> dict[str, str]:
    """Show or hide the opponent profiles panel on each button click."""
    visible = bool(n_clicks) and n_clicks % 2 == 1  # type: ignore[operator]
    return {
        "display": "flex" if visible else "none",
        "flexWrap": "wrap",
        "gap": "10px",
        "padding": "10px 0",
    }


@callback(
    Output("drill-down-state", "data", allow_duplicate=True),
    Input("session-report-browse-btn", "n_clicks"),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _browse_session_hands(
    n_clicks: int | None,
    current_state: _DrillDownState,
) -> _DrillDownState:
    """Navigate from Session Report to the full hands list for that session."""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    session_id = int(current_state.get("session_id") or 0)
    if not session_id:
        raise dash.exceptions.PreventUpdate
    return _DrillDownState(level="hands", session_id=session_id)
