"""Entry point for the PokerHero Analyzer development server.

Usage:
    python run.py

The database is created at data/pokerhero.db if it does not already exist.
Override the path with the POKERHERO_DB_PATH environment variable.
Set POKERHERO_DEBUG=true to enable the Werkzeug debugger.
"""

import os

import diskcache
from dash import DiskcacheManager

from pokerhero.config import DB_PATH, setup_logging
from pokerhero.database.db import init_db
from pokerhero.frontend.app import create_app

if __name__ == "__main__":
    setup_logging()
    init_db(DB_PATH)
    cache_dir = str(DB_PATH.parent / "cache")
    cache = diskcache.Cache(cache_dir)
    manager = DiskcacheManager(cache)
    app = create_app(db_path=DB_PATH, background_callback_manager=manager)
    debug = os.environ.get("POKERHERO_DEBUG", "").lower() == "true"
    app.run(debug=debug)
