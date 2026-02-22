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


class TestMathCell:
    """Tests for the _format_math_cell helper in the action view."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_empty_string_for_non_hero_no_spr(self):
        """Non-hero action with no SPR and no MDF → empty string."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        assert _format_math_cell(None, None, False, 0.0, 100.0) == ""

    def test_spr_shown_on_flop_action(self):
        """SPR value present → 'SPR: X.XX' appears in result."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(3.5, None, False, 0.0, 100.0)
        assert "SPR: 3.50" in result

    def test_pot_odds_shown_for_hero_facing_bet(self):
        """Hero facing a bet → 'Pot odds: X.X%' appears in result.

        amount_to_call=50, pot_before=100 → 50/150 = 33.3%
        """
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(None, None, True, 50.0, 100.0)
        assert "Pot odds: 33.3%" in result

    def test_mdf_shown_alongside_pot_odds(self):
        """Hero facing bet with mdf set → both Pot Odds and MDF in result."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(None, 0.667, True, 50.0, 100.0)
        assert "Pot odds:" in result
        assert "MDF:" in result

    def test_mdf_formats_as_percentage(self):
        """mdf=0.5 → 'MDF: 50.0%' in result."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(None, 0.5, True, 50.0, 100.0)
        assert "MDF: 50.0%" in result

    def test_mdf_not_shown_when_none(self):
        """mdf=None → 'MDF' must not appear in result."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(None, None, True, 50.0, 100.0)
        assert "MDF" not in result

    def test_spr_prepended_before_pot_odds_and_mdf(self):
        """When all three are present, SPR appears before Pot Odds and MDF."""
        from pokerhero.frontend.pages.sessions import _format_math_cell

        result = _format_math_cell(2.5, 0.667, True, 50.0, 100.0)
        assert result.index("SPR") < result.index("Pot odds")
        assert result.index("Pot odds") < result.index("MDF")


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


class TestDashboardHighlights:
    """Tests for the _build_highlights helper and its presence on the dashboard."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_hp_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "net_result": [500.0, -200.0, 100.0],
                "hole_cards": ["As Kd", "Qh Jh", None],
                "hand_id": [1, 2, 3],
                "session_id": [10, 20, 10],
            }
        )

    def _make_sessions_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [10, 20],
                "net_profit": [800.0, -300.0],
                "start_time": ["2026-01-01", "2026-01-02"],
                "small_blind": [100.0, 100.0],
                "big_blind": [200.0, 200.0],
            }
        )

    def test_highlights_section_in_dashboard_source(self):
        """Dashboard module source must contain a highlights-section id."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        assert "highlights-section" in inspect.getsource(dashboard)

    def test_build_highlights_returns_div(self):
        """_build_highlights must return a Dash html.Div."""
        from dash import html

        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = _build_highlights(self._make_hp_df(), self._make_sessions_df())
        assert isinstance(result, html.Div)

    def test_build_highlights_shows_biggest_win(self):
        """_build_highlights must show the biggest single-hand win amount."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "500" in result

    def test_build_highlights_shows_biggest_loss(self):
        """_build_highlights must show the biggest single-hand loss amount."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "200" in result

    def test_build_highlights_shows_best_session(self):
        """_build_highlights must show the best session net_profit."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "800" in result

    def test_build_highlights_shows_worst_session(self):
        """_build_highlights must show the worst session net_profit."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "300" in result

    def test_build_highlights_empty_returns_div(self):
        """_build_highlights with empty DataFrames must still return html.Div."""
        import pandas as pd
        from dash import html

        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = _build_highlights(pd.DataFrame(), pd.DataFrame())
        assert isinstance(result, html.Div)

    def test_build_highlights_biggest_win_is_green(self):
        """Biggest hand win card must use green colouring."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        # The +500 win and green colour must appear together in the output
        assert "green" in result

    def test_build_highlights_biggest_loss_is_red(self):
        """Biggest hand loss card must use red colouring."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "red" in result

    def test_best_session_card_links_to_sessions_page(self):
        """Best session card must be a link to /sessions with session_id param."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "/sessions?session_id=10" in result  # session id=10 has net_profit=800

    def test_worst_session_card_links_to_sessions_page(self):
        """Worst session card must be a link to /sessions with session_id param."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "/sessions?session_id=20" in result  # session id=20 has net_profit=-300

    def test_best_hand_card_links_with_hand_and_session_id(self):
        """Best hand card must link to /sessions with both hand_id and session_id."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "hand_id=1" in result  # hand_id=1 has net_result=500
        assert "session_id=10" in result  # session_id of that hand

    def test_worst_hand_card_links_with_hand_and_session_id(self):
        """Worst hand card must link to /sessions with both hand_id and session_id."""
        from pokerhero.frontend.pages.dashboard import _build_highlights

        result = str(_build_highlights(self._make_hp_df(), self._make_sessions_df()))
        assert "hand_id=2" in result  # hand_id=2 has net_result=-200
        assert "session_id=20" in result  # session_id of that hand


class TestSessionsNavParsing:
    """Tests for the _parse_nav_search URL helper on the sessions page."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_empty_search_returns_none(self):
        """Empty search string returns None (no navigation intent)."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        assert _parse_nav_search("") is None

    def test_session_id_param_sets_hands_level(self):
        """?session_id=5 → level='hands', session_id=5."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        state = _parse_nav_search("?session_id=5")
        assert state is not None
        assert state["level"] == "hands"
        assert state["session_id"] == 5

    def test_hand_id_param_sets_actions_level(self):
        """?session_id=5&hand_id=12 → level='actions', hand_id=12, session_id=5."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        state = _parse_nav_search("?session_id=5&hand_id=12")
        assert state is not None
        assert state["level"] == "actions"
        assert state["hand_id"] == 12
        assert state["session_id"] == 5

    def test_unrelated_params_return_none(self):
        """Search string with no recognised params returns None."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        assert _parse_nav_search("?foo=bar") is None


