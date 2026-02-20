"""Sessions page — drill-down view: session list → hand list."""

from __future__ import annotations

import dash
from dash import Input, Output, State, callback, dcc, html

from pokerhero.database.db import get_connection, get_setting, upsert_player

dash.register_page(__name__, path="/sessions", name="Review Sessions")  # type: ignore[no-untyped-call]

_TABLE_HEADER_STYLE = {
    "background": "#0074D9",
    "color": "#fff",
    "padding": "10px 12px",
    "textAlign": "left",
    "fontWeight": "600",
    "fontSize": "13px",
}
_CELL_STYLE = {
    "padding": "9px 12px",
    "borderBottom": "1px solid #eee",
    "fontSize": "13px",
    "cursor": "pointer",
}

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
            "← Back to Home", href="/", style={"fontSize": "13px", "color": "#0074D9"}
        ),
        html.Hr(),
        # Sessions table (populated by callback on page load)
        dcc.Loading(
            id="sessions-loading",
            children=html.Div(id="sessions-table"),
        ),
        html.Hr(style={"marginTop": "30px"}),
        # Hand list panel (populated when a session row is clicked)
        html.Div(id="hands-table"),
        # Hidden stores
        dcc.Store(id="selected-session-id"),
    ],
)


def _get_db_path() -> str:
    result: str = dash.get_app().server.config.get("DB_PATH", ":memory:")  # type: ignore[no-untyped-call]
    return result


def _get_hero_player_id(db_path: str) -> int | None:
    """Return the hero player_id from the settings table, or None if not set."""
    if db_path == ":memory:":
        return None
    conn = get_connection(db_path)
    try:
        username = get_setting(conn, "hero_username", default="")
        if not username:
            return None
        return upsert_player(conn, username)
    finally:
        conn.close()


def _pnl_style(value: float) -> dict[str, str]:
    color = "green" if value >= 0 else "red"
    return {"color": color, "fontWeight": "600"}


@callback(
    Output("sessions-table", "children"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _load_sessions(pathname: str) -> html.Div | html.Table | str:
    """Render the sessions table when navigating to /sessions."""
    if pathname != "/sessions":
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
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

    header = html.Tr(
        [
            html.Th("Date", style=_TABLE_HEADER_STYLE),
            html.Th("Stakes", style=_TABLE_HEADER_STYLE),
            html.Th("Hands", style=_TABLE_HEADER_STYLE),
            html.Th("Net P&L", style=_TABLE_HEADER_STYLE),
        ]
    )
    rows = []
    for _, row in df.iterrows():
        stakes = f"{int(row['small_blind'])}/{int(row['big_blind'])}"
        pnl = float(row["net_profit"])
        date_str = str(row["start_time"])[:10] if row["start_time"] else "—"
        rows.append(
            html.Tr(
                id={"type": "session-row", "index": int(row["id"])},
                style={"cursor": "pointer"},
                children=[
                    html.Td(date_str, style=_CELL_STYLE),
                    html.Td(stakes, style=_CELL_STYLE),
                    html.Td(int(row["hands_played"]), style=_CELL_STYLE),
                    html.Td(
                        f"{'+' if pnl >= 0 else ''}{pnl:,.0f}",
                        style={**_CELL_STYLE, **_pnl_style(pnl)},
                    ),
                ],
            )
        )
    return html.Table(
        [html.Thead(header), html.Tbody(rows)],
        style={"width": "100%", "borderCollapse": "collapse"},
    )


@callback(
    Output("selected-session-id", "data"),
    Input({"type": "session-row", "index": dash.ALL}, "n_clicks"),
    State({"type": "session-row", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def _select_session(
    n_clicks: list[int | None],
    row_ids: list[dict[str, int]],
) -> int | None:
    """Store the session_id when a session row is clicked."""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    import json

    parsed = json.loads(triggered_id)
    return int(parsed["index"])


@callback(
    Output("hands-table", "children"),
    Input("selected-session-id", "data"),
    prevent_initial_call=True,
)
def _load_hands(session_id: int | None) -> html.Div | str:
    """Render the hand list for the selected session."""
    if session_id is None:
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
    player_id = _get_hero_player_id(db_path)
    if player_id is None:
        return ""

    from pokerhero.analysis.queries import get_hands

    conn = get_connection(db_path)
    try:
        df = get_hands(conn, session_id, player_id)
    finally:
        conn.close()

    if df.empty:
        return html.Div("No hands found for this session.")

    header = html.Tr(
        [
            html.Th("Hand #", style=_TABLE_HEADER_STYLE),
            html.Th("Hole Cards", style=_TABLE_HEADER_STYLE),
            html.Th("Pot", style=_TABLE_HEADER_STYLE),
            html.Th("Net Result", style=_TABLE_HEADER_STYLE),
        ]
    )
    rows = []
    for _, row in df.iterrows():
        pnl = float(row["net_result"]) if row["net_result"] is not None else 0.0
        rows.append(
            html.Tr(
                [
                    html.Td(str(row["source_hand_id"]), style=_CELL_STYLE),
                    html.Td(str(row["hole_cards"] or "—"), style=_CELL_STYLE),
                    html.Td(f"{float(row['total_pot']):,.0f}", style=_CELL_STYLE),
                    html.Td(
                        f"{'+' if pnl >= 0 else ''}{pnl:,.0f}",
                        style={**_CELL_STYLE, **_pnl_style(pnl)},
                    ),
                ]
            )
        )

    return html.Div(
        [
            html.H3(f"Hands in Session #{session_id}", style={"marginTop": "0"}),
            html.Table(
                [html.Thead(header), html.Tbody(rows)],
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
        ]
    )
