"""Entry point for the PokerHero Analyzer development server.

Usage:
    python run.py

The database is created at data/pokerhero.db if it does not already exist.
Override the path with the POKERHERO_DB_PATH environment variable.
"""

import diskcache
from dash import DiskcacheManager

from pokerhero.config import DB_PATH, setup_logging
from pokerhero.database.db import init_db
from pokerhero.frontend.app import create_app

if __name__ == "__main__":
    setup_logging()
    init_db(DB_PATH)
    cache = diskcache.Cache("./cache")
    manager = DiskcacheManager(cache)
    app = create_app(db_path=DB_PATH, background_callback_manager=manager)
    app.run(debug=True)