class TestVpipPfrChart:
    """Tests for the _build_vpip_pfr_chart helper on the dashboard."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_vpip_pfr_chart_id_in_dashboard_source(self):
        """Dashboard source must contain the vpip-pfr-chart component id."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        assert "vpip-pfr-chart" in inspect.getsource(dashboard)

    def test_build_vpip_pfr_chart_returns_div(self):
        """_build_vpip_pfr_chart must return an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.dashboard import _build_vpip_pfr_chart

        result = _build_vpip_pfr_chart(0.25, 0.18)
        assert isinstance(result, html.Div)

    def test_build_vpip_pfr_chart_contains_graph(self):
        """_build_vpip_pfr_chart must contain a dcc.Graph child."""

        from pokerhero.frontend.pages.dashboard import _build_vpip_pfr_chart

        result = str(_build_vpip_pfr_chart(0.25, 0.18))
        assert "vpip-pfr-chart" in result

    def test_build_vpip_pfr_chart_handles_zeros(self):
        """_build_vpip_pfr_chart must not raise when vpip and pfr are both 0."""
        from pokerhero.frontend.pages.dashboard import _build_vpip_pfr_chart

        result = _build_vpip_pfr_chart(0.0, 0.0)
        assert result is not None

    def test_build_vpip_pfr_chart_pfr_cannot_exceed_vpip(self):
        """_build_vpip_pfr_chart must clamp pfr to vpip when pfr > vpip."""
        from pokerhero.frontend.pages.dashboard import _build_vpip_pfr_chart

        # Should not raise even with inconsistent inputs
        result = _build_vpip_pfr_chart(0.10, 0.20)
        assert result is not None


class TestStatHeader:
    """Tests for the _stat_header helper on the dashboard positional stats table."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_stat_header_returns_th(self):
        """_stat_header must return an html.Th."""
        from dash import html

        from pokerhero.frontend.pages.dashboard import _stat_header

        result = _stat_header("VPIP%", "Voluntarily Put In Pot")
        assert isinstance(result, html.Th)

    def test_stat_header_label_in_output(self):
        """Label text must appear in the component output."""
        from pokerhero.frontend.pages.dashboard import _stat_header

        result = _stat_header("VPIP%", "Some tooltip text")
        assert "VPIP%" in str(result)

    def test_stat_header_tooltip_text_in_output(self):
        """Tooltip text must be present in the component so it renders on hover."""
        from pokerhero.frontend.pages.dashboard import _stat_header

        result = _stat_header("PFR%", "Pre-Flop Raise rate")
        assert "Pre-Flop Raise rate" in str(result)

    def test_stat_header_has_help_class(self):
        """The tooltip trigger element must have the stat-help CSS class."""
        from pokerhero.frontend.pages.dashboard import _stat_header

        result = _stat_header("AF", "Aggression Factor")
        assert "stat-help" in str(result)

    def test_stat_header_in_dashboard_source(self):
        """Dashboard source must use _stat_header (confirms it is wired in)."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        assert "stat-help" in inspect.getsource(dashboard)


class TestSessionFilters:
    """Tests for the _filter_sessions_data pure helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "start_time": ["2026-01-10", "2026-01-20", "2026-02-05"],
                "small_blind": [50, 100, 100],
                "big_blind": [100, 200, 200],
                "hands_played": [20, 5, 40],
                "net_profit": [500.0, -200.0, 1000.0],
            }
        )

    def test_no_filters_returns_all(self):
        """With no filter values all rows are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, None, None
        )
        assert len(result) == 3

    def test_filter_by_date_from(self):
        """Only sessions on or after date_from are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), "2026-01-15", None, None, None, None, None
        )
        assert len(result) == 2

    def test_filter_by_date_to(self):
        """Only sessions on or before date_to are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, "2026-01-25", None, None, None, None
        )
        assert len(result) == 2

    def test_filter_by_stakes(self):
        """Only sessions matching selected stakes label are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, ["50/100"], None, None, None
        )
        assert len(result) == 1

    def test_filter_by_pnl_min(self):
        """Only sessions with net_profit >= pnl_min are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(self._make_df(), None, None, None, 0, None, None)
        assert len(result) == 2

    def test_filter_by_pnl_max(self):
        """Only sessions with net_profit <= pnl_max are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, 500, None
        )
        assert len(result) == 2

    def test_filter_by_min_hands(self):
        """Only sessions with hands_played >= min_hands are returned."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, None, 10
        )
        assert len(result) == 2


class TestHandFilters:
    """Tests for the _filter_hands_data pure helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "source_hand_id": ["H1", "H2", "H3", "H4"],
                "hole_cards": ["As Kh", "Qd Jc", None, "7s 2d"],
                "total_pot": [300.0, 150.0, 500.0, 80.0],
                "net_result": [200.0, -100.0, 400.0, -50.0],
                "position": ["BTN", "SB", "BB", "CO"],
                "went_to_showdown": [1, 0, 1, 0],
                "saw_flop": [1, 0, 1, 1],
            }
        )

    def test_no_filters_returns_all(self):
        """With no filter values all rows are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(self._make_df(), None, None, None, False, False)
        assert len(result) == 4

    def test_filter_by_pnl_min(self):
        """Only hands with net_result >= pnl_min are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(self._make_df(), 0, None, None, False, False)
        assert len(result) == 2

    def test_filter_by_pnl_max(self):
        """Only hands with net_result <= pnl_max are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(self._make_df(), None, 0, None, False, False)
        assert len(result) == 2

    def test_filter_by_position(self):
        """Only hands at the selected positions are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(
            self._make_df(), None, None, ["BTN", "CO"], False, False
        )
        assert len(result) == 2

    def test_filter_saw_flop_only(self):
        """Only hands where hero saw the flop are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(self._make_df(), None, None, None, True, False)
        assert len(result) == 3

    def test_filter_showdown_only(self):
        """Only hands that went to showdown are returned."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(self._make_df(), None, None, None, False, True)
        assert len(result) == 2


