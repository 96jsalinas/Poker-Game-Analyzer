"""Tests for the ingestion pipeline: splitter and file/directory ingestion."""

from pathlib import Path

import pytest

HISTORIES = Path(__file__).parent / "fixtures"
FRATERNITAS = HISTORIES / "play_money_two_hand_session.txt"
FIXTURES = Path(__file__).parent / "fixtures"
REBUY_FIXTURE = FIXTURES / "cash_hero_rebuy.txt"


class TestSplitHands:
    def test_empty_text_returns_empty_list(self):
        from pokerhero.ingestion.splitter import split_hands

        assert split_hands("") == []

    def test_whitespace_only_returns_empty_list(self):
        from pokerhero.ingestion.splitter import split_hands

        assert split_hands("   \n\n  ") == []

    def test_single_hand_returns_one_block(self):
        from pokerhero.ingestion.splitter import split_hands

        text = (FIXTURES / "cash_hero_wins_showdown.txt").read_text()
        assert len(split_hands(text)) == 1

    def test_multi_hand_file_returns_correct_count(self):
        from pokerhero.ingestion.splitter import split_hands

        text = FRATERNITAS.read_text(encoding="utf-8")
        assert len(split_hands(text)) == 2

    def test_each_block_starts_with_hand_header(self):
        from pokerhero.ingestion.splitter import split_hands

        text = FRATERNITAS.read_text(encoding="utf-8")
        for block in split_hands(text):
            assert block.startswith("PokerStars Hand #")

    def test_blocks_have_no_leading_trailing_whitespace(self):
        from pokerhero.ingestion.splitter import split_hands

        text = FRATERNITAS.read_text(encoding="utf-8")
        for block in split_hands(text):
            assert block == block.strip()


