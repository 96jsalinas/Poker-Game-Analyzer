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


class TestMultiPageApp:
    def test_app_uses_pages(self):
        """create_app() must register at least one page (use_pages=True)."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        assert len(dash.page_registry) > 0

    def test_home_page_registered(self):
        """Home page must be registered at path '/'."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/" in paths

    def test_upload_page_registered(self):
        """Upload page must be registered at path '/upload'."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/upload" in paths


class TestHomePageLayout:
    def test_has_link_to_upload(self):
        """Home layout must contain an href to /upload."""
        from pokerhero.frontend.pages.home import layout

        comp = layout() if callable(layout) else layout
        assert "/upload" in str(comp)

    def test_has_link_to_sessions(self):
        """Home layout must contain an href to /sessions."""
        from pokerhero.frontend.pages.home import layout

        comp = layout() if callable(layout) else layout
        assert "/sessions" in str(comp)


class TestUploadPageLayout:
    def test_has_username_input(self):
        """Upload page layout must have a hero-username input component."""
        from pokerhero.frontend.pages.upload import layout

        comp = layout() if callable(layout) else layout
        assert "hero-username" in str(comp)

    def test_has_upload_component(self):
        """Upload page layout must have an upload-data dcc.Upload component."""
        from pokerhero.frontend.pages.upload import layout

        comp = layout() if callable(layout) else layout
        assert "upload-data" in str(comp)


class TestSessionsPageLayout:
    def test_sessions_page_registered(self):
        """Sessions page must be registered at path '/sessions'."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/sessions" in paths

    def test_layout_has_drill_down_content(self):
        """Sessions page layout must have a drill-down-content container."""
        from pokerhero.frontend.pages.sessions import layout

        comp = layout() if callable(layout) else layout
        assert "drill-down-content" in str(comp)

    def test_layout_has_breadcrumb(self):
        """Sessions page layout must have a breadcrumb component."""
        from pokerhero.frontend.pages.sessions import layout

        comp = layout() if callable(layout) else layout
        assert "breadcrumb" in str(comp)

    def test_layout_has_drill_down_state_store(self):
        """Sessions page layout must have a drill-down-state dcc.Store."""
        from pokerhero.frontend.pages.sessions import layout

        comp = layout() if callable(layout) else layout
        assert "drill-down-state" in str(comp)

    def test_layout_has_back_link(self):
        """Sessions page layout must have a link back to home."""
        from pokerhero.frontend.pages.sessions import layout

        comp = layout() if callable(layout) else layout
        assert "/" in str(comp)


class TestDashboardPageLayout:
    def test_dashboard_page_registered(self):
        """Dashboard page must be registered at path '/dashboard'."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/dashboard" in paths

    def test_layout_has_kpi_section(self):
        """Dashboard layout must contain a dashboard-content loading container."""
        from pokerhero.frontend.pages.dashboard import layout

        comp = layout() if callable(layout) else layout
        assert "dashboard-content" in str(comp)

    def test_layout_has_bankroll_graph(self):
        """Dashboard callback must target bankroll-graph; verify ID in render output."""
        # The graph is rendered inside the callback — confirm the ID string is defined
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert "bankroll-graph" in src

    def test_layout_has_positional_table(self):
        """Dashboard callback must render a positional-stats section."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert "positional-stats" in src

    def test_home_links_to_dashboard(self):
        """Home page layout must contain a link to /dashboard."""
        from pokerhero.frontend.pages.home import layout

        comp = layout() if callable(layout) else layout
        assert "/dashboard" in str(comp)