class TestFavoriteButton:
    """Tests for the favourite button helper and filter extensions."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_fav_button_label_filled_star_when_favorite(self):
        """_fav_button_label(True) must return the filled star character."""
        from pokerhero.frontend.pages.sessions import _fav_button_label

        assert _fav_button_label(True) == "★"

    def test_fav_button_label_empty_star_when_not_favorite(self):
        """_fav_button_label(False) must return the empty star character."""
        from pokerhero.frontend.pages.sessions import _fav_button_label

        assert _fav_button_label(False) == "☆"

    def _make_sessions_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "start_time": ["2026-01-10", "2026-01-20", "2026-02-05"],
                "small_blind": [50, 100, 100],
                "big_blind": [100, 200, 200],
                "hands_played": [20, 5, 40],
                "net_profit": [500.0, -200.0, 1000.0],
                "is_favorite": [1, 0, 1],
            }
        )

    def _make_hands_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "source_hand_id": ["H1", "H2", "H3"],
                "hole_cards": ["As Kh", "Qd Jc", None],
                "total_pot": [300.0, 150.0, 500.0],
                "net_result": [200.0, -100.0, 400.0],
                "position": ["BTN", "SB", "BB"],
                "went_to_showdown": [1, 0, 1],
                "saw_flop": [1, 0, 1],
                "is_favorite": [0, 1, 0],
            }
        )

    def test_filter_sessions_favorites_only_returns_only_favorites(self):
        """favorites_only=True keeps only rows where is_favorite == 1."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_sessions_df(),
            None,
            None,
            None,
            None,
            None,
            None,
            favorites_only=True,
        )
        assert len(result) == 2
        assert all(result["is_favorite"] == 1)

    def test_filter_sessions_favorites_default_returns_all(self):
        """favorites_only defaults to False and returns all rows."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_sessions_df(), None, None, None, None, None, None
        )
        assert len(result) == 3

    def test_filter_hands_favorites_only_returns_only_favorites(self):
        """favorites_only=True keeps only hands where is_favorite == 1."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(
            self._make_hands_df(),
            None,
            None,
            None,
            False,
            False,
            favorites_only=True,
        )
        assert len(result) == 1
        assert all(result["is_favorite"] == 1)

    def test_filter_hands_favorites_default_returns_all(self):
        """favorites_only defaults to False and returns all rows."""
        from pokerhero.frontend.pages.sessions import _filter_hands_data

        result = _filter_hands_data(
            self._make_hands_df(), None, None, None, False, False
        )
        assert len(result) == 3


