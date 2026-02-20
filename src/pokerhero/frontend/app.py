"""Dash application factory for PokerHero Analyzer.

Use create_app() to build the app instance. run.py calls create_app()
with the configured DB path and starts the development server.
"""

from __future__ import annotations

from pathlib import Path

import dash
from dash import dcc, html

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
    )

    # Ensure the schema exists for file-based DBs.
    if db_path != ":memory:":
        init_db(db_path)

    # Expose db_path to page callbacks via Flask's app config.
    app.server.config["DB_PATH"] = str(db_path)

    app.layout = html.Div(
        style={"fontFamily": "sans-serif"},
        children=[
            dcc.Location(id="_pages_location"),
            dash.page_container,
        ],
    )

    return app
