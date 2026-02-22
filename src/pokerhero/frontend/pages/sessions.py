"""Sessions page — breadcrumb drill-down: Sessions → Hands → Actions."""

from __future__ import annotations

import json
import math
from typing import Any, NotRequired, TypedDict
from urllib.parse import parse_qs, urlparse

import dash
import pandas as pd
from dash import Input, Output, State, callback, dcc, html

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
        dcc.Loading(html.Div(id="drill-down-content")),
        dcc.Store(id="drill-down-state", data={"level": "sessions"}),
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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
    if level == "hands":
        return html.Div(
            [
                html.Button(
                    "Sessions",
                    id={"type": "breadcrumb-btn", "level": "sessions", "session_id": 0},
                    style=btn_style,
                    n_clicks=0,
                ),
                sep,
                html.Span(session_label or f"Session #{session_id}", style=plain_style),
            ]
        )
    # actions level
    return html.Div(
        [
            html.Button(
                "Sessions",
                id={"type": "breadcrumb-btn", "level": "sessions", "session_id": 0},
                style=btn_style,
                n_clicks=0,
            ),
            sep,
            html.Button(
                session_label or f"Session #{session_id}",
                id={
                    "type": "breadcrumb-btn",
                    "level": "hands",
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
# State updater — all row/breadcrumb clicks funnel into drill-down-state
# ---------------------------------------------------------------------------
@callback(
    Output("drill-down-state", "data"),
    Input({"type": "session-row", "index": dash.ALL}, "n_clicks"),
    Input({"type": "hand-row", "index": dash.ALL}, "n_clicks"),
    Input(
        {"type": "breadcrumb-btn", "level": dash.ALL, "session_id": dash.ALL},
        "n_clicks",
    ),
    State("drill-down-state", "data"),
    prevent_initial_call=True,
)
def _update_state(
    _session_clicks: list[int | None],
    _hand_clicks: list[int | None],
    _breadcrumb_clicks: list[int | None],
    current_state: _DrillDownState,
) -> _DrillDownState:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    trigger = ctx.triggered[0]
    # Ignore synthetic fires from newly-rendered pattern-match components (n_clicks=0)
    if not trigger.get("value"):
        raise dash.exceptions.PreventUpdate
    tid = trigger["prop_id"].split(".")[0]
    try:
        parsed = json.loads(tid)
    except (json.JSONDecodeError, ValueError):
        raise dash.exceptions.PreventUpdate

    t = parsed.get("type")
    if t == "session-row":
        return _DrillDownState(level="hands", session_id=int(parsed["index"]))
    if t == "hand-row":
        return _DrillDownState(
            level="actions",
            session_id=int(current_state.get("session_id") or 0),
            hand_id=int(parsed["index"]),
        )
    if t == "breadcrumb-btn":
        if parsed["level"] == "sessions":
            return _DrillDownState(level="sessions")
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
      - ``?session_id=X``              → hands level for that session
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
        return _DrillDownState(level="hands", session_id=int(params["session_id"][0]))
    return None


# ---------------------------------------------------------------------------
# Renderer — reacts to state + page navigation
# ---------------------------------------------------------------------------
@callback(
    Output("drill-down-content", "children"),
    Output("breadcrumb", "children"),
    Input("drill-down-state", "data"),
    Input("_pages_location", "pathname"),
    State("_pages_location", "search"),
    prevent_initial_call=False,
)
def _render(
    state: _DrillDownState | None,
    pathname: str,
    search: str,
) -> tuple[html.Div | str, html.Div]:
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
        return _render_sessions(db_path), _breadcrumb("sessions")

    session_id = int(state.get("session_id") or 0)
    if level == "hands":
        content, label = _render_hands(db_path, session_id)
        return content, _breadcrumb("hands", session_label=label, session_id=session_id)

    hand_id = int(state.get("hand_id") or 0)
    session_label = _get_session_label(db_path, session_id)
    content, hand_label = _render_actions(db_path, hand_id)
    return content, _breadcrumb(
        "actions",
        session_label=session_label,
        session_id=session_id,
        hand_label=hand_label,
    )


# ---------------------------------------------------------------------------
# Pure filter helpers (no Dash, fully testable in isolation)
# ---------------------------------------------------------------------------
def _filter_sessions_data(
    df: pd.DataFrame,
    date_from: str | None,
    date_to: str | None,
    stakes: list[str] | None,
    pnl_min: float | None,
    pnl_max: float | None,
    min_hands: int | None,
) -> pd.DataFrame:
    """Filter a sessions DataFrame based on user-selected criteria.

    All parameters are optional; None means no constraint on that axis.

    Args:
        df: DataFrame from get_sessions (columns: start_time, small_blind,
            big_blind, hands_played, net_profit).
        date_from: ISO date string lower bound for start_time (inclusive).
        date_to: ISO date string upper bound for start_time (inclusive).
        stakes: List of 'SB/BB' labels to keep; None keeps all.
        pnl_min: Minimum net_profit (inclusive); None keeps all.
        pnl_max: Maximum net_profit (inclusive); None keeps all.
        min_hands: Minimum hands_played (inclusive); None keeps all.

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
            lambda r: f"{int(r['small_blind'])}/{int(r['big_blind'])}", axis=1
        )
        result = result[labels.isin(stakes)]
    if pnl_min is not None:
        result = result[result["net_profit"].astype(float) >= float(pnl_min)]
    if pnl_max is not None:
        result = result[result["net_profit"].astype(float) <= float(pnl_max)]
    if min_hands is not None:
        result = result[result["hands_played"].astype(int) >= int(min_hands)]
    return result


def _filter_hands_data(
    df: pd.DataFrame,
    pnl_min: float | None,
    pnl_max: float | None,
    positions: list[str] | None,
    saw_flop_only: bool,
    showdown_only: bool,
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
    return result


# ---------------------------------------------------------------------------
# Table builder helpers
# ---------------------------------------------------------------------------
def _build_session_table(df: pd.DataFrame) -> html.Div:
    """Render a filtered sessions DataFrame as a clickable HTML table."""

    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_profit"])
        date_str = str(row["start_time"])[:10] if row["start_time"] else "—"
        stakes = f"{int(row['small_blind'])}/{int(row['big_blind'])}"
        rows.append(
            html.Tr(
                id={"type": "session-row", "index": int(row["id"])},
                style={"cursor": "pointer"},
                children=[
                    html.Td(date_str, style=_TD),
                    html.Td(stakes, style=_TD),
                    html.Td(int(row["hands_played"]), style=_TD),
                    html.Td(
                        f"{'+' if pnl >= 0 else ''}{pnl:,.0f}",
                        style={**_TD, **_pnl_style(pnl)},
                    ),
                ],
            )
        )
    header = html.Tr(
        [html.Th(h, style=_TH) for h in ("Date", "Stakes", "Hands", "Net P&L")]
    )
    return html.Div(
        html.Table(
            [html.Thead(header), html.Tbody(rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        )
        if rows
        else html.Div("No sessions match the current filters.", style={"color": "#888"})
    )


def _build_hand_table(df: pd.DataFrame) -> html.Div:
    """Render a filtered hands DataFrame as a clickable HTML table."""
    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_result"]) if row["net_result"] is not None else 0.0
        rows.append(
            html.Tr(
                id={"type": "hand-row", "index": int(row["id"])},
                style={"cursor": "pointer"},
                children=[
                    html.Td(str(row["source_hand_id"]), style=_TD),
                    html.Td(_render_cards(row["hole_cards"]), style=_TD),
                    html.Td(f"{float(row['total_pot']):,.0f}", style=_TD),
                    html.Td(
                        f"{'+' if pnl >= 0 else ''}{pnl:,.0f}",
                        style={**_TD, **_pnl_style(pnl)},
                    ),
                ],
            )
        )
    header = html.Tr(
        [html.Th(h, style=_TH) for h in ("Hand #", "Hole Cards", "Pot", "Net Result")]
    )
    return html.Div(
        html.Table(
            [html.Thead(header), html.Tbody(rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        )
        if rows
        else html.Div("No hands match the current filters.", style={"color": "#888"})
    )


# ---------------------------------------------------------------------------
# Level renderers
# ---------------------------------------------------------------------------
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
        {f"{int(r['small_blind'])}/{int(r['big_blind'])}" for _, r in df.iterrows()}
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
            html.Div(
                id="session-table-container",
                children=_build_session_table(df),
            ),
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
    return f"{date}  {int(row[1])}/{int(row[2])}"


def _render_hands(db_path: str, session_id: int) -> tuple[html.Div | str, str]:
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return "", ""

    from pokerhero.analysis.queries import get_hands

    conn = get_connection(db_path)
    try:
        df = get_hands(conn, session_id, player_id)
    finally:
        conn.close()

    session_label = _get_session_label(db_path, session_id)

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

    return (
        html.Div(
            [
                filter_bar,
                html.Div(
                    id="hand-table-container",
                    children=_build_hand_table(df),
                ),
                dcc.Store(id="hand-data-store", data=df.to_dict("records")),
            ]
        ),
        session_label,
    )


def _render_actions(db_path: str, hand_id: int) -> tuple[html.Div | str, str]:
    from pokerhero.analysis.queries import get_actions
    from pokerhero.analysis.stats import compute_ev

    hero_id = _get_hero_player_id(db_path)

    conn = get_connection(db_path)
    try:
        df = get_actions(conn, hand_id)
        hand_row = conn.execute(
            "SELECT source_hand_id, board_flop, board_turn, board_river"
            " FROM hands WHERE id = ?",
            (hand_id,),
        ).fetchone()
        hero_cards: str | None = None
        # Map player_id → hole_cards for EV calculation at all-in spots
        all_hole_cards: dict[int, str] = {}
        if hero_id is not None:
            hole_row = conn.execute(
                "SELECT hole_cards FROM hand_players"
                " WHERE hand_id = ? AND player_id = ?",
                (hand_id, hero_id),
            ).fetchone()
            if hole_row:
                hero_cards = hole_row[0]
        for row in conn.execute(
            "SELECT player_id, hole_cards FROM hand_players"
            " WHERE hand_id = ? AND hole_cards IS NOT NULL",
            (hand_id,),
        ).fetchall():
            all_hole_cards[int(row[0])] = row[1]
    finally:
        conn.close()

    if df.empty or hand_row is None:
        return html.Div("No actions found for this hand."), ""

    source_id, flop, turn, river = hand_row
    hand_label = f"Hand #{source_id}"

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
        actor = f"{username} ({position})" if position else username
        if action["is_hero"]:
            actor = f"🦸 {actor}"

        action_type = str(action["action_type"])
        amount = float(action["amount"])
        pot_before = float(action["pot_before"])
        amount_to_call = float(action["amount_to_call"])

        label = action_type
        if amount > 0:
            label += f"  {amount:,.0f}"
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
                sign = "+" if ev_val >= 0 else ""
                ev_cell = f"EV: {sign}{ev_val:,.0f}"

        street_rows.append(
            html.Tr(
                [
                    html.Td(
                        actor, style={**_TD, "width": "200px", "fontWeight": "600"}
                    ),
                    html.Td(label, style=_TD),
                    html.Td(
                        f"Pot: {pot_before:,.0f}",
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

    header_children: list[html.H3 | html.Div] = [
        html.H3(hand_label, style={"marginTop": "0"}),
        *([] if hero_row is None else [hero_row]),
        board_div,
    ]
    return (
        html.Div([*header_children, *sections]),
        hand_label,
    )


# ---------------------------------------------------------------------------
# Filter callbacks — update table containers when filter inputs change
# ---------------------------------------------------------------------------
@callback(
    Output("session-table-container", "children"),
    Input("session-filter-date-from", "value"),
    Input("session-filter-date-to", "value"),
    Input("session-filter-stakes", "value"),
    Input("session-filter-pnl-min", "value"),
    Input("session-filter-pnl-max", "value"),
    Input("session-filter-min-hands", "value"),
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
    data: list[dict[str, Any]] | None,
) -> html.Div:
    if not data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(data)
    filtered = _filter_sessions_data(
        df,
        date_from,
        date_to,
        stakes,
        pnl_min,
        pnl_max,
        int(min_hands) if min_hands is not None else None,
    )
    return _build_session_table(filtered)


@callback(
    Output("hand-table-container", "children"),
    Input("hand-filter-pnl-min", "value"),
    Input("hand-filter-pnl-max", "value"),
    Input("hand-filter-position", "value"),
    Input("hand-filter-flags", "value"),
    State("hand-data-store", "data"),
    prevent_initial_call=True,
)
def _apply_hand_filters(
    pnl_min: float | None,
    pnl_max: float | None,
    positions: list[str] | None,
    flags: list[str] | None,
    data: list[dict[str, Any]] | None,
) -> html.Div:
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
    )
    return _build_hand_table(filtered)
