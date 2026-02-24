"""Dashboard page — hero performance overview."""

from __future__ import annotations

import dash
import pandas as pd
from dash import Input, Output, callback, dcc, html

from pokerhero.analysis.targets import (
    canonical_position,
    read_target_settings,
    traffic_light,
)
from pokerhero.database.db import get_connection, get_setting, upsert_player

dash.register_page(__name__, path="/dashboard", name="Overall Stats")  # type: ignore[no-untyped-call]

_PERIOD_OPTIONS = [
    {"label": "7 days", "value": "7d"},
    {"label": "1 month", "value": "1m"},
    {"label": "1 year", "value": "1y"},
    {"label": "All time", "value": "all"},
]
_CURRENCY_OPTIONS = [
    {"label": "All", "value": "all"},
    {"label": "Real Money", "value": "real"},
    {"label": "Play Money", "value": "play"},
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
            style={"marginBottom": "8px"},
        ),
        html.Div(
            [
                html.Span(
                    "Game type: ",
                    style={"fontSize": "13px", "color": "#555", "marginRight": "8px"},
                ),
                dcc.RadioItems(
                    id="dashboard-currency",
                    options=_CURRENCY_OPTIONS,
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
# Shared style constants
# ---------------------------------------------------------------------------
_TH: dict[str, str] = {
    "background": "#0074D9",
    "color": "#fff",
    "padding": "8px 12px",
    "textAlign": "left",
    "fontWeight": "600",
    "fontSize": "13px",
}
_TD: dict[str, str] = {
    "padding": "8px 12px",
    "borderBottom": "1px solid #eee",
    "fontSize": "13px",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_blind(v: object) -> str:
    """Format a blind/stake value: integer if whole, else strip trailing zeros."""
    return f"{float(v):g}"  # type: ignore[arg-type]


def _fmt_pnl(pnl: float) -> str:
    """Format a P&L value with leading sign; no trailing decimal zeros."""
    sign = "+" if pnl >= 0 else ""
    return f"{sign}{pnl:,.6g}"


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


_STAT_TOOLTIPS: dict[str, str] = {
    "VPIP%": (
        "Voluntarily Put In Pot — % of hands where hero called or raised "
        "pre-flop. Excludes posting blinds."
    ),
    "PFR%": ("Pre-Flop Raise — % of all hands where hero raised or 3-bet pre-flop."),
    "3-Bet%": (
        "3-Bet % — % of opportunities where hero re-raised a pre-flop opener. "
        "Only counts hands where a raise had already been made before hero's action."
    ),
    "C-Bet%": (
        "Continuation Bet % — % of flops where hero bet after being the last "
        "pre-flop aggressor."
    ),
    "AF": (
        "Aggression Factor — (Bets + Raises) ÷ Calls, post-flop streets only. "
        "Higher = more aggressive. ∞ means hero never called post-flop."
    ),
}


def _stat_header(label: str, tooltip: str) -> html.Th:
    """Return a table header cell with a hoverable ⓘ tooltip.

    The tooltip is rendered via the CSS class 'stat-help' defined in
    assets/tooltips.css, using a CSS content: attr(data-tip) pattern.

    Args:
        label: Column header text.
        tooltip: Explanatory text shown on hover.

    Returns:
        html.Th with the label and a small '?' badge that reveals the tooltip.
    """
    return html.Th(
        [
            label,
            html.Span(
                ["?", html.Span(tooltip, className="stat-tip")],
                className="stat-help",
            ),
        ],
        style=_TH,
    )


_TL_COLORS: dict[str, str] = {
    "green": "#d4edda",
    "yellow": "#fff3cd",
    "red": "#f8d7da",
}


def _kpi_card(
    label: str,
    value: str,
    color: str = "#333",
) -> html.Div:
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


def _build_vpip_pfr_chart(vpip: float, pfr: float) -> html.Div:
    """Build the VPIP/PFR gap chart as a stacked horizontal bar.

    The bar is split into three segments that always sum to 100%:
      - PFR%:           how often hero raised preflop           (green)
      - Call/limp gap:  VPIP% − PFR% (called but did not raise) (steel blue)
      - Fold%:          1 − VPIP% (folded or checked blind)     (light gray)

    The visual gap between the PFR and VPIP bars gives an instant read of
    how passive or aggressive the hero's pre-flop game is.

    Args:
        vpip: VPIP as a decimal in [0.0, 1.0].
        pfr: PFR as a decimal in [0.0, 1.0]. Clamped to vpip if pfr > vpip.

    Returns:
        html.Div containing a dcc.Graph with id='vpip-pfr-chart'.
    """
    import plotly.graph_objects as go

    pfr = min(pfr, vpip)  # guard: PFR can never exceed VPIP
    pfr_pct = pfr * 100
    gap_pct = (vpip - pfr) * 100
    fold_pct = (1.0 - vpip) * 100

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[pfr_pct],
            y=[""],
            name=f"PFR {pfr_pct:.1f}%",
            orientation="h",
            marker_color="#2ECC40",
            text=f"PFR {pfr_pct:.1f}%",
            textposition="inside",
            insidetextanchor="middle",
        )
    )
    fig.add_trace(
        go.Bar(
            x=[gap_pct],
            y=[""],
            name=f"Call/Limp {gap_pct:.1f}%",
            orientation="h",
            marker_color="#7FBADC",
            text=f"Call/Limp {gap_pct:.1f}%" if gap_pct >= 4 else "",
            textposition="inside",
            insidetextanchor="middle",
        )
    )
    fig.add_trace(
        go.Bar(
            x=[fold_pct],
            y=[""],
            name=f"Fold {fold_pct:.1f}%",
            orientation="h",
            marker_color="#e0e0e0",
            text=f"Fold {fold_pct:.1f}%" if fold_pct >= 6 else "",
            textposition="inside",
            insidetextanchor="middle",
        )
    )
    fig.update_layout(
        barmode="stack",
        title=None,
        xaxis={"range": [0, 100], "showticklabels": False, "showgrid": False},
        yaxis={"showticklabels": False},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.6,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11},
        },
        height=80,
    )
    return html.Div(
        [
            html.H4(
                "VPIP / PFR Gap",
                style={"marginBottom": "4px", "color": "#333"},
            ),
            dcc.Graph(
                id="vpip-pfr-chart",
                figure=fig,
                config={"displayModeBar": False},
            ),
        ],
        style={"marginBottom": "28px"},
    )


