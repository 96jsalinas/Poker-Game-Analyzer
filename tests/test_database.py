import sqlite3
from pathlib import Path
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "pokerhero" / "database" / "schema.sql"

@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    yield conn
    conn.close()

class TestSchema:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists()

    def test_players_table_exists(self, db):
        row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'").fetchone()
        assert row is not None

    def test_sessions_table_exists(self, db):
        row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'").fetchone()
        assert row is not None

    def test_hands_table_exists(self, db):
        row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hands'").fetchone()
        assert row is not None

    def test_hand_players_table_exists(self, db):
        row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hand_players'").fetchone()
        assert row is not None

    def test_actions_table_exists(self, db):
        row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='actions'").fetchone()
        assert row is not None

    def _columns(self, db, table):
        return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}

    def test_players_columns(self, db):
        cols = self._columns(db, "players")
        assert {"id", "username", "preferred_name"} <= cols

    def test_sessions_columns(self, db):
        cols = self._columns(db, "sessions")
        assert {"id", "game_type", "limit_type", "max_seats", "small_blind", "big_blind", "ante", "start_time", "hero_buy_in", "hero_cash_out"} <= cols

    def test_hands_columns(self, db):
        cols = self._columns(db, "hands")
        assert {"id", "session_id", "board_flop", "board_turn", "board_river", "total_pot", "uncalled_bet_returned", "rake", "timestamp"} <= cols

    def test_hand_players_columns(self, db):
        cols = self._columns(db, "hand_players")
        assert {"hand_id", "player_id", "position", "starting_stack", "hole_cards", "vpip", "pfr", "went_to_showdown", "net_result"} <= cols

    def test_actions_columns(self, db):
        cols = self._columns(db, "actions")
        assert {"id", "hand_id", "player_id", "is_hero", "street", "action_type", "amount", "amount_to_call", "pot_before", "is_all_in", "sequence", "spr", "mdf"} <= cols


class TestConnection:
    def test_get_connection_returns_connection(self, tmp_path):
        from pokerhero.database.db import get_connection
        conn = get_connection(tmp_path / "test.db")
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_row_factory_is_set(self, tmp_path):
        from pokerhero.database.db import get_connection
        conn = get_connection(tmp_path / "test.db")
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_foreign_keys_enabled(self, tmp_path):
        from pokerhero.database.db import get_connection
        conn = get_connection(tmp_path / "test.db")
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
        conn.close()

    def test_init_db_creates_tables(self, tmp_path):
        from pokerhero.database.db import init_db
        conn = init_db(tmp_path / "test.db")
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"players", "sessions", "hands", "hand_players", "actions"} <= tables
        conn.close()

    def test_init_db_idempotent(self, tmp_path):
        """Calling init_db twice does not raise or duplicate tables."""
        from pokerhero.database.db import init_db
        db_path = tmp_path / "test.db"
        init_db(db_path).close()
        conn = init_db(db_path)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert len([t for t in tables if t in {"players", "sessions", "hands", "hand_players", "actions"}]) == 5
        conn.close()