class TestIngestFile:
    @pytest.fixture
    def db(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_returns_correct_ingested_count(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        result = ingest_file(FRATERNITAS, "jsalinas96", db)
        assert result.ingested == 2

    def test_returns_zero_skipped_on_first_import(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        result = ingest_file(FRATERNITAS, "jsalinas96", db)
        assert result.skipped == 0

    def test_returns_zero_failed_on_clean_file(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        result = ingest_file(FRATERNITAS, "jsalinas96", db)
        assert result.failed == 0

    def test_duplicate_import_skips_all_hands(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        result = ingest_file(FRATERNITAS, "jsalinas96", db)
        assert result.skipped == 2
        assert result.ingested == 0

    def test_session_row_created(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1

    def test_hand_rows_created(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM hands").fetchone()[0] == 2

    def test_actions_populated(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM actions").fetchone()[0] > 0

    def test_result_file_path_matches_input(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        result = ingest_file(FRATERNITAS, "jsalinas96", db)
        assert result.file_path == str(FRATERNITAS)


class TestIngestDirectory:
    @pytest.fixture
    def db(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    @pytest.fixture
    def single_file_dir(self, tmp_path):
        import shutil

        shutil.copy(FRATERNITAS, tmp_path / FRATERNITAS.name)
        return tmp_path

    def test_returns_one_result_per_txt_file(self, db, single_file_dir):
        from pokerhero.ingestion.pipeline import ingest_directory

        results = ingest_directory(single_file_dir, "jsalinas96", db)
        assert len(results) == 1

    def test_total_hands_ingested(self, db, single_file_dir):
        from pokerhero.ingestion.pipeline import ingest_directory

        results = ingest_directory(single_file_dir, "jsalinas96", db)
        assert sum(r.ingested for r in results) == 2

    def test_ignores_non_txt_files(self, db, tmp_path):
        import shutil

        from pokerhero.ingestion.pipeline import ingest_directory

        shutil.copy(FRATERNITAS, tmp_path / FRATERNITAS.name)
        (tmp_path / "notes.md").write_text("ignore me")
        results = ingest_directory(tmp_path, "jsalinas96", db)
        assert len(results) == 1

    def test_empty_directory_returns_empty_list(self, db, tmp_path):
        from pokerhero.ingestion.pipeline import ingest_directory

        assert ingest_directory(tmp_path, "jsalinas96", db) == []


class TestHeroBuyInWithRebuy:
    @pytest.fixture
    def db(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_hero_buy_in_includes_rebuy(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(REBUY_FIXTURE, "jsalinas96", db)
        db.commit()
        row = db.execute("SELECT hero_buy_in FROM sessions WHERE id=1").fetchone()
        # Hand 1 starting_stack=42368 + re-buy of 50000 = 92368
        assert row[0] == pytest.approx(92368.0)

    def test_hero_cash_out_is_final_stack(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(REBUY_FIXTURE, "jsalinas96", db)
        db.commit()
        row = db.execute("SELECT hero_cash_out FROM sessions WHERE id=1").fetchone()
        # Hand 2: starting_stack=50000, net_result=-500 → 49500
        assert row[0] == pytest.approx(49500.0)

    def test_net_profit_equals_cash_out_minus_buy_in(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(REBUY_FIXTURE, "jsalinas96", db)
        db.commit()
        row = db.execute(
            "SELECT hero_buy_in, hero_cash_out FROM sessions WHERE id=1"
        ).fetchone()
        net_row = db.execute(
            """SELECT SUM(hp.net_result)
               FROM hand_players hp
               JOIN players p ON p.id = hp.player_id
               WHERE p.username = 'jsalinas96'"""
        ).fetchone()
        # cash_out - buy_in should equal sum of hand net_results
        # (42368 - 42368) + (49500 - 50000) = -500
        assert abs((row[1] - row[0]) - net_row[0]) < 0.01


class TestSessionFinancials:
    @pytest.fixture
    def db(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_hero_buy_in_is_not_null(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        row = db.execute("SELECT hero_buy_in FROM sessions WHERE id=1").fetchone()
        assert row[0] is not None

    def test_hero_cash_out_is_not_null(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        row = db.execute("SELECT hero_cash_out FROM sessions WHERE id=1").fetchone()
        assert row[0] is not None

    def test_hero_cash_out_minus_buy_in_equals_sum_of_net_results(self, db):
        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        db.commit()
        row = db.execute(
            "SELECT hero_buy_in, hero_cash_out FROM sessions WHERE id=1"
        ).fetchone()
        net_row = db.execute(
            """SELECT SUM(hp.net_result)
               FROM hand_players hp
               JOIN players p ON p.id = hp.player_id
               WHERE p.username = 'jsalinas96'"""
        ).fetchone()
        assert abs((row[1] - row[0]) - net_row[0]) < 0.01


class TestIngestFileLogging:
    @pytest.fixture
    def db(self, tmp_path):
        from pokerhero.database.db import init_db

        conn = init_db(tmp_path / "test.db")
        yield conn
        conn.close()

    def test_logs_info_on_start(self, db, caplog):
        import logging

        from pokerhero.ingestion.pipeline import ingest_file

        with caplog.at_level(logging.INFO, logger="pokerhero.ingestion.pipeline"):
            ingest_file(FRATERNITAS, "jsalinas96", db)
        assert any("Starting ingestion" in r.message for r in caplog.records)

    def test_logs_info_on_completion(self, db, caplog):
        import logging

        from pokerhero.ingestion.pipeline import ingest_file

        with caplog.at_level(logging.INFO, logger="pokerhero.ingestion.pipeline"):
            ingest_file(FRATERNITAS, "jsalinas96", db)
        assert any("Ingestion complete" in r.message for r in caplog.records)

    def test_logs_warning_on_skipped_duplicate(self, db, caplog):
        import logging

        from pokerhero.ingestion.pipeline import ingest_file

        ingest_file(FRATERNITAS, "jsalinas96", db)
        with caplog.at_level(logging.WARNING, logger="pokerhero.ingestion.pipeline"):
            ingest_file(FRATERNITAS, "jsalinas96", db)
        assert any("duplicate" in r.message.lower() for r in caplog.records)

    def test_logs_error_on_failed_hand(self, db, caplog, monkeypatch):
        import logging

        from pokerhero.ingestion import pipeline
        from pokerhero.ingestion.pipeline import ingest_file

        monkeypatch.setattr(
            pipeline,
            "save_parsed_hand",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("injected")),
        )
        with caplog.at_level(logging.ERROR, logger="pokerhero.ingestion.pipeline"):
            ingest_file(FRATERNITAS, "jsalinas96", db)
        assert any("Failed" in r.message for r in caplog.records)