def _build_highlights(
    hp_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
) -> html.Div:
    """Build the Highlights card showing four peak performance figures.

    Each card is a clickable link: session cards navigate to the hand list
    for that session; hand cards navigate directly to the action view.

    Args:
        hp_df: DataFrame from get_hero_hand_players; requires net_result,
            hole_cards, hand_id, and session_id columns.
        sessions_df: DataFrame from get_sessions; requires net_profit,
            start_time, small_blind, big_blind, and id columns.

    Returns:
        html.Div with id='highlights-section'.
    """
    if hp_df.empty or sessions_df.empty:
        return html.Div(
            "Not enough data for highlights.",
            id="highlights-section",
            style={"color": "#888", "fontSize": "13px"},
        )

    _CARD_STYLE = {
        "background": "#f8f9fa",
        "border": "1px solid #e0e0e0",
        "borderRadius": "8px",
        "padding": "14px 18px",
        "minWidth": "140px",
        "textAlign": "center",
    }

    def _hl_card(label: str, value: str, sub: str, color: str, href: str) -> dcc.Link:
        return dcc.Link(
            html.Div(
                [
                    html.Div(
                        value,
                        style={
                            "fontSize": "22px",
                            "fontWeight": "700",
                            "color": color,
                            "lineHeight": "1.2",
                        },
                    ),
                    html.Div(
                        sub,
                        style={"fontSize": "11px", "color": "#999", "marginTop": "2px"},
                    ),
                    html.Div(
                        label,
                        style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                    ),
                ],
                style=_CARD_STYLE,
            ),
            href=href,
            style={"textDecoration": "none", "color": "inherit"},
        )

    best_hand = hp_df.loc[hp_df["net_result"].idxmax()]
    worst_hand = hp_df.loc[hp_df["net_result"].idxmin()]
    best_sess = sessions_df.loc[sessions_df["net_profit"].idxmax()]
    worst_sess = sessions_df.loc[sessions_df["net_profit"].idxmin()]

    best_hand_pnl = float(best_hand["net_result"])
    worst_hand_pnl = float(worst_hand["net_result"])
    best_sess_pnl = float(best_sess["net_profit"])
    worst_sess_pnl = float(worst_sess["net_profit"])

    best_hand_cards = best_hand.get("hole_cards") or "—"
    worst_hand_cards = worst_hand.get("hole_cards") or "—"
    best_sess_label = (
        f"{str(best_sess['start_time'])[:10]} · "
        f"{_fmt_blind(best_sess['small_blind'])}/{_fmt_blind(best_sess['big_blind'])}"
    )
    worst_sess_label = (
        f"{str(worst_sess['start_time'])[:10]} · "
        f"{_fmt_blind(worst_sess['small_blind'])}/{_fmt_blind(worst_sess['big_blind'])}"
    )

    best_hand_url = (
        f"/sessions?session_id={int(best_hand['session_id'])}"
        f"&hand_id={int(best_hand['hand_id'])}"
    )
    worst_hand_url = (
        f"/sessions?session_id={int(worst_hand['session_id'])}"
        f"&hand_id={int(worst_hand['hand_id'])}"
    )
    best_sess_url = f"/sessions?session_id={int(best_sess['id'])}"
    worst_sess_url = f"/sessions?session_id={int(worst_sess['id'])}"

    cards = [
        _hl_card(
            "Best Hand",
            _fmt_pnl(best_hand_pnl),
            best_hand_cards if isinstance(best_hand_cards, str) else "—",
            "green",
            best_hand_url,
        ),
        _hl_card(
            "Worst Hand",
            _fmt_pnl(worst_hand_pnl),
            worst_hand_cards if isinstance(worst_hand_cards, str) else "—",
            "red",
            worst_hand_url,
        ),
        _hl_card(
            "Best Session",
            _fmt_pnl(best_sess_pnl),
            best_sess_label,
            "green",
            best_sess_url,
        ),
        _hl_card(
            "Worst Session",
            _fmt_pnl(worst_sess_pnl),
            worst_sess_label,
            "red",
            worst_sess_url,
        ),
    ]

    return html.Div(
        id="highlights-section",
        children=[
            html.H4("Highlights", style={"marginBottom": "8px", "color": "#333"}),
            html.Div(
                cards,
                style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------
@callback(
    Output("dashboard-content", "children"),
    Input("_pages_location", "pathname"),
    Input("dashboard-period", "value"),
    Input("dashboard-currency", "value"),
    prevent_initial_call=False,
)
def _render(pathname: str, period: str, currency: str) -> html.Div | str:
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
    currency_type = None if currency == "all" else currency

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
        hp_df = get_hero_hand_players(
            conn, player_id, since_date=since_date, currency_type=currency_type
        )
        sessions_df = get_sessions(
            conn, player_id, since_date=since_date, currency_type=currency_type
        )
        timeline_df = get_hero_timeline(
            conn, player_id, since_date=since_date, currency_type=currency_type
        )
        actions_df = get_hero_actions(
            conn, player_id, since_date=since_date, currency_type=currency_type
        )
        opp_df = get_hero_opportunity_actions(
            conn, player_id, since_date=since_date, currency_type=currency_type
        )
        tl_targets = read_target_settings(conn)
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
    three_bet = three_bet_pct(opp_df) * 100

    pnl_str = _fmt_pnl(pnl)
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
            _kpi_card("3-Bet", f"{three_bet:.1f}%"),
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
            hovertemplate="Hand %{x}<br>Cumulative P&L: %{y:,.4g}<extra></extra>",
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

        # Traffic-light colours for VPIP, PFR, 3-Bet
        canon = canonical_position(pos)
        vpip_b = tl_targets.get(("vpip", canon), tl_targets[("vpip", "utg")])
        pfr_b = tl_targets.get(("pfr", canon), tl_targets[("pfr", "utg")])
        tbet_b = tl_targets.get(("3bet", canon), tl_targets[("3bet", "utg")])
        tl_color = _TL_COLORS[
            traffic_light(
                pos_vpip,
                vpip_b["green_min"],
                vpip_b["green_max"],
                vpip_b["yellow_min"],
                vpip_b["yellow_max"],
            )
        ]
        pfr_tl_color = _TL_COLORS[
            traffic_light(
                pos_pfr,
                pfr_b["green_min"],
                pfr_b["green_max"],
                pfr_b["yellow_min"],
                pfr_b["yellow_max"],
            )
        ]
        tbet_tl_color = _TL_COLORS[
            traffic_light(
                pos_3bet,
                tbet_b["green_min"],
                tbet_b["green_max"],
                tbet_b["yellow_min"],
                tbet_b["yellow_max"],
            )
        ]
        pos_rows.append(
            html.Tr(
                [
                    html.Td(pos, style={**_TD, "fontWeight": "600"}),
                    html.Td(len(pos_hp), style=_TD),
                    html.Td(
                        f"{pos_vpip:.1f}%", style={**_TD, "backgroundColor": tl_color}
                    ),
                    html.Td(
                        f"{pos_pfr:.1f}%",
                        style={**_TD, "backgroundColor": pfr_tl_color},
                    ),
                    html.Td(
                        f"{pos_3bet:.1f}%",
                        style={**_TD, "backgroundColor": tbet_tl_color},
                    ),
                    html.Td(f"{pos_cbet:.1f}%", style=_TD),
                    html.Td(af_str, style=_TD),
                    html.Td(
                        _fmt_pnl(pos_pnl),
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
                                html.Th("Position", style=_TH),
                                html.Th("Hands", style=_TH),
                                _stat_header("VPIP%", _STAT_TOOLTIPS["VPIP%"]),
                                _stat_header("PFR%", _STAT_TOOLTIPS["PFR%"]),
                                _stat_header("3-Bet%", _STAT_TOOLTIPS["3-Bet%"]),
                                _stat_header("C-Bet%", _STAT_TOOLTIPS["C-Bet%"]),
                                _stat_header("AF", _STAT_TOOLTIPS["AF"]),
                                html.Th("Net P&L", style=_TH),
                            ]
                        )
                    ),
                    html.Tbody(pos_rows),
                ],
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
        ],
    )

    return html.Div(
        [
            kpi_section,
            bankroll_section,
            _build_vpip_pfr_chart(vpip / 100, pfr / 100),
            positional_section,
            _build_highlights(hp_df, sessions_df),
        ]
    )
