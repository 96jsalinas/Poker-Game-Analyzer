"""Entry point for the PokerHero Analyzer development server.

Usage:
    python run.py

The database is created at data/pokerhero.db if it does not already exist.
Override the path with the POKERHERO_DB_PATH environment variable.
"""

from pokerhero.config import DB_PATH
from pokerhero.database.db import init_db
from pokerhero.frontend.app import create_app

if __name__ == "__main__":
    init_db(DB_PATH)
    app = create_app(db_path=DB_PATH)
    app.run(debug=True)