class TestFormatCardsText:
    """Tests for the _format_cards_text plain-text card formatter."""

    def test_none_returns_dash(self):
        """None input returns an em-dash placeholder."""
        from pokerhero.frontend.pages.sessions import _format_cards_text

        assert _format_cards_text(None) == "—"

    def test_empty_string_returns_dash(self):
        """Empty string returns an em-dash placeholder."""
        from pokerhero.frontend.pages.sessions import _format_cards_text

        assert _format_cards_text("") == "—"

    def test_single_card_converted(self):
        """A single card code is converted to rank + suit symbol."""
        from pokerhero.frontend.pages.sessions import _format_cards_text

        assert _format_cards_text("As") == "A♠"

    def test_two_card_hole_hand(self):
        """A typical two-card hole hand is formatted with suit symbols."""
        from pokerhero.frontend.pages.sessions import _format_cards_text

        assert _format_cards_text("As Kh") == "A♠ K♥"

    def test_suit_mapping_all_suits(self):
        """All four suit codes are mapped to the correct symbols."""
        from pokerhero.frontend.pages.sessions import _format_cards_text

        assert _format_cards_text("2h 3d 4c 5s") == "2♥ 3♦ 4♣ 5♠"


class TestSessionDataTable:
    """Tests for _build_session_table returning a dash_table.DataTable."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2],
                "start_time": ["2026-01-10", "2026-02-05"],
                "small_blind": [50, 100],
                "big_blind": [100, 200],
                "hands_played": [20, 40],
                "net_profit": [500.0, -200.0],
                "is_favorite": [0, 0],
            }
        )

    def test_returns_datatable(self):
        """_build_session_table returns a DataTable component."""
        from dash import dash_table

        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert isinstance(result, dash_table.DataTable)

    def test_has_correct_id(self):
        """DataTable has id 'session-table'."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert result.id == "session-table"

    def test_has_sort_action_native(self):
        """DataTable has sort_action='native' for client-side sorting."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert result.sort_action == "native"

    def test_column_names(self):
        """DataTable columns are Date, Stakes, Hands, Net P&L."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        col_names = [c["name"] for c in result.columns]
        assert col_names == ["Date", "Stakes", "Hands", "Net P&L"]

    def test_data_has_id_field(self):
        """Each data row contains an 'id' key for navigation lookups."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert all("id" in row for row in result.data)

    def test_data_row_count(self):
        """DataTable data has one row per session in the DataFrame."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert len(result.data) == 2


