import sqlite3
from pathlib import Path

import pytest

SCHEMA_PATH = (
    Path(__file__).parent.parent / "src" / "pokerhero" / "database" / "schema.sql"
)


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
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='players'"
        ).fetchone()
        assert row is not None

    def test_sessions_table_exists(self, db):
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        ).fetchone()
        assert row is not None

    def test_hands_table_exists(self, db):
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hands'"
        ).fetchone()
        assert row is not None

    def test_hand_players_table_exists(self, db):
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hand_players'"
        ).fetchone()
        assert row is not None

    def test_actions_table_exists(self, db):
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='actions'"
        ).fetchone()
        assert row is not None

    def _columns(self, db, table):
        return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}

    def test_players_columns(self, db):
        cols = self._columns(db, "players")
        assert {"id", "username", "preferred_name"} <= cols

    def test_sessions_columns(self, db):
        cols = self._columns(db, "sessions")
        assert {
            "id",
            "game_type",
            "limit_type",
            "max_seats",
            "small_blind",
            "big_blind",
            "ante",
            "start_time",
            "hero_buy_in",
            "hero_cash_out",
        } <= cols

    def test_hands_columns(self, db):
        cols = self._columns(db, "hands")
        assert {
            "id",
            "session_id",
            "board_flop",
            "board_turn",
            "board_river",
            "total_pot",
            "uncalled_bet_returned",
            "rake",
            "timestamp",
        } <= cols

    def test_hand_players_columns(self, db):
        cols = self._columns(db, "hand_players")
        assert {
            "hand_id",
            "player_id",
            "position",
            "starting_stack",
            "hole_cards",
            "vpip",
            "pfr",
            "went_to_showdown",
            "net_result",
        } <= cols

    def test_actions_columns(self, db):
        cols = self._columns(db, "actions")
        assert {
            "id",
            "hand_id",
            "player_id",
            "is_hero",
            "street",
            "action_type",
            "amount",
            "amount_to_call",
            "pot_before",
            "is_all_in",
            "sequence",
            "spr",
            "mdf",
        } <= cols


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
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"players", "sessions", "hands", "hand_players", "actions"} <= tables
        conn.close()

    def test_init_db_idempotent(self, tmp_path):
        """Calling init_db twice does not raise or duplicate tables."""
        from pokerhero.database.db import init_db

        db_path = tmp_path / "test.db"
        init_db(db_path).close()
        conn = init_db(db_path)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert (
            len(
                [
                    t
                    for t in tables
                    if t in {"players", "sessions", "hands", "hand_players", "actions"}
                ]
            )
            == 5
        )
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
        row = idb.execute(
            "SELECT username, preferred_name FROM players WHERE username='villain'"
        ).fetchone()
        assert row is not None
        assert row[0] == "villain"
        assert row[1] == "villain"

    def test_preferred_name_defaults_to_username(self, idb):
        from pokerhero.database.db import upsert_player

        upsert_player(idb, "jsalinas96")
        row = idb.execute(
            "SELECT preferred_name FROM players WHERE username='jsalinas96'"
        ).fetchone()
        assert row[0] == "jsalinas96"

    def test_upsert_idempotent_same_id(self, idb):
        from pokerhero.database.db import upsert_player

        id1 = upsert_player(idb, "player1")
        id2 = upsert_player(idb, "player1")
        assert id1 == id2

    def test_upsert_does_not_overwrite_preferred_name(self, idb):
        from pokerhero.database.db import upsert_player

        upsert_player(idb, "player1")
        idb.execute(
            "UPDATE players SET preferred_name='My Villain' WHERE username='player1'"
        )
        upsert_player(idb, "player1")  # second call
        row = idb.execute(
            "SELECT preferred_name FROM players WHERE username='player1'"
        ).fetchone()
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
        from decimal import Decimal

        from pokerhero.parser.models import SessionData

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
        row = idb.execute(
            "SELECT game_type, limit_type, max_seats, small_blind, big_blind FROM sessions WHERE id=?",
            (sid,),
        ).fetchone()
        assert row[0] == "NLHE"
        assert row[1] == "No Limit"
        assert row[2] == 9
        assert row[3] == 100.0
        assert row[4] == 200.0

    def test_insert_with_hero_buyin(self, idb, sample_session):
        from decimal import Decimal

        from pokerhero.database.db import insert_session

        sid = insert_session(
            idb,
            sample_session,
            start_time="2024-01-15T20:30:00",
            hero_buy_in=Decimal("5000"),
        )
        row = idb.execute(
            "SELECT hero_buy_in FROM sessions WHERE id=?", (sid,)
        ).fetchone()
        assert row[0] == 5000.0

    def test_insert_hero_buyin_null_by_default(self, idb, sample_session):
        from pokerhero.database.db import insert_session

        sid = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        row = idb.execute(
            "SELECT hero_buy_in, hero_cash_out FROM sessions WHERE id=?", (sid,)
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

    def test_multiple_sessions_unique_ids(self, idb, sample_session):
        from pokerhero.database.db import insert_session

        id1 = insert_session(idb, sample_session, start_time="2024-01-15T20:30:00")
        id2 = insert_session(idb, sample_session, start_time="2024-01-15T21:30:00")
        assert id1 != id2


class TestUpdateSessionFinancials:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def session_id(self, idb):
        from decimal import Decimal

        from pokerhero.database.db import insert_session
        from pokerhero.parser.models import SessionData

        s = SessionData(
            game_type="NLHE",
            limit_type="NL",
            max_seats=9,
            small_blind=Decimal("100"),
            big_blind=Decimal("200"),
            ante=Decimal("0"),
            is_tournament=False,
            table_name="TestTable",
        )
        return insert_session(idb, s, start_time="2024-01-15T20:30:00")

    def test_sets_hero_buy_in(self, idb, session_id):
        from decimal import Decimal

        from pokerhero.database.db import update_session_financials

        update_session_financials(idb, session_id, Decimal("10000"), Decimal("12500"))
        row = idb.execute(
            "SELECT hero_buy_in FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        assert row[0] == 10000.0

    def test_sets_hero_cash_out(self, idb, session_id):
        from decimal import Decimal

        from pokerhero.database.db import update_session_financials

        update_session_financials(idb, session_id, Decimal("10000"), Decimal("12500"))
        row = idb.execute(
            "SELECT hero_cash_out FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        assert row[0] == 12500.0

    def test_does_not_affect_other_sessions(self, idb, session_id):
        from decimal import Decimal

        from pokerhero.database.db import insert_session, update_session_financials
        from pokerhero.parser.models import SessionData

        other = SessionData(
            game_type="NLHE",
            limit_type="NL",
            max_seats=9,
            small_blind=Decimal("100"),
            big_blind=Decimal("200"),
            ante=Decimal("0"),
            is_tournament=False,
            table_name="OtherTable",
        )
        other_id = insert_session(idb, other, start_time="2024-02-01T10:00:00")
        update_session_financials(idb, session_id, Decimal("10000"), Decimal("12500"))
        row = idb.execute(
            "SELECT hero_buy_in, hero_cash_out FROM sessions WHERE id=?", (other_id,)
        ).fetchone()
        assert row[0] is None
        assert row[1] is None


class TestHandInsert:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def session_id(self, idb):
        from decimal import Decimal

        from pokerhero.database.db import insert_session
        from pokerhero.parser.models import SessionData

        s = SessionData(
            game_type="NLHE",
            limit_type="No Limit",
            max_seats=9,
            small_blind=Decimal("100"),
            big_blind=Decimal("200"),
            ante=Decimal("0"),
            is_tournament=False,
            table_name="T",
            tournament_id=None,
        )
        return insert_session(idb, s, start_time="2024-01-15T20:30:00")

    @pytest.fixture
    def sample_hand(self):
        from datetime import datetime
        from decimal import Decimal

        from pokerhero.parser.models import HandData

        return HandData(
            hand_id="123456789",
            timestamp=datetime(2024, 1, 15, 20, 30, 0),
            button_seat=1,
            board_flop="Ah Kh Qh",
            board_turn="Js",
            board_river="Td",
            total_pot=Decimal("1200"),
            uncalled_bet_returned=Decimal("0"),
            rake=Decimal("60"),
        )

    @pytest.fixture
    def sample_players(self):
        from decimal import Decimal

        from pokerhero.parser.models import HandPlayerData

        return [
            HandPlayerData(
                username="jsalinas96",
                seat=1,
                starting_stack=Decimal("10000"),
                position="BTN",
                hole_cards="As Kd",
                net_result=Decimal("600"),
                vpip=True,
                pfr=True,
                went_to_showdown=True,
                is_hero=True,
            ),
            HandPlayerData(
                username="villain1",
                seat=2,
                starting_stack=Decimal("8000"),
                position="BB",
                hole_cards=None,
                net_result=Decimal("-600"),
                vpip=True,
                pfr=False,
                went_to_showdown=False,
                is_hero=False,
            ),
        ]

    def test_insert_hand_row_exists(self, idb, session_id, sample_hand):
        from pokerhero.database.db import insert_hand

        insert_hand(idb, sample_hand, session_id)
        row = idb.execute(
            "SELECT id FROM hands WHERE source_hand_id=?", (sample_hand.hand_id,)
        ).fetchone()
        assert row is not None

    def test_insert_hand_values_correct(self, idb, session_id, sample_hand):
        from pokerhero.database.db import insert_hand

        insert_hand(idb, sample_hand, session_id)
        row = idb.execute(
            "SELECT total_pot, rake, board_flop FROM hands WHERE source_hand_id=?",
            (sample_hand.hand_id,),
        ).fetchone()
        assert row[0] == 1200.0
        assert row[1] == 60.0
        assert row[2] == "Ah Kh Qh"

    def test_insert_hand_players_rows_exist(
        self, idb, session_id, sample_hand, sample_players
    ):
        from pokerhero.database.db import (
            insert_hand,
            insert_hand_players,
            upsert_player,
        )

        hid = insert_hand(idb, sample_hand, session_id)
        pid_map = {p.username: upsert_player(idb, p.username) for p in sample_players}
        insert_hand_players(idb, hid, sample_players, pid_map)
        count = idb.execute(
            "SELECT COUNT(*) FROM hand_players WHERE hand_id=?", (hid,)
        ).fetchone()[0]
        assert count == 2

    def test_insert_hand_players_values_correct(
        self, idb, session_id, sample_hand, sample_players
    ):
        from pokerhero.database.db import (
            insert_hand,
            insert_hand_players,
            upsert_player,
        )

        hid = insert_hand(idb, sample_hand, session_id)
        pid_map = {p.username: upsert_player(idb, p.username) for p in sample_players}
        insert_hand_players(idb, hid, sample_players, pid_map)
        hero_pid = pid_map["jsalinas96"]
        row = idb.execute(
            "SELECT position, vpip, pfr, went_to_showdown, net_result FROM hand_players WHERE hand_id=? AND player_id=?",
            (hid, hero_pid),
        ).fetchone()
        assert row[0] == "BTN"
        assert row[1] == 1  # vpip True
        assert row[2] == 1  # pfr True
        assert row[3] == 1  # went_to_showdown True
        assert row[4] == 600.0

    def test_insert_hand_players_null_hole_cards(
        self, idb, session_id, sample_hand, sample_players
    ):
        from pokerhero.database.db import (
            insert_hand,
            insert_hand_players,
            upsert_player,
        )

        hid = insert_hand(idb, sample_hand, session_id)
        pid_map = {p.username: upsert_player(idb, p.username) for p in sample_players}
        insert_hand_players(idb, hid, sample_players, pid_map)
        villain_pid = pid_map["villain1"]
        row = idb.execute(
            "SELECT hole_cards FROM hand_players WHERE hand_id=? AND player_id=?",
            (hid, villain_pid),
        ).fetchone()
        assert row[0] is None


class TestActionsInsert:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def setup_hand(self, idb):
        """Insert a session, hand, and players; return (hand_id, player_id_map)."""
        from datetime import datetime
        from decimal import Decimal

        from pokerhero.database.db import insert_hand, insert_session, upsert_player
        from pokerhero.parser.models import HandData, SessionData

        s = SessionData(
            game_type="NLHE",
            limit_type="No Limit",
            max_seats=9,
            small_blind=Decimal("100"),
            big_blind=Decimal("200"),
            ante=Decimal("0"),
            is_tournament=False,
            table_name="T",
            tournament_id=None,
        )
        sid = insert_session(idb, s, start_time="2024-01-15T20:30:00")
        h = HandData(
            hand_id="111222333",
            timestamp=datetime(2024, 1, 15, 20, 30, 0),
            button_seat=1,
            board_flop=None,
            board_turn=None,
            board_river=None,
            total_pot=Decimal("600"),
            uncalled_bet_returned=Decimal("0"),
            rake=Decimal("0"),
        )
        hid = insert_hand(idb, h, sid)
        pid_map = {
            "jsalinas96": upsert_player(idb, "jsalinas96"),
            "villain1": upsert_player(idb, "villain1"),
        }
        return hid, pid_map

    @pytest.fixture
    def sample_actions(self):
        from decimal import Decimal

        from pokerhero.parser.models import ActionData

        return [
            ActionData(
                sequence=1,
                player="villain1",
                is_hero=False,
                street="PREFLOP",
                action_type="POST_BLIND",
                amount=Decimal("200"),
                amount_to_call=Decimal("0"),
                pot_before=Decimal("0"),
                is_all_in=False,
                spr=None,
                mdf=None,
            ),
            ActionData(
                sequence=2,
                player="jsalinas96",
                is_hero=True,
                street="PREFLOP",
                action_type="CALL",
                amount=Decimal("200"),
                amount_to_call=Decimal("200"),
                pot_before=Decimal("200"),
                is_all_in=False,
                spr=None,
                mdf=None,
            ),
            ActionData(
                sequence=3,
                player="jsalinas96",
                is_hero=True,
                street="FLOP",
                action_type="CHECK",
                amount=Decimal("0"),
                amount_to_call=Decimal("0"),
                pot_before=Decimal("400"),
                is_all_in=False,
                spr=Decimal("5.5"),
                mdf=None,
            ),
        ]

    def test_insert_actions_count(self, idb, setup_hand, sample_actions):
        from pokerhero.database.db import insert_actions

        hand_id, pid_map = setup_hand
        insert_actions(idb, hand_id, sample_actions, pid_map)
        count = idb.execute(
            "SELECT COUNT(*) FROM actions WHERE hand_id=?", (hand_id,)
        ).fetchone()[0]
        assert count == 3

    def test_insert_actions_sequence_correct(self, idb, setup_hand, sample_actions):
        from pokerhero.database.db import insert_actions

        hand_id, pid_map = setup_hand
        insert_actions(idb, hand_id, sample_actions, pid_map)
        rows = idb.execute(
            "SELECT sequence FROM actions WHERE hand_id=? ORDER BY sequence", (hand_id,)
        ).fetchall()
        assert [r[0] for r in rows] == [1, 2, 3]

    def test_insert_actions_values_correct(self, idb, setup_hand, sample_actions):
        from pokerhero.database.db import insert_actions

        hand_id, pid_map = setup_hand
        insert_actions(idb, hand_id, sample_actions, pid_map)
        row = idb.execute(
            "SELECT street, action_type, amount, pot_before, is_hero FROM actions WHERE hand_id=? AND sequence=2",
            (hand_id,),
        ).fetchone()
        assert row[0] == "PREFLOP"
        assert row[1] == "CALL"
        assert row[2] == 200.0
        assert row[3] == 200.0
        assert row[4] == 1  # is_hero True

    def test_insert_actions_spr_stored(self, idb, setup_hand, sample_actions):
        from pokerhero.database.db import insert_actions

        hand_id, pid_map = setup_hand
        insert_actions(idb, hand_id, sample_actions, pid_map)
        row = idb.execute(
            "SELECT spr FROM actions WHERE hand_id=? AND sequence=3", (hand_id,)
        ).fetchone()
        assert row[0] == pytest.approx(5.5)

    def test_insert_actions_null_spr_mdf(self, idb, setup_hand, sample_actions):
        from pokerhero.database.db import insert_actions

        hand_id, pid_map = setup_hand
        insert_actions(idb, hand_id, sample_actions, pid_map)
        row = idb.execute(
            "SELECT spr, mdf FROM actions WHERE hand_id=? AND sequence=1", (hand_id,)
        ).fetchone()
        assert row[0] is None
        assert row[1] is None


class TestSaveParsedHand:
    FIXTURE = Path(__file__).parent / "fixtures" / "cash_hero_wins_showdown.txt"

    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def parsed(self):
        from pokerhero.parser.hand_parser import HandParser

        return HandParser(hero_username="jsalinas96").parse(self.FIXTURE.read_text())

    @pytest.fixture
    def session_id(self, idb, parsed):
        from pokerhero.database.db import insert_session

        return insert_session(
            idb, parsed.session, start_time=parsed.hand.timestamp.isoformat()
        )

    def test_save_inserts_hand_row(self, idb, parsed, session_id):
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        row = idb.execute(
            "SELECT id FROM hands WHERE source_hand_id=?", (parsed.hand.hand_id,)
        ).fetchone()
        assert row is not None

    def test_save_inserts_all_players(self, idb, parsed, session_id):
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        count = idb.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        assert count == len(parsed.players)

    def test_save_inserts_all_hand_players(self, idb, parsed, session_id):
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        hid = idb.execute(
            "SELECT id FROM hands WHERE source_hand_id=?", (parsed.hand.hand_id,)
        ).fetchone()[0]
        count = idb.execute(
            "SELECT COUNT(*) FROM hand_players WHERE hand_id=?", (hid,)
        ).fetchone()[0]
        assert count == len(parsed.players)

    def test_save_inserts_all_actions(self, idb, parsed, session_id):
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        hid = idb.execute(
            "SELECT id FROM hands WHERE source_hand_id=?", (parsed.hand.hand_id,)
        ).fetchone()[0]
        count = idb.execute(
            "SELECT COUNT(*) FROM actions WHERE hand_id=?", (hid,)
        ).fetchone()[0]
        assert count == len(parsed.actions)

    def test_save_hero_vpip_stored(self, idb, parsed, session_id):
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        hero_player = next(p for p in parsed.players if p.is_hero)
        hero_pid = idb.execute(
            "SELECT id FROM players WHERE username=?", ("jsalinas96",)
        ).fetchone()[0]
        hid = idb.execute(
            "SELECT id FROM hands WHERE source_hand_id=?", (parsed.hand.hand_id,)
        ).fetchone()[0]
        row = idb.execute(
            "SELECT vpip FROM hand_players WHERE hand_id=? AND player_id=?",
            (hid, hero_pid),
        ).fetchone()
        assert row[0] == int(hero_player.vpip)

    def test_save_twice_raises_on_duplicate_hand(self, idb, parsed, session_id):
        """source_hand_id is UNIQUE — inserting the same hand twice must raise."""
        from pokerhero.database.db import save_parsed_hand

        save_parsed_hand(idb, parsed, session_id)
        idb.commit()
        with pytest.raises(Exception):
            save_parsed_hand(idb, parsed, session_id)


class TestSettings:
    @pytest.fixture
    def idb(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_settings_table_exists(self, idb):
        row = idb.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        ).fetchone()
        assert row is not None

    def test_get_setting_returns_default_when_missing(self, idb):
        from pokerhero.database.db import get_setting

        assert get_setting(idb, "hero_username", default="") == ""

    def test_set_and_get_setting(self, idb):
        from pokerhero.database.db import get_setting, set_setting

        set_setting(idb, "hero_username", "jsalinas96")
        assert get_setting(idb, "hero_username", default="") == "jsalinas96"

    def test_set_setting_overwrites_existing(self, idb):
        from pokerhero.database.db import get_setting, set_setting

        set_setting(idb, "hero_username", "jsalinas96")
        set_setting(idb, "hero_username", "newname")
        assert get_setting(idb, "hero_username", default="") == "newname"

    def test_set_setting_does_not_affect_other_keys(self, idb):
        from pokerhero.database.db import get_setting, set_setting

        set_setting(idb, "hero_username", "jsalinas96")
        assert get_setting(idb, "other_key", default="fallback") == "fallback"
