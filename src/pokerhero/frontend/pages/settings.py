"""Settings page — hero username, data management, and CSV export."""

from __future__ import annotations

import io
import sqlite3

import dash
from dash import Input, Output, State, callback, dcc, html

from pokerhero.analysis.queries import get_export_data
from pokerhero.database.db import (
    clear_all_data,
    get_connection,
    get_setting,
    init_db,
    set_setting,
)

dash.register_page(__name__, path="/settings", name="Settings")  # type: ignore[no-untyped-call]

_SECTION_STYLE = {
    "marginBottom": "32px",
    "padding": "20px",
    "border": "1px solid #e0e0e0",
    "borderRadius": "8px",
    "background": "#fafafa",
}

_BUTTON_STYLE = {
    "padding": "10px 20px",
    "fontSize": "14px",
    "cursor": "pointer",
    "borderRadius": "6px",
    "border": "none",
}

layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "700px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H2("⚙️ Settings"),
        dcc.Link(
            "← Back to Home", href="/", style={"fontSize": "13px", "color": "#0074D9"}
        ),
        html.Hr(),
        # ── Hero Username ───────────────────────────────────────────────────
        html.Div(
            style=_SECTION_STYLE,
            children=[
                html.H3("🎯 Hero Username", style={"marginTop": 0}),
                html.P(
                    "Your PokerStars screen name. Used to identify your actions in "
                    "every hand history file you upload.",
                    style={"color": "#555", "fontSize": "14px"},
                ),
                dcc.Input(
                    id="settings-username",
                    type="text",
                    placeholder="e.g. jsalinas96",
                    debounce=True,
                    style={"width": "300px", "padding": "8px", "fontSize": "14px"},
                ),
                html.Span(
                    id="settings-username-saved",
                    style={"marginLeft": "10px", "color": "#888", "fontSize": "12px"},
                ),
            ],
        ),
        # ── Analysis Settings ────────────────────────────────────────────────
        html.Div(
            style=_SECTION_STYLE,
            children=[
                html.H3("📊 Analysis Settings", style={"marginTop": 0}),
                html.P(
                    "Tune the equity and classification parameters used when "
                    "analysing your session reports.",
                    style={"color": "#555", "fontSize": "14px"},
                ),
                html.Div(
                    style={"display": "grid", "gap": "16px"},
                    children=[
                        html.Div(
                            [
                                html.Label(
                                    "Equity sample count",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "display": "block",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.P(
                                    "Monte Carlo samples used to estimate equity "
                                    "(higher = more accurate but slower).",
                                    style={
                                        "fontSize": "12px",
                                        "color": "#777",
                                        "margin": "0 0 6px 0",
                                    },
                                ),
                                dcc.Input(
                                    id="settings-sample-count",
                                    type="number",
                                    min=500,
                                    max=10000,
                                    step=500,
                                    value=2000,
                                    style={
                                        "width": "130px",
                                        "padding": "6px",
                                        "fontSize": "14px",
                                    },
                                ),
                                html.Span(
                                    id="settings-sample-count-saved",
                                    style={
                                        "marginLeft": "10px",
                                        "color": "#888",
                                        "fontSize": "12px",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Lucky equity threshold (%)",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "display": "block",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.P(
                                    "Hero wins with equity below this %"
                                    " → flagged as Lucky.",
                                    style={
                                        "fontSize": "12px",
                                        "color": "#777",
                                        "margin": "0 0 6px 0",
                                    },
                                ),
                                dcc.Input(
                                    id="settings-lucky-threshold",
                                    type="number",
                                    min=10,
                                    max=49,
                                    step=1,
                                    value=40,
                                    style={
                                        "width": "130px",
                                        "padding": "6px",
                                        "fontSize": "14px",
                                    },
                                ),
                                html.Span(
                                    id="settings-lucky-threshold-saved",
                                    style={
                                        "marginLeft": "10px",
                                        "color": "#888",
                                        "fontSize": "12px",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Unlucky equity threshold (%)",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "display": "block",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.P(
                                    "Hero loses with equity above this %"
                                    " → flagged as Unlucky.",
                                    style={
                                        "fontSize": "12px",
                                        "color": "#777",
                                        "margin": "0 0 6px 0",
                                    },
                                ),
                                dcc.Input(
                                    id="settings-unlucky-threshold",
                                    type="number",
                                    min=51,
                                    max=90,
                                    step=1,
                                    value=60,
                                    style={
                                        "width": "130px",
                                        "padding": "6px",
                                        "fontSize": "14px",
                                    },
                                ),
                                html.Span(
                                    id="settings-unlucky-threshold-saved",
                                    style={
                                        "marginLeft": "10px",
                                        "color": "#888",
                                        "fontSize": "12px",
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Min hands for archetype badge",
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "display": "block",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.P(
                                    "Minimum hands observed before TAG/LAG/Nit/Fish "
                                    "badge is shown for an opponent.",
                                    style={
                                        "fontSize": "12px",
                                        "color": "#777",
                                        "margin": "0 0 6px 0",
                                    },
                                ),
                                dcc.Input(
                                    id="settings-min-hands",
                                    type="number",
                                    min=5,
                                    max=200,
                                    step=1,
                                    value=15,
                                    style={
                                        "width": "130px",
                                        "padding": "6px",
                                        "fontSize": "14px",
                                    },
                                ),
                                html.Span(
                                    id="settings-min-hands-saved",
                                    style={
                                        "marginLeft": "10px",
                                        "color": "#888",
                                        "fontSize": "12px",
                                    },
                                ),
                            ]
                        ),
                    ],
                ),
            ],
        ),
        # ── Data Management ─────────────────────────────────────────────────
        html.Div(
            style=_SECTION_STYLE,
            children=[
                html.H3("🗄️ Data Management", style={"marginTop": 0}),
                html.P(
                    "Export your data as CSV or wipe the database. "
                    "Settings (username) are preserved after a clear.",
                    style={"color": "#555", "fontSize": "14px"},
                ),
                html.Div(
                    style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
                    children=[
                        html.Button(
                            "📥 Export CSV",
                            id="export-csv-btn",
                            style={
                                **_BUTTON_STYLE,
                                "background": "#0074D9",
                                "color": "#fff",
                            },
                        ),
                        html.Button(
                            "🗑️ Clear Database",
                            id="clear-db-btn",
                            style={
                                **_BUTTON_STYLE,
                                "background": "#ff4136",
                                "color": "#fff",
                            },
                        ),
                    ],
                ),
                html.Div(
                    id="settings-action-msg",
                    style={"marginTop": "12px", "fontSize": "14px"},
                ),
                dcc.Download(id="settings-download"),
            ],
        ),
    ],
)


def _get_db_path() -> str:
    result: str = dash.get_app().server.config.get("DB_PATH", ":memory:")  # type: ignore[no-untyped-call]
    return result


def _open_conn(db_path: str) -> sqlite3.Connection:
    if db_path == ":memory:":
        return init_db(":memory:")
    return get_connection(db_path)


@callback(
    Output("settings-username", "value"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _load_username(pathname: str) -> str:
    """Pre-populate username input from settings table on page visit."""
    if pathname != "/settings":
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        return get_setting(conn, "hero_username", default="")
    finally:
        conn.close()


@callback(
    Output("settings-username-saved", "children"),
    Input("settings-username", "value"),
    prevent_initial_call=True,
)
def _save_username(value: str | None) -> str:
    """Persist hero username to settings table on change."""
    if not value or not value.strip():
        return ""
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        set_setting(conn, "hero_username", value.strip())
        conn.commit()
    finally:
        conn.close()
    return "✓ saved"


_ANALYSIS_SETTING_KEYS = {
    "settings-sample-count": ("equity_sample_count", "2000"),
    "settings-lucky-threshold": ("lucky_equity_threshold", "40"),
    "settings-unlucky-threshold": ("unlucky_equity_threshold", "60"),
    "settings-min-hands": ("min_hands_classification", "15"),
}


@callback(
    Output("settings-sample-count", "value"),
    Output("settings-lucky-threshold", "value"),
    Output("settings-unlucky-threshold", "value"),
    Output("settings-min-hands", "value"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _load_analysis_settings(pathname: str) -> tuple[int, int, int, int]:
    """Pre-populate analysis setting inputs from the settings table on page visit."""
    if pathname != "/settings":
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
    defaults = (2000, 40, 60, 15)
    if db_path == ":memory:":
        return defaults
    conn = get_connection(db_path)
    try:
        return (
            int(get_setting(conn, "equity_sample_count", default="2000")),
            int(get_setting(conn, "lucky_equity_threshold", default="40")),
            int(get_setting(conn, "unlucky_equity_threshold", default="60")),
            int(get_setting(conn, "min_hands_classification", default="15")),
        )
    finally:
        conn.close()


@callback(
    Output("settings-sample-count-saved", "children"),
    Input("settings-sample-count", "value"),
    prevent_initial_call=True,
)
def _save_sample_count(value: int | None) -> str:
    """Persist equity_sample_count to settings table on change."""
    if value is None:
        return ""
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        set_setting(conn, "equity_sample_count", str(int(value)))
        conn.commit()
    finally:
        conn.close()
    return "✓ saved"


@callback(
    Output("settings-lucky-threshold-saved", "children"),
    Input("settings-lucky-threshold", "value"),
    prevent_initial_call=True,
)
def _save_lucky_threshold(value: int | None) -> str:
    """Persist lucky_equity_threshold to settings table on change."""
    if value is None:
        return ""
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        set_setting(conn, "lucky_equity_threshold", str(int(value)))
        conn.commit()
    finally:
        conn.close()
    return "✓ saved"


@callback(
    Output("settings-unlucky-threshold-saved", "children"),
    Input("settings-unlucky-threshold", "value"),
    prevent_initial_call=True,
)
def _save_unlucky_threshold(value: int | None) -> str:
    """Persist unlucky_equity_threshold to settings table on change."""
    if value is None:
        return ""
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        set_setting(conn, "unlucky_equity_threshold", str(int(value)))
        conn.commit()
    finally:
        conn.close()
    return "✓ saved"


@callback(
    Output("settings-min-hands-saved", "children"),
    Input("settings-min-hands", "value"),
    prevent_initial_call=True,
)
def _save_min_hands(value: int | None) -> str:
    """Persist min_hands_classification to settings table on change."""
    if value is None:
        return ""
    db_path = _get_db_path()
    if db_path == ":memory:":
        return ""
    conn = get_connection(db_path)
    try:
        set_setting(conn, "min_hands_classification", str(int(value)))
        conn.commit()
    finally:
        conn.close()
    return "✓ saved"


@callback(
    Output("settings-download", "data"),
    Output("settings-action-msg", "children"),
    Input("export-csv-btn", "n_clicks"),
    Input("clear-db-btn", "n_clicks"),
    State("settings-username", "value"),
    prevent_initial_call=True,
)
def _handle_actions(
    export_clicks: int | None,
    clear_clicks: int | None,
    username: str | None,
) -> tuple[dict[str, object] | None, str | html.Span]:
    """Handle Export CSV and Clear Database button clicks."""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    db_path = _get_db_path()

    if triggered_id == "export-csv-btn":
        hero = (username or "").strip()
        if not hero:
            return None, html.Span(
                "⚠️ Set your hero username before exporting.", style={"color": "orange"}
            )
        if db_path == ":memory:":
            return None, html.Span("No data to export.", style={"color": "#888"})
        conn = get_connection(db_path)
        try:
            player_row = conn.execute(
                "SELECT id FROM players WHERE username = ?", (hero,)
            ).fetchone()
            if player_row is None:
                return None, html.Span(
                    f"⚠️ No data found for '{hero}'.", style={"color": "orange"}
                )
            df = get_export_data(conn, int(player_row[0]))
        finally:
            conn.close()
        if df.empty:
            return None, html.Span("No hands to export yet.", style={"color": "#888"})
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return (
            dcc.send_string(buf.getvalue(), "pokerhero_export.csv"),  # type: ignore[attr-defined, no-untyped-call]
            html.Span("✅ Export ready — downloading…", style={"color": "green"}),
        )

    if triggered_id == "clear-db-btn":
        if db_path == ":memory:":
            return None, html.Span("Nothing to clear.", style={"color": "#888"})
        conn = get_connection(db_path)
        try:
            clear_all_data(conn)
        finally:
            conn.close()
        return None, html.Span(
            "✅ Database cleared. Settings preserved.", style={"color": "green"}
        )

    raise dash.exceptions.PreventUpdate
