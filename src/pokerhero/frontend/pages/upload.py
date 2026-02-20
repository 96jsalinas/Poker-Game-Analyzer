"""Upload page — drag-and-drop hand history ingestion."""

from __future__ import annotations

import sqlite3

import dash
from dash import Input, Output, State, callback, dcc, html

from pokerhero.database.db import get_connection, get_setting, init_db, set_setting
from pokerhero.frontend.upload_handler import handle_upload

dash.register_page(__name__, path="/upload", name="Upload Files")  # type: ignore[no-untyped-call]

layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "800px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H2("📤 Upload Hand History"),
        dcc.Link(
            "← Back to Home", href="/", style={"fontSize": "13px", "color": "#0074D9"}
        ),
        html.Hr(),
        html.H3("1. Your PokerStars username"),
        dcc.Input(
            id="hero-username",
            type="text",
            placeholder="e.g. jsalinas96",
            debounce=True,
            style={"width": "300px", "padding": "8px", "fontSize": "14px"},
        ),
        html.Span(
            id="username-saved-indicator",
            style={"marginLeft": "10px", "color": "#888", "fontSize": "12px"},
        ),
        html.Br(),
        html.Br(),
        html.H3("2. Upload hand history files (.txt)"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                [
                    "Drag and drop or ",
                    html.A(
                        "click to select",
                        style={"cursor": "pointer", "color": "#0074D9"},
                    ),
                    html.Br(),
                    html.Small(
                        "PokerStars .txt hand history files",
                        style={"color": "#888"},
                    ),
                ]
            ),
            multiple=True,
            style={
                "width": "100%",
                "height": "100px",
                "lineHeight": "100px",
                "borderWidth": "2px",
                "borderStyle": "dashed",
                "borderRadius": "8px",
                "borderColor": "#aaa",
                "textAlign": "center",
                "cursor": "pointer",
            },
        ),
        html.Br(),
        html.Div(id="upload-output"),
    ],
)


def _get_db_path() -> str:
    """Return the configured DB path from the running Dash app's server config."""
    result: str = dash.get_app().server.config.get("DB_PATH", ":memory:")  # type: ignore[no-untyped-call]
    return result


def _open_conn(db_path: str) -> sqlite3.Connection:
    """Open (or initialise) a DB connection appropriate for db_path."""
    if db_path == ":memory:":
        return init_db(":memory:")
    return get_connection(db_path)


@callback(
    Output("hero-username", "value"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _load_username(pathname: str) -> str:
    """Pre-populate the username input from the settings table on page visit."""
    if pathname != "/upload":
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
    Output("username-saved-indicator", "children"),
    Input("hero-username", "value"),
    prevent_initial_call=True,
)
def _save_username(value: str | None) -> str:
    """Persist the username to the settings table whenever it changes."""
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


@callback(
    Output("upload-output", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("hero-username", "value"),
    prevent_initial_call=True,
)
def _process_upload(
    contents_list: list[str] | None,
    filenames: list[str] | None,
    hero_username: str | None,
) -> list[html.Div] | html.Div | str:
    if not contents_list:
        return ""
    if not hero_username or not hero_username.strip():
        return html.Div(
            "⚠️ Please enter your PokerStars username before uploading.",
            style={"color": "orange"},
        )

    conn = _open_conn(_get_db_path())
    messages = []
    for content, filename in zip(contents_list, filenames or []):
        try:
            msg = handle_upload(content, filename, hero_username.strip(), conn)
            color = "green" if msg.startswith("✅") else "orange"
        except Exception as exc:  # noqa: BLE001
            msg = f"❌ {filename} — unexpected error: {exc}"
            color = "red"
        messages.append(html.Div(msg, style={"color": color, "marginBottom": "6px"}))

    conn.close()
    return messages
