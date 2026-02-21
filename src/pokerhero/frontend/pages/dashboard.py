"""Dashboard page — hero performance overview."""

from __future__ import annotations

import dash
from dash import Input, Output, callback, dcc, html

from pokerhero.database.db import get_connection, get_setting, upsert_player

dash.register_page(__name__, path="/dashboard", name="Overall Stats")  # type: ignore[no-untyped-call]

_PERIOD_OPTIONS = [
    {"label": "7 days", "value": "7d"},
    {"label": "1 month", "value": "1m"},
    {"label": "1 year", "value": "1y"},
    {"label": "All time", "value": "all"},
]

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "1000px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H2("📊 Overall Stats"),
        dcc.Link(
            "← Back to Home",
            href="/",
            style={"fontSize": "13px", "color": "#0074D9"},
        ),
        html.Hr(),
        html.Div(
            [
                html.Span(
                    "Period: ",
                    style={"fontSize": "13px", "color": "#555", "marginRight": "8px"},
                ),
                dcc.RadioItems(
                    id="dashboard-period",
                    options=_PERIOD_OPTIONS,
                    value="all",
                    inline=True,
                    inputStyle={"marginRight": "4px"},
                    labelStyle={"marginRight": "16px", "fontSize": "13px"},
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        dcc.Loading(
            html.Div(id="dashboard-content"),
        ),
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


def _period_to_since_date(period: str) -> str | None:
    """Convert a period key to an ISO date string cutoff, or None for all-time."""
    from datetime import date, timedelta

    today = date.today()
    if period == "7d":
        return (today - timedelta(days=7)).isoformat()
    if period == "1m":
        return (today - timedelta(days=30)).isoformat()
    if period == "1y":
        return (today - timedelta(days=365)).isoformat()
    return None  # "all"


def _kpi_card(label: str, value: str, color: str = "#333") -> html.Div:
    return html.Div(
        [
            html.Div(
                value,
                style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": color,
                    "lineHeight": "1.2",
                },
            ),
            html.Div(
                label,
                style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
            ),
        ],
        style={
            "background": "#f8f9fa",
            "border": "1px solid #e0e0e0",
            "borderRadius": "8px",
            "padding": "16px 20px",
            "minWidth": "130px",
            "textAlign": "center",
        },
    )


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------
@callback(
    Output("dashboard-content", "children"),
    Input("_pages_location", "pathname"),
    Input("dashboard-period", "value"),
    prevent_initial_call=False,
)
def _render(pathname: str, period: str) -> html.Div | str:
    if pathname != "/dashboard":
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

    since_date = _period_to_since_date(period)

    from pokerhero.analysis.queries import (
        get_hero_actions,
        get_hero_hand_players,
        get_hero_opportunity_actions,
        get_hero_timeline,
        get_sessions,
    )
    from pokerhero.analysis.stats import (
        aggression_factor,
        cbet_pct,
        pfr_pct,
        three_bet_pct,
        total_profit,
        vpip_pct,
        win_rate_bb100,
    )

    conn = get_connection(db_path)
    try:
        hp_df = get_hero_hand_players(conn, player_id, since_date=since_date)
        sessions_df = get_sessions(conn, player_id, since_date=since_date)
        timeline_df = get_hero_timeline(conn, player_id, since_date=since_date)
        actions_df = get_hero_actions(conn, player_id, since_date=since_date)
        opp_df = get_hero_opportunity_actions(conn, player_id, since_date=since_date)
    finally:
        conn.close()

    if hp_df.empty:
        return html.Div("No hands found. Upload a hand history file to get started.")

    # --- Scalar KPIs ---
    pnl = total_profit(hp_df)
    win_rate = win_rate_bb100(hp_df)
    n_sessions = len(sessions_df)
    n_hands = len(hp_df)
    vpip = vpip_pct(hp_df) * 100
    pfr = pfr_pct(hp_df) * 100

    pnl_str = f"{'+' if pnl >= 0 else ''}{pnl:,.0f}"
    pnl_color = "green" if pnl >= 0 else "red"
    wr_str = f"{'+' if win_rate >= 0 else ''}{win_rate:.1f} bb/100"
    wr_color = "green" if win_rate >= 0 else "red"

    kpi_section = html.Div(
        id="kpi-section",
        style={
            "display": "flex",
            "gap": "12px",
            "flexWrap": "wrap",
            "marginBottom": "24px",
        },
        children=[
            _kpi_card("Total P&L", pnl_str, color=pnl_color),
            _kpi_card("Win Rate", wr_str, color=wr_color),
            _kpi_card("Sessions", str(n_sessions)),
            _kpi_card("Hands Played", str(n_hands)),
            _kpi_card("VPIP", f"{vpip:.1f}%"),
            _kpi_card("PFR", f"{pfr:.1f}%"),
        ],
    )

    # --- Bankroll graph ---
    import plotly.graph_objects as go

    cumulative = timeline_df["net_result"].cumsum()
    fig = go.Figure(
        go.Scatter(
            x=list(range(1, len(cumulative) + 1)),
            y=cumulative.tolist(),
            mode="lines",
            line={"color": "#0074D9", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(0,116,217,0.08)",
            hovertemplate="Hand %{x}<br>Cumulative P&L: %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=None,
        xaxis_title="Hands played",
        yaxis_title="Cumulative P&L",
        margin={"l": 50, "r": 20, "t": 20, "b": 40},
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        xaxis={"showgrid": True, "gridcolor": "#eee"},
        yaxis={"showgrid": True, "gridcolor": "#eee", "zeroline": True},
        height=280,
    )
    bankroll_section = html.Div(
        [
            html.H4(
                "Bankroll Graph",
                style={"marginBottom": "8px", "color": "#333"},
            ),
            dcc.Graph(
                id="bankroll-graph",
                figure=fig,
                config={"displayModeBar": False},
            ),
        ],
        style={"marginBottom": "28px"},
    )

    # --- Positional stats table ---
    _TH = {
        "background": "#0074D9",
        "color": "#fff",
        "padding": "8px 12px",
        "textAlign": "left",
        "fontWeight": "600",
        "fontSize": "13px",
    }
    _TD = {
        "padding": "8px 12px",
        "borderBottom": "1px solid #eee",
        "fontSize": "13px",
    }

    position_order = ["BTN", "CO", "MP", "MP+1", "UTG", "UTG+1", "SB", "BB"]
    pos_rows: list[html.Tr] = []

    for pos in position_order:
        pos_hp = hp_df[hp_df["position"] == pos]
        if pos_hp.empty:
            continue
        pos_actions = actions_df[actions_df["position"] == pos]
        pos_hand_ids = set(pos_hp["hand_id"].tolist())
        pos_opp = opp_df[opp_df["hand_id"].isin(pos_hand_ids)]
        pos_vpip = vpip_pct(pos_hp) * 100
        pos_pfr = pfr_pct(pos_hp) * 100
        pos_3bet = three_bet_pct(pos_opp) * 100
        pos_cbet = cbet_pct(pos_opp) * 100
        pos_af = aggression_factor(pos_actions)
        pos_pnl = total_profit(pos_hp)
        af_str = f"{pos_af:.2f}" if pos_af != float("inf") else "∞"
        pnl_style = {**_TD, "color": "green" if pos_pnl >= 0 else "red"}
        pos_rows.append(
            html.Tr(
                [
                    html.Td(pos, style={**_TD, "fontWeight": "600"}),
                    html.Td(len(pos_hp), style=_TD),
                    html.Td(f"{pos_vpip:.1f}%", style=_TD),
                    html.Td(f"{pos_pfr:.1f}%", style=_TD),
                    html.Td(f"{pos_3bet:.1f}%", style=_TD),
                    html.Td(f"{pos_cbet:.1f}%", style=_TD),
                    html.Td(af_str, style=_TD),
                    html.Td(
                        f"{'+' if pos_pnl >= 0 else ''}{pos_pnl:,.0f}",
                        style=pnl_style,
                    ),
                ]
            )
        )

    positional_section = html.Div(
        id="positional-stats",
        children=[
            html.H4(
                "Positional Stats",
                style={"marginBottom": "8px", "color": "#333"},
            ),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(h, style=_TH)
                                for h in (
                                    "Position",
                                    "Hands",
                                    "VPIP%",
                                    "PFR%",
                                    "3-Bet%",
                                    "C-Bet%",
                                    "AF",
                                    "Net P&L",
                                )
                            ]
                        )
                    ),
                    html.Tbody(pos_rows),
                ],
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
        ],
    )

    return html.Div([kpi_section, bankroll_section, positional_section])