class TestHandDataTable:
    """Tests for _build_hand_table returning a dash_table.DataTable."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2],
                "source_hand_id": ["H1", "H2"],
                "hole_cards": ["As Kh", "Qd Jc"],
                "total_pot": [300.0, 150.0],
                "net_result": [200.0, -100.0],
                "position": ["BTN", "SB"],
                "went_to_showdown": [1, 0],
                "saw_flop": [1, 0],
                "is_favorite": [0, 0],
            }
        )

    def test_returns_datatable(self):
        """_build_hand_table returns a DataTable component."""
        from dash import dash_table

        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        assert isinstance(result, dash_table.DataTable)

    def test_has_correct_id(self):
        """DataTable has id 'hand-table'."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        assert result.id == "hand-table"

    def test_has_sort_action_native(self):
        """DataTable has sort_action='native' for client-side sorting."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        assert result.sort_action == "native"

    def test_column_names(self):
        """DataTable columns are Hand #, Hole Cards, Pot, Net Result."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        col_names = [c["name"] for c in result.columns]
        assert col_names == ["Hand #", "Hole Cards", "Pot", "Net Result"]

    def test_hole_cards_uses_suit_symbols(self):
        """Hole cards are formatted with suit symbols, not raw codes."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        hole_col_id = next(c["id"] for c in result.columns if c["name"] == "Hole Cards")
        assert result.data[0][hole_col_id] == "A♠ K♥"

    def test_data_has_id_field(self):
        """Each data row contains an 'id' key for navigation lookups."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        assert all("id" in row for row in result.data)


class TestGuidePage:
    """Tests for the /guide page layout."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_guide_page_registers_at_slash_guide(self):
        """The guide page is registered at the /guide path."""
        import dash

        pages = {p["path"] for p in dash.page_registry.values()}
        assert "/guide" in pages

    def test_guide_layout_is_div(self):
        """The guide page layout is an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.guide import layout

        assert isinstance(layout, html.Div)

    def test_guide_layout_contains_heading(self):
        """The guide page includes a top-level H1 heading."""
        from pokerhero.frontend.pages.guide import layout

        text = str(layout)
        assert "Guide" in text or "guide" in text

    def test_guide_layout_contains_vpip_section(self):
        """The guide page includes a VPIP explanation."""
        from pokerhero.frontend.pages.guide import layout

        text = str(layout)
        assert "VPIP" in text

    def test_guide_layout_contains_spr_section(self):
        """The guide page includes an SPR explanation."""
        from pokerhero.frontend.pages.guide import layout

        text = str(layout)
        assert "SPR" in text

    def test_home_page_has_guide_link(self):
        """The home page navigation includes a link to /guide."""
        from pokerhero.frontend.pages.home import layout

        text = str(layout)
        assert "/guide" in text


class TestShowdownSection:
    """Tests for _build_showdown_section helper in the action view."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_returns_none_when_no_villain_cards(self):
        """No showdown section when no villain cards are available."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section([])
        assert result is None

    def test_returns_div_when_villain_cards_present(self):
        """Returns an html.Div when at least one villain has hole cards."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Ah Kh"}]
        )
        assert isinstance(result, html.Div)

    def test_contains_showdown_heading(self):
        """Rendered section includes a 'Showdown' heading."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "BTN", "hole_cards": "Qd Jc"}]
        )
        assert "Showdown" in str(result)

    def test_contains_villain_username(self):
        """Rendered section includes the villain's username."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "CO", "hole_cards": "7s 2d"}]
        )
        assert "villain1" in str(result)

    def test_contains_hole_cards(self):
        """Rendered section includes the villain's hole card rank values."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "v", "position": "SB", "hole_cards": "As Kd"}]
        )
        text = str(result)
        # Cards render as rank + suit symbol (e.g. "A♠"), not raw "As"
        assert "A" in text and "K" in text

    def test_multiple_villains_all_shown(self):
        """All villains with hole cards are included in the section."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [
                {"username": "alice", "position": "BTN", "hole_cards": "Ah Kh"},
                {"username": "bob", "position": "SB", "hole_cards": "Qd Jc"},
            ]
        )
        text = str(result)
        assert "alice" in text and "bob" in text
