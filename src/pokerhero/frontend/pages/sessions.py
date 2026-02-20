"""Sessions page — breadcrumb drill-down: Sessions → Hands → Actions."""

from __future__ import annotations

import json
from typing import NotRequired, TypedDict

import dash
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
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
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
# Renderer — reacts to state + page navigation
# ---------------------------------------------------------------------------
@callback(
    Output("drill-down-content", "children"),
    Output("breadcrumb", "children"),
    Input("drill-down-state", "data"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _render(
    state: _DrillDownState | None,
    pathname: str,
) -> tuple[html.Div | str, html.Div]:
    if pathname != "/sessions":
        raise dash.exceptions.PreventUpdate

    if state is None:
        state = _DrillDownState(level="sessions")
    level = state.get("level", "sessions")

    db_path = _get_db_path()

    if level == "sessions":
        return _render_sessions(db_path), _breadcrumb("sessions")

    session_id = int(state.get("session_id") or 0)
    if level == "hands":
        content, label = _render_hands(db_path, session_id)
        return content, _breadcrumb("hands", session_label=label, session_id=session_id)

    hand_id = int(state.get("hand_id") or 0)
    session_label = state.get("session_label") or f"Session #{session_id}"
    content, hand_label = _render_actions(db_path, hand_id)
    return content, _breadcrumb(
        "actions",
        session_label=session_label,
        session_id=session_id,
        hand_label=hand_label,
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
    )


def _render_hands(db_path: str, session_id: int) -> tuple[html.Div | str, str]:
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return "", ""

    from pokerhero.analysis.queries import get_hands

    conn = get_connection(db_path)
    try:
        df = get_hands(conn, session_id, player_id)
        sess_row = conn.execute(
            "SELECT start_time, small_blind, big_blind FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()

    session_label = ""
    if sess_row:
        date = str(sess_row[0])[:10] if sess_row[0] else "—"
        session_label = f"{date}  {int(sess_row[1])}/{int(sess_row[2])}"

    if df.empty:
        return html.Div("No hands found for this session."), session_label

    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_result"]) if row["net_result"] is not None else 0.0
        rows.append(
            html.Tr(
                id={"type": "hand-row", "index": int(row["id"])},
                style={"cursor": "pointer"},
                children=[
                    html.Td(str(row["source_hand_id"]), style=_TD),
                    html.Td(str(row["hole_cards"] or "—"), style=_TD),
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
    return (
        html.Div(
            html.Table(
                [html.Thead(header), html.Tbody(rows)],
                style={"width": "100%", "borderCollapse": "collapse"},
            )
        ),
        session_label,
    )


def _render_actions(db_path: str, hand_id: int) -> tuple[html.Div | str, str]:
    from pokerhero.analysis.queries import get_actions

    conn = get_connection(db_path)
    try:
        df = get_actions(conn, hand_id)
        hand_row = conn.execute(
            "SELECT source_hand_id, board_flop, board_turn, board_river"
            " FROM hands WHERE id = ?",
            (hand_id,),
        ).fetchone()
    finally:
        conn.close()

    if df.empty or hand_row is None:
        return html.Div("No actions found for this hand."), ""

    source_id, flop, turn, river = hand_row
    board_parts = [b for b in (flop, turn, river) if b]
    board_str = "  |  ".join(board_parts) if board_parts else "—"
    hand_label = f"Hand #{source_id}"

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

        extra = ""
        if action["is_hero"] and amount_to_call > 0:
            pot_odds = amount_to_call / (pot_before + amount_to_call) * 100
            extra = f"Pot odds: {pot_odds:.1f}%"
        if action["spr"] is not None:
            spr_str = f"SPR: {float(action['spr']):.2f}"
            extra = f"{spr_str}  |  {extra}" if extra else spr_str

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
                ]
            )
        )

    if current_street is not None:
        sections.append(_flush(current_street, street_rows))

    return (
        html.Div(
            [
                html.H3(hand_label, style={"marginTop": "0"}),
                html.P(
                    f"Board: {board_str}",
                    style={"color": "#555", "marginBottom": "12px"},
                ),
                *sections,
            ]
        ),
        hand_label,
    )
