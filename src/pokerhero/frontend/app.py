"""Dash application factory and layout for PokerHero Analyzer.

Use create_app() to build the app instance. run.py calls create_app()
with the configured DB path and starts the development server.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import dash
from dash import Input, Output, State, dcc, html

from pokerhero.database.db import get_connection, init_db
from pokerhero.frontend.upload_handler import handle_upload


def create_app(db_path: str | Path = "data/pokerhero.db") -> dash.Dash:
    """Create and configure the Dash application.

    Args:
        db_path: Path to the SQLite database file, or ':memory:' for tests.

    Returns:
        Configured Dash app instance (not yet running).
    """
    db_path = Path(db_path) if db_path != ":memory:" else ":memory:"

    app = dash.Dash(__name__, title="PokerHero Analyzer")

    app.layout = html.Div(
        style={"fontFamily": "sans-serif", "maxWidth": "800px", "margin": "40px auto", "padding": "0 20px"},
        children=[
            html.H1("♠ PokerHero Analyzer"),
            html.Hr(),

            # --- Hero username ---
            html.H3("1. Enter your PokerStars username"),
            dcc.Input(
                id="hero-username",
                type="text",
                placeholder="e.g. jsalinas96",
                debounce=True,
                style={"width": "300px", "padding": "8px", "fontSize": "14px"},
            ),

            html.Br(), html.Br(),

            # --- File upload ---
            html.H3("2. Upload hand history files (.txt)"),
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    "Drag and drop or ",
                    html.A("click to select", style={"cursor": "pointer", "color": "#0074D9"}),
                    html.Br(),
                    html.Small("PokerStars .txt hand history files", style={"color": "#888"}),
                ]),
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

            # --- Results ---
            html.Div(id="upload-output"),
        ],
    )

    @app.callback(
        Output("upload-output", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        State("hero-username", "value"),
        prevent_initial_call=True,
    )
    def process_upload(
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

        conn: sqlite3.Connection = (
            get_connection(db_path)
            if db_path != ":memory:"
            else init_db(":memory:")
        )

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

    return app
