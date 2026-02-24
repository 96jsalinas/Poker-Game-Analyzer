"""Dash application factory for PokerHero Analyzer.

Use create_app() to build the app instance. run.py calls create_app()
with the configured DB path and starts the development server.
"""

from __future__ import annotations

from pathlib import Path

import dash
from dash import Input, Output, State, dcc, html

from pokerhero.database.db import init_db


def create_app(db_path: str | Path = "data/pokerhero.db") -> dash.Dash:
    """Create and configure the Dash application.

    Args:
        db_path: Path to the SQLite database file, or ':memory:' for tests.

    Returns:
        Configured Dash app instance (not yet running).
    """
    db_path = Path(db_path) if db_path != ":memory:" else ":memory:"

    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder=str(Path(__file__).parent / "pages"),
        title="PokerHero Analyzer",
        suppress_callback_exceptions=True,
    )

    # Ensure the schema exists for file-based DBs.
    if db_path != ":memory:":
        init_db(db_path)

    # Expose db_path to page callbacks via Flask's app config.
    app.server.config["DB_PATH"] = str(db_path)

    app.layout = html.Div(
        style={"fontFamily": "sans-serif"},
        children=[
            dcc.Store(id="theme-store", storage_type="local", data="light"),
            html.Span(id="theme-apply-dummy", style={"display": "none"}),
            html.Button(
                "🌚",
                id="theme-toggle-btn",
                n_clicks=0,
                title="Toggle dark / light mode",
                style={
                    "position": "fixed",
                    "top": "12px",
                    "right": "16px",
                    "zIndex": "9999",
                    "fontSize": "22px",
                    "lineHeight": "1",
                    "background": "transparent",
                    "border": "none",
                    "cursor": "pointer",
                    "padding": "4px 6px",
                    "borderRadius": "6px",
                },
            ),
            dash.page_container,
        ],
    )

    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle-btn", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def _toggle_theme(n_clicks: int | None, current: str) -> str:
        """Flip theme between light and dark on button click."""
        return "dark" if current == "light" else "light"

    @app.callback(
        Output("theme-toggle-btn", "children"),
        Input("theme-store", "data"),
    )
    def _sync_theme_button(theme: str) -> str:
        """Keep toggle icon in sync with stored theme (🌚 = go dark, 🌞 = go light)."""
        return "🌞" if theme == "dark" else "🌚"

    app.clientside_callback(  # type: ignore[no-untyped-call]
        """
        function(theme) {
            if (theme === 'dark') {
                document.body.classList.add('dark');
            } else {
                document.body.classList.remove('dark');
            }
            return '';
        }
        """,
        Output("theme-apply-dummy", "children"),
        Input("theme-store", "data"),
    )

    return app
