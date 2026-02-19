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


class TestPlayerInsert:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db
        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_upsert_returns_int_id(self, idb):
        from pokerhero.database.db import upsert_player
        pid = upsert_player(idb, "hero")
        assert isinstance(pid, int)
        assert pid > 0

    def test_upsert_inserts_row(self, idb):
        from pokerhero.database.db import upsert_player
        upsert_player(idb, "villain")
        row = idb.execute("SELECT username, preferred_name FROM players WHERE username='villain'").fetchone()
        assert row is not None
        assert row[0] == "villain"
        assert row[1] == "villain"

    def test_preferred_name_defaults_to_username(self, idb):
        from pokerhero.database.db import upsert_player
        upsert_player(idb, "jsalinas96")
        row = idb.execute("SELECT preferred_name FROM players WHERE username='jsalinas96'").fetchone()
        assert row[0] == "jsalinas96"

    def test_upsert_idempotent_same_id(self, idb):
        from pokerhero.database.db import upsert_player
        id1 = upsert_player(idb, "player1")
        id2 = upsert_player(idb, "player1")
        assert id1 == id2

    def test_upsert_does_not_overwrite_preferred_name(self, idb):
        from pokerhero.database.db import upsert_player
        upsert_player(idb, "player1")
        idb.execute("UPDATE players SET preferred_name='My Villain' WHERE username='player1'")
        upsert_player(idb, "player1")  # second call
        row = idb.execute("SELECT preferred_name FROM players WHERE username='player1'").fetchone()
        assert row[0] == "My Villain"  # not overwritten

    def test_multiple_players_unique_ids(self, idb):
        from pokerhero.database.db import upsert_player
        id1 = upsert_player(idb, "alpha")
        id2 = upsert_player(idb, "beta")
        assert id1 != id2


class TestSessionInsert:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db
        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def sample_session(self):
        from pokerhero.parser.models import SessionData
        from decimal import Decimal
        return SessionData(
            game_type="NLHE",
            limit_type="No Limit",
            max_seats=9,
            small_blind=Decimal("100"),
            big_blind=Decimal("200"),
            ante=Decimal("0"),
            is_tournament=False,
            table_name="TestTable",
            tournament_id=None,
        )

    def test_insert_returns_int_id(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        assert isinstance(sid, int)
        assert sid > 0

    def test_insert_row_exists(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        row = idb.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        assert row is not None

    def test_insert_values_correct(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        row = idb.execute("SELECT game_type, limit_type, max_seats, small_blind, big_blind FROM sessions WHERE id=?", (sid,)).fetchone()
        assert row[0] == "NLHE"
        assert row[1] == "No Limit"
        assert row[2] == 9
        assert row[3] == 100.0
        assert row[4] == 200.0

    def test_insert_with_hero_buyin(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        from decimal import Decimal
        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00", hero_buy_in=Decimal("5000"))
        row = idb.execute("SELECT hero_buy_in FROM sessions WHERE id=?", (sid,)).fetchone()
        assert row[0] == 5000.0

    def test_insert_hero_buyin_null_by_default(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        row = idb.execute("SELECT hero_buy_in, hero_cash_out FROM sessions WHERE id=?", (sid,)).fetchone()
        assert row[0] is None
        assert row[1] is None

    def test_multiple_sessions_unique_ids(self, idb, sample_session):
        from pokerhero.database.db import insert_session
        id1 = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        id2 = insert_session(idb, sample_session, start_time="2024-01-15T21:30:00")
        assert id1 != id2