class TestCardRendering:
    """Tests for the _render_card and _render_cards helper functions."""

    def test_render_card_spade_symbol(self):
        """_render_card('As') must contain the spade symbol ♠."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "♠" in str(_render_card("As"))

    def test_render_card_heart_symbol(self):
        """_render_card('Kh') must contain the heart symbol ♥."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "♥" in str(_render_card("Kh"))

    def test_render_card_diamond_symbol(self):
        """_render_card('Qd') must contain the diamond symbol ♦."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "♦" in str(_render_card("Qd"))

    def test_render_card_club_symbol(self):
        """_render_card('Jc') must contain the club symbol ♣."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "♣" in str(_render_card("Jc"))

    def test_render_card_rank_shown(self):
        """_render_card('As') must contain the rank 'A'."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "A" in str(_render_card("As"))

    def test_render_card_red_for_hearts(self):
        """Hearts must render with red colour (#cc0000)."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "#cc0000" in str(_render_card("Kh"))

    def test_render_card_red_for_diamonds(self):
        """Diamonds must render with red colour (#cc0000)."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "#cc0000" in str(_render_card("Qd"))

    def test_render_card_dark_for_spades(self):
        """Spades must NOT render with red colour."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "#cc0000" not in str(_render_card("As"))

    def test_render_card_dark_for_clubs(self):
        """Clubs must NOT render with red colour."""
        from pokerhero.frontend.pages.sessions import _render_card

        assert "#cc0000" not in str(_render_card("Jc"))

    def test_render_cards_multiple(self):
        """_render_cards('As Kd') must render both suit symbols."""
        from pokerhero.frontend.pages.sessions import _render_cards

        result = str(_render_cards("As Kd"))
        assert "♠" in result
        assert "♦" in result

    def test_render_cards_three_cards(self):
        """_render_cards for a flop string must render all three suit symbols."""
        from pokerhero.frontend.pages.sessions import _render_cards

        result = str(_render_cards("Ah Kh Qh"))
        assert result.count("♥") == 3

    def test_render_cards_none_shows_dash(self):
        """_render_cards(None) must show the em-dash fallback."""
        from pokerhero.frontend.pages.sessions import _render_cards

        assert "—" in str(_render_cards(None))

    def test_render_cards_empty_shows_dash(self):
        """_render_cards('') must show the em-dash fallback."""
        from pokerhero.frontend.pages.sessions import _render_cards

        assert "—" in str(_render_cards(""))


class TestHeroRowHighlighting:
    """Tests for _action_row_style — hero row visual distinction."""

    def test_hero_row_has_background_color(self):
        """Hero rows must have a backgroundColor style."""
        from pokerhero.frontend.pages.sessions import _action_row_style

        assert "backgroundColor" in _action_row_style(True)

    def test_hero_row_has_left_border(self):
        """Hero rows must have a left-border accent."""
        from pokerhero.frontend.pages.sessions import _action_row_style

        assert "borderLeft" in _action_row_style(True)

    def test_non_hero_row_no_background(self):
        """Non-hero rows must not have a backgroundColor override."""
        from pokerhero.frontend.pages.sessions import _action_row_style

        assert "backgroundColor" not in _action_row_style(False)

    def test_non_hero_row_no_border(self):
        """Non-hero rows must not have a left-border override."""
        from pokerhero.frontend.pages.sessions import _action_row_style

        assert "borderLeft" not in _action_row_style(False)

    def test_hero_and_non_hero_styles_differ(self):
        """Hero and non-hero row styles must be different dicts."""
        from pokerhero.frontend.pages.sessions import _action_row_style

        assert _action_row_style(True) != _action_row_style(False)


class TestSettingsPageLayout:
    def test_settings_page_registered(self):
        """Settings page must be registered at path '/settings'."""
        import dash

        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")
        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/settings" in paths

    def test_layout_has_username_input(self):
        """Settings layout must contain a settings-username input."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "settings-username" in str(comp)

    def test_layout_has_clear_db_button(self):
        """Settings layout must contain a clear-db-btn button."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "clear-db-btn" in str(comp)

    def test_layout_has_export_csv_button(self):
        """Settings layout must contain an export-csv-btn button."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "export-csv-btn" in str(comp)

    def test_home_links_to_settings(self):
        """Home page layout must contain a link to /settings."""
        from pokerhero.frontend.pages.home import layout

        comp = layout() if callable(layout) else layout
        assert "/settings" in str(comp)
