"""Tests for the frontend upload handler logic."""

import base64
from pathlib import Path

import pytest

FRATERNITAS = (
    Path(__file__).parent.parent
    / "data"
    / "histories"
    / "HH20260129 Fraternitas VII - 100-200 - Play Money No Limit Hold'em.txt"
)


def _encode_file(path: Path) -> str:
    """Encode a file as a Dash dcc.Upload content string (data URI)."""
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:text/plain;base64,{b64}"


@pytest.fixture
def db(tmp_path):
    from pokerhero.database.db import init_db

    conn = init_db(tmp_path / "test.db")
    yield conn
    conn.close()


class TestUploadHandler:
    def test_valid_file_returns_success_message(self, db):
        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        result = handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        assert "2" in result  # 2 hands ingested
        assert "error" not in result.lower()

    def test_ingested_count_in_message(self, db):
        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        result = handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        assert "2 imported" in result or "2 hands" in result

    def test_duplicate_import_shows_skipped(self, db):
        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        result = handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        assert "2 skipped" in result

    def test_hands_persisted_to_db(self, db):
        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        count = db.execute("SELECT COUNT(*) FROM hands").fetchone()[0]
        assert count == 2

    def test_app_can_be_created(self):
        from pokerhero.frontend.app import create_app

        app = create_app(db_path=":memory:")
        assert app is not None
        assert app.layout is not None


class TestUploadHandlerLogging:
    def test_logs_info_on_upload_received(self, db, caplog):
        import logging

        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        with caplog.at_level(logging.INFO, logger="pokerhero.frontend.upload_handler"):
            handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        assert any(FRATERNITAS.name in r.message for r in caplog.records)

    def test_logs_info_on_upload_result(self, db, caplog):
        import logging

        from pokerhero.frontend.upload_handler import handle_upload

        content = _encode_file(FRATERNITAS)
        with caplog.at_level(logging.INFO, logger="pokerhero.frontend.upload_handler"):
            handle_upload(content, FRATERNITAS.name, "jsalinas96", db)
        assert any("imported" in r.message for r in caplog.records)
