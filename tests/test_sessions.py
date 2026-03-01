"""Tests for the sessions page components."""

import pytest


class TestCardRendering:
    """Tests for the _render_card and _render_cards helper functions."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

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

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

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


class TestSessionsNavParsing:
    """Tests for the _parse_nav_search URL helper on the sessions page."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_empty_search_returns_none(self):
        """Empty search string returns None (no navigation intent)."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        assert _parse_nav_search("") is None

    def test_session_id_param_sets_report_level(self):
        """?session_id=5 → level='report', session_id=5 (opens Session Report)."""
        from pokerhero.frontend.pages.sessions import _parse_nav_search

        state = _parse_nav_search("?session_id=5")
        assert state is not None
        assert state["level"] == "report"
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


class TestUpdateStateDataTable:
    """Tests for _compute_state_from_cell — pure navigation logic."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_session_cell_click_navigates_to_report(self):
        """Clicking a session row navigates to level='report' (Session Report)."""
        from pokerhero.frontend.pages.sessions import _compute_state_from_cell

        session_data = [{"id": 7, "date": "2026-01-10", "stakes": "50/100"}]
        result = _compute_state_from_cell(
            session_cell={"row": 0, "column": 0, "column_id": "date"},
            hand_cell=None,
            session_data=session_data,
            hand_data=None,
            current_state={"level": "sessions"},
        )
        assert result["level"] == "report"
        assert result["session_id"] == 7

    def test_hand_cell_click_navigates_to_actions(self):
        """Clicking a hand-table cell navigates to level='actions'."""
        from pokerhero.frontend.pages.sessions import _compute_state_from_cell

        hand_data = [{"id": 42, "hand_num": "H1", "hole_cards": "A♠ K♥"}]
        result = _compute_state_from_cell(
            session_cell=None,
            hand_cell={"row": 0, "column": 0, "column_id": "hand_num"},
            session_data=None,
            hand_data=hand_data,
            current_state={"level": "hands", "session_id": 3},
        )
        assert result["level"] == "actions"
        assert result["hand_id"] == 42
        assert result["session_id"] == 3

    def test_none_cells_raises_prevent_update(self):
        """Both cells None (initial mount) raises PreventUpdate."""
        import dash

        from pokerhero.frontend.pages.sessions import _compute_state_from_cell

        with pytest.raises(dash.exceptions.PreventUpdate):
            _compute_state_from_cell(
                session_cell=None,
                hand_cell=None,
                session_data=None,
                hand_data=None,
                current_state={"level": "sessions"},
            )


# ---------------------------------------------------------------------------
# TestSessionsBreadcrumb
# ---------------------------------------------------------------------------


class TestSessionsBreadcrumb:
    """Tests for _breadcrumb — updated to support 'report' level."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_report_level_returns_html_div(self):
        """_breadcrumb('report', ...) returns an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _breadcrumb

        result = _breadcrumb(
            "report", session_label="2026-01-29  100/200", session_id=3
        )
        assert isinstance(result, html.Div)

    def test_report_level_shows_session_label(self):
        """'report' breadcrumb contains the session label text."""
        from pokerhero.frontend.pages.sessions import _breadcrumb

        result = _breadcrumb(
            "report", session_label="2026-01-29  100/200", session_id=3
        )
        assert "100/200" in str(result)

    def test_hands_level_shows_all_hands(self):
        """'hands' breadcrumb now shows 'All Hands' as the current page."""
        from pokerhero.frontend.pages.sessions import _breadcrumb

        result = _breadcrumb("hands", session_label="100/200", session_id=3)
        assert "All Hands" in str(result)


# ---------------------------------------------------------------------------
# TestUpdateStateBreadcrumb
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TestUpdateStateBreadcrumb
# ---------------------------------------------------------------------------


class TestUpdateStateBreadcrumb:
    """Tests that breadcrumb buttons carry correct ids for _update_state routing."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_report_breadcrumb_button_has_report_level_id(self):
        """'hands' breadcrumb session-label button carries level='report' id."""
        from pokerhero.frontend.pages.sessions import _breadcrumb

        # The session-label button in 'hands' breadcrumb should point to 'report'
        result = str(_breadcrumb("hands", session_label="100/200", session_id=5))
        assert '"report"' in result or "'report'" in result


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
                "currency": ["PLAY", "EUR", "USD"],
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

    def test_currency_filter_real_keeps_eur_and_usd(self):
        """currency_type='real' keeps EUR and USD sessions only."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, None, None, currency_type="real"
        )
        assert set(result["currency"]) == {"EUR", "USD"}

    def test_currency_filter_play_keeps_play_only(self):
        """currency_type='play' keeps PLAY sessions only."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, None, None, currency_type="play"
        )
        assert list(result["currency"]) == ["PLAY"]

    def test_currency_filter_none_returns_all(self):
        """currency_type=None applies no currency filter."""
        from pokerhero.frontend.pages.sessions import _filter_sessions_data

        result = _filter_sessions_data(
            self._make_df(), None, None, None, None, None, None, currency_type=None
        )
        assert len(result) == 3


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

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

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
                "ev_status": ["📊 Calculate", "✅ Ready (2026-01-10)"],
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
        """DataTable columns are Date, Stakes, Hands, Net P&L, EV Status."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        col_names = [c["name"] for c in result.columns]
        assert col_names == ["Date", "Stakes", "Hands", "Net P&L", "EV Status"]

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

    def test_pnl_column_is_numeric_type(self):
        """Net P&L column must have type='numeric' so Dash sorts it numerically."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        pnl_col = next(c for c in result.columns if c["name"] == "Net P&L")
        assert pnl_col.get("type") == "numeric"

    def test_pnl_data_values_are_numeric(self):
        """Net P&L data values must be floats, not formatted strings."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        pnl_col_id = next(c["id"] for c in result.columns if c["name"] == "Net P&L")
        for row in result.data:
            assert isinstance(row[pnl_col_id], (int, float))


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

    def test_pnl_column_is_numeric_type(self):
        """Net Result column must have type='numeric' so Dash sorts it numerically."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        pnl_col = next(c for c in result.columns if c["name"] == "Net Result")
        assert pnl_col.get("type") == "numeric"

    def test_pnl_data_values_are_numeric(self):
        """Net Result data values must be floats, not formatted strings."""
        from pokerhero.frontend.pages.sessions import _build_hand_table

        result = _build_hand_table(self._make_df())
        pnl_col_id = next(c["id"] for c in result.columns if c["name"] == "Net Result")
        for row in result.data:
            assert isinstance(row[pnl_col_id], (int, float))


class TestDescribeHand:
    """Tests for the _describe_hand pure helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_flush_description(self):
        """Flush hand returns 'Flush'."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("Ah Kh", "Qh Jh 2h 3c 4d") == "Flush"

    def test_full_house_description(self):
        """Full house returns 'Full house'."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("As Ad", "Ah Kh Ks 2c 7d") == "Full house"

    def test_straight_flush_description(self):
        """Straight flush returns 'Straight flush'."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("Ah Kh", "Qh Jh Th 2c 3d") == "Straight flush"

    def test_high_card_description(self):
        """7-2 offsuit on a dry board returns 'High card'."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("7s 2d", "Ah Kh Qc 3d 5c") == "High card"

    def test_returns_none_for_short_board(self):
        """Returns None when board has fewer than 3 cards (hand not complete)."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("Ah Kh", "") is None
        assert _describe_hand("Ah Kh", "Qh") is None

    def test_three_card_board_still_works(self):
        """Works with just the flop (3 board cards = 5 total)."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        result = _describe_hand("Ah Kh", "Qh Jh Th")
        assert result == "Straight flush"

    def test_four_of_a_kind_description(self):
        """Four of a kind returns 'Four of a kind'."""
        from pokerhero.frontend.pages.sessions import _describe_hand

        assert _describe_hand("Kd Kc", "Ah Kh Ks 2c 7d") == "Four of a kind"


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

    def test_hero_appears_when_hero_cards_provided(self):
        """Hero is shown in the showdown section when hero_cards is given."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            board="Ah Kh Qs 2c 7d",
        )
        assert "Hero" in str(result)

    def test_hand_description_shown_with_board(self):
        """Each player's hand description is shown when board is provided."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        # Hero: As Ks + board Ah Kh Qd Jc 2s = two pair (aces and kings)
        # Villain: Qh Js + board Ah Kh Qd Jc 2s = two pair (queens and jacks)
        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qh Js"}],
            hero_name="Hero",
            hero_cards="As Ks",
            board="Ah Kh Qd Jc 2s",
        )
        text = str(result)
        assert text.count("Two pair") == 2

    def test_winner_gets_trophy(self):
        """The player with the best hand is labelled with a trophy emoji."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        # Hero: full house (As Ad + Ah Kh Ks), villain: two pair
        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Ad",
            board="Ah Kh Ks 2c 7d",
        )
        assert "🏆" in str(result)

    def test_loser_has_no_trophy(self):
        """The losing player's row does not include a trophy."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Kd Kc"}],
            hero_name="Hero",
            hero_cards="As Ad",
            board="Ah Kh Ks 2c 7d",
        )
        text = str(result)
        # villain has four-of-a-kind kings, hero has full house — villain wins
        # so exactly one trophy exists
        assert text.count("🏆") == 1

    def test_split_pot_both_get_trophy(self):
        """Both players receive a trophy when they tie."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        # Both use the board as their best hand (both have worse hole cards)
        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "2c 3d"}],
            hero_name="Hero",
            hero_cards="4c 5d",
            board="Ah Kh Qh Jh Th",
        )
        text = str(result)
        # Both play the royal-flush board — tied
        assert text.count("🏆") == 2

    def test_no_description_without_board(self):
        """When no board is provided, hand descriptions are not shown."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            board="",
        )
        text = str(result)
        assert "Flush" not in text and "Straight" not in text and "Pair" not in text

    def test_villain_archetype_shown_when_opp_stats_provided(self):
        """Archetype badge appears for villain when opp_stats has their data."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        # 20% VPIP, 15% PFR, 20 hands → TAG
        opp_stats = {"villain1": {"hands_played": 20, "vpip_count": 4, "pfr_count": 3}}
        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            board="Ah Kh Qs 2c 7d",
            opp_stats=opp_stats,
        )
        assert "TAG" in str(result)

    def test_no_archetype_when_opp_stats_absent(self):
        """No archetype badge when opp_stats is None (default)."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            board="Ah Kh Qs 2c 7d",
        )
        text = str(result)
        for archetype in ("TAG", "LAG", "Nit", "Fish"):
            assert archetype not in text

    def test_hero_has_no_archetype_badge(self):
        """Hero row never gets an archetype badge even when opp_stats is provided."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        # Providing a stat entry keyed "Hero" should not cause a badge for hero
        opp_stats = {"villain1": {"hands_played": 20, "vpip_count": 4, "pfr_count": 3}}
        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            board="Ah Kh Qs 2c 7d",
            opp_stats=opp_stats,
        )
        text = str(result)
        # TAG from villain1 appears; hero has no archetype so only one badge
        assert text.count("TAG") == 1

    def test_hero_positive_result_shown(self):
        """Positive hero_net_result is displayed with a '+' prefix in the section."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            hero_net_result=12.5,
        )
        assert "+12.5" in str(result)

    def test_hero_negative_result_shown(self):
        """Negative hero_net_result is displayed with a '-' prefix in the section."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [{"username": "villain1", "position": "SB", "hole_cards": "Qd Jc"}],
            hero_name="Hero",
            hero_cards="As Kd",
            hero_net_result=-8.0,
        )
        assert "-8" in str(result)

    def test_villain_result_shown(self):
        """Villain net_result in the row dict is displayed in the section."""
        from pokerhero.frontend.pages.sessions import _build_showdown_section

        result = _build_showdown_section(
            [
                {
                    "username": "villain1",
                    "position": "BTN",
                    "hole_cards": "Qd Jc",
                    "net_result": -5.25,
                }
            ],
        )
        assert "-5.25" in str(result)


# ===========================================================================
# TestVillainSummaryLine
# ===========================================================================


class TestVillainSummaryLine:
    """Tests for the _build_villain_summary header helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _stats(self, hands=20, vpip=4, pfr=3):
        return {"hands_played": hands, "vpip_count": vpip, "pfr_count": pfr}

    def test_returns_none_when_no_stats(self):
        """Returns None when opp_stats is empty."""
        from pokerhero.frontend.pages.sessions import _build_villain_summary

        assert _build_villain_summary({}) is None

    def test_returns_div_when_stats_present(self):
        """Returns an html.Div when at least one opponent has stats."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_villain_summary

        result = _build_villain_summary({"alice": self._stats()})
        assert isinstance(result, html.Div)

    def test_shows_username(self):
        """Div text includes the opponent's username."""
        from pokerhero.frontend.pages.sessions import _build_villain_summary

        result = _build_villain_summary({"alice": self._stats()})
        assert "alice" in str(result)

    def test_shows_archetype_badge(self):
        """Div includes the archetype badge (TAG) for a qualified opponent."""
        from pokerhero.frontend.pages.sessions import _build_villain_summary

        # 20% VPIP, 15% PFR, 20 hands → TAG
        result = _build_villain_summary({"alice": self._stats(20, 4, 3)})
        assert "TAG" in str(result)

    def test_multiple_opponents_all_shown(self):
        """All opponents appear in the summary line."""
        from pokerhero.frontend.pages.sessions import _build_villain_summary

        result = _build_villain_summary(
            {"alice": self._stats(), "bob": self._stats(20, 10, 2)}
        )
        text = str(result)
        assert "alice" in text and "bob" in text

    def test_below_min_hands_no_archetype(self):
        """Opponent with fewer than 15 hands shows name but no archetype."""
        from pokerhero.frontend.pages.sessions import _build_villain_summary

        result = _build_villain_summary({"alice": self._stats(10, 3, 2)})
        text = str(result)
        assert "alice" in text
        for archetype in ("TAG", "LAG", "Nit", "Fish"):
            assert archetype not in text

    def test_source_shows_first_action_badge(self):
        """sessions.py source contains the first-appearance badge pattern."""
        import inspect

        import pokerhero.frontend.pages.sessions as mod

        src = inspect.getsource(mod)
        assert "seen_villains" in src


# ===========================================================================
# TestFmtBlind / TestFmtPnl
# ===========================================================================


class TestFmtBlind:
    """_fmt_blind formats blind/stake amounts without truncating decimals."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_integer_blind_no_decimal(self):
        from pokerhero.frontend.pages.sessions import _fmt_blind

        assert _fmt_blind(100) == "100"

    def test_decimal_blind_preserves_cents(self):
        from pokerhero.frontend.pages.sessions import _fmt_blind

        assert _fmt_blind(0.02) == "0.02"

    def test_decimal_bb_preserves_cents(self):
        from pokerhero.frontend.pages.sessions import _fmt_blind

        assert _fmt_blind(0.05) == "0.05"

    def test_whole_float_no_trailing_dot(self):
        from pokerhero.frontend.pages.sessions import _fmt_blind

        assert _fmt_blind(200.0) == "200"


class TestFmtPnl:
    """_fmt_pnl formats P&L values with sign and correct decimal places."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_positive_integer_shows_plus(self):
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        assert _fmt_pnl(1500.0) == "+1,500"

    def test_negative_integer_shows_minus(self):
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        assert _fmt_pnl(-200.0) == "-200"

    def test_positive_decimal_preserves_cents(self):
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        assert _fmt_pnl(0.08) == "+0.08"

    def test_negative_decimal_preserves_cents(self):
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        assert _fmt_pnl(-0.02) == "-0.02"

    def test_zero_shows_plus_zero(self):
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        assert _fmt_pnl(0.0) == "+0"

    def test_tiny_value_no_scientific_notation(self):
        """M2: Very small P&L must not use scientific notation."""
        from pokerhero.frontend.pages.sessions import _fmt_pnl

        result = _fmt_pnl(0.000001)
        assert "e" not in result.lower(), f"Scientific notation detected: {result}"


# ---------------------------------------------------------------------------
# TestBuildOpponentProfileCard
# ---------------------------------------------------------------------------


class TestBuildOpponentProfileCard:
    """Tests for the _build_opponent_profile_card pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _card(self, username="Alice", hands=20, vpip_count=5, pfr_count=4):
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        return _build_opponent_profile_card(username, hands, vpip_count, pfr_count)

    def test_returns_html_component(self):
        """Result is a Dash html component (not None or a str)."""
        from dash import html

        result = self._card()
        assert isinstance(result, html.Div)

    def test_shows_username(self):
        """Card source text includes the player's username."""

        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        card = _build_opponent_profile_card("Villain99", 20, 6, 4)
        assert "Villain99" in str(card)

    def test_shows_vpip_percentage(self):
        """Card text includes computed VPIP percentage."""

        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        # 5 vpip out of 20 = 25%
        card = _build_opponent_profile_card("X", 20, 5, 3)
        assert "25" in str(card)

    def test_shows_archetype_tag(self):
        """Card includes the archetype label (TAG/LAG/Nit/Fish) when ≥15 hands."""
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        # 20% VPIP, 15% PFR → TAG
        card = _build_opponent_profile_card("X", 20, 4, 3)
        assert "TAG" in str(card)

    def test_below_min_hands_shows_no_archetype(self):
        """Cards with fewer than 15 hands show no archetype badge."""
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        card = _build_opponent_profile_card("X", 10, 3, 2)
        card_str = str(card)
        for archetype in ("TAG", "LAG", "Nit", "Fish"):
            assert archetype not in card_str

    def test_preliminary_badge_is_faded(self):
        """Badge for 15–49 hands has reduced opacity (preliminary read)."""
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        # 30 hands (≥ min=15, < 50): preliminary tier — badge should be faded
        card = _build_opponent_profile_card("X", 30, 9, 6)
        assert "opacity" in str(card)

    def test_standard_badge_has_no_opacity(self):
        """Badge for 50–99 hands has no opacity adjustment (standard read)."""
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        # 75 hands: standard tier — badge has full opacity (no opacity key)
        card = _build_opponent_profile_card("X", 75, 15, 12)
        card_str = str(card)
        assert "TAG" in card_str
        assert "opacity" not in card_str

    def test_confirmed_badge_has_checkmark(self):
        """Badge for ≥ 100 hands includes a ✓ checkmark (confirmed read)."""
        from pokerhero.frontend.pages.sessions import _build_opponent_profile_card

        # 150 hands: confirmed tier
        card = _build_opponent_profile_card("X", 150, 30, 20)
        assert "✓" in str(card)


# ---------------------------------------------------------------------------
# TestOpponentProfilesPanel
# ---------------------------------------------------------------------------


class TestOpponentProfilesPanel:
    """Tests for the opponent profiles panel in the sessions page source."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_source_has_opponent_profiles_toggle(self):
        """sessions.py source defines the opponent profiles toggle button id."""
        import inspect

        import pokerhero.frontend.pages.sessions as mod

        src = inspect.getsource(mod)
        assert "opponent-profiles-btn" in src

    def test_source_has_opponent_profiles_panel(self):
        """sessions.py source defines the opponent profiles panel container."""
        import inspect

        import pokerhero.frontend.pages.sessions as mod

        src = inspect.getsource(mod)
        assert "opponent-profiles-panel" in src


# ---------------------------------------------------------------------------
# TestBuildSessionKpiStrip
# ---------------------------------------------------------------------------


class TestBuildSessionKpiStrip:
    """Tests for _build_session_kpi_strip pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _kpis(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "vpip": [1, 0, 1],
                "pfr": [1, 0, 0],
                "net_result": [500.0, -200.0, -100.0],
                "big_blind": [200.0, 200.0, 200.0],
                "saw_flop": [1, 0, 1],
                "went_to_showdown": [1, 0, 0],
                "position": ["BTN", "BB", "SB"],
            }
        )

    def _actions(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [1, 1],
                "street": ["FLOP", "FLOP"],
                "action_type": ["BET", "CALL"],
                "position": ["BTN", "BTN"],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_session_kpi_strip

        assert isinstance(
            _build_session_kpi_strip(self._kpis(), self._actions()), html.Div
        )

    def test_shows_hands_count(self):
        """KPI strip displays the number of hands played."""
        from pokerhero.frontend.pages.sessions import _build_session_kpi_strip

        # 3 hands in the fixture DataFrame
        assert "3" in str(_build_session_kpi_strip(self._kpis(), self._actions()))

    def test_shows_vpip_value(self):
        """KPI strip displays the VPIP percentage (2/3 = 66.7%)."""
        from pokerhero.frontend.pages.sessions import _build_session_kpi_strip

        assert "66" in str(_build_session_kpi_strip(self._kpis(), self._actions()))

    def test_shows_pfr_value(self):
        """KPI strip displays the PFR percentage (1/3 = 33.3%)."""
        from pokerhero.frontend.pages.sessions import _build_session_kpi_strip

        assert "33" in str(_build_session_kpi_strip(self._kpis(), self._actions()))

    def test_empty_dataframes_no_crash(self):
        """Empty DataFrames return a Div without raising."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_session_kpi_strip

        assert _build_session_kpi_strip(pd.DataFrame(), pd.DataFrame()) is not None


# ---------------------------------------------------------------------------
# TestBuildSessionNarrative
# ---------------------------------------------------------------------------


class TestBuildSessionNarrative:
    """Tests for _build_session_narrative pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _kpis(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "vpip": [1, 0, 1],
                "pfr": [1, 0, 0],
                "net_result": [500.0, -200.0, -100.0],
                "big_blind": [200.0, 200.0, 200.0],
                "saw_flop": [1, 0, 1],
                "went_to_showdown": [1, 0, 0],
                "position": ["BTN", "BB", "SB"],
            }
        )

    def _actions(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [1, 1],
                "street": ["FLOP", "FLOP"],
                "action_type": ["BET", "CALL"],
                "position": ["BTN", "BTN"],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_session_narrative

        result = _build_session_narrative(
            self._kpis(), self._actions(), "2026-01-29  100/200"
        )
        assert isinstance(result, html.Div)

    def test_contains_hands_count(self):
        """Narrative text includes the number of hands played."""
        from pokerhero.frontend.pages.sessions import _build_session_narrative

        result = _build_session_narrative(
            self._kpis(), self._actions(), "2026-01-29  100/200"
        )
        assert "3" in str(result)

    def test_contains_session_label(self):
        """Narrative text includes the session label (stakes)."""
        from pokerhero.frontend.pages.sessions import _build_session_narrative

        result = _build_session_narrative(
            self._kpis(), self._actions(), "2026-01-29  100/200"
        )
        assert "100/200" in str(result)

    def test_empty_no_crash(self):
        """Empty DataFrames return a Div without raising."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_session_narrative

        assert (
            _build_session_narrative(pd.DataFrame(), pd.DataFrame(), "no session")
            is not None
        )


# ---------------------------------------------------------------------------
# TestBuildEvSummary
# ---------------------------------------------------------------------------


class TestBuildEvSummary:
    """Tests for _build_ev_summary pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _ev_df(self, equity: float = 0.9, net_result: float = 5000.0):
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#100"],
                "equity": [equity],
                "net_result": [net_result],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div for both empty and non-empty input."""
        import pandas as pd
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_ev_summary

        assert isinstance(_build_ev_summary(pd.DataFrame()), html.Div)

    def test_empty_shows_not_calculated_message(self):
        """Empty DataFrame (no cache) produces a 'not yet calculated' message."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_ev_summary

        text = str(_build_ev_summary(pd.DataFrame())).lower()
        assert "calculate" in text

    def test_nonempty_mentions_showdown(self):
        """Non-empty ev_df mentions showdown in the output."""
        from pokerhero.frontend.pages.sessions import _build_ev_summary

        text = str(_build_ev_summary(self._ev_df())).lower()
        assert "showdown" in text

    def test_unlucky_outcome_shows_below_equity(self):
        """Hero had near-100% equity but lost → below equity verdict."""
        from pokerhero.frontend.pages.sessions import _build_ev_summary

        result = _build_ev_summary(self._ev_df(equity=1.0, net_result=-3000.0))
        assert "below" in str(result).lower()


# ---------------------------------------------------------------------------
# TestBuildFlaggedHandsList
# ---------------------------------------------------------------------------


class TestBuildFlaggedHandsList:
    """Tests for _build_flagged_hands_list pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _ev_df(self, equity: float = 0.9, net_result: float = 5000.0):
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#100"],
                "equity": [equity],
                "net_result": [net_result],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div for empty input."""
        import pandas as pd
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        assert isinstance(_build_flagged_hands_list(pd.DataFrame()), html.Div)

    def test_nonempty_no_crash(self):
        """Non-flagged hand (won with high equity) returns Div without raising."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        # equity=0.9, won → not flagged (below lucky_threshold=0.4)
        assert (
            _build_flagged_hands_list(self._ev_df(equity=0.9, net_result=5000.0))
            is not None
        )

    def test_unlucky_hand_flagged(self):
        """Hero had near-100% equity but lost → flagged as Unlucky."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        result = _build_flagged_hands_list(self._ev_df(equity=1.0, net_result=-3000.0))
        assert "Unlucky" in str(result)

    def test_lucky_hand_flagged(self):
        """Hero had near-zero equity but won → flagged as Lucky."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        result = _build_flagged_hands_list(self._ev_df(equity=0.0, net_result=5000.0))
        assert "Lucky" in str(result)


# ---------------------------------------------------------------------------
# TestBuildSessionPositionTable
# ---------------------------------------------------------------------------


class TestBuildSessionPositionTable:
    """Tests for _build_session_position_table pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _kpis(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "vpip": [1, 1, 0, 1, 0, 1],
                "pfr": [1, 0, 0, 1, 0, 0],
                "net_result": [500.0, -200.0, -100.0, 300.0, -50.0, 100.0],
                "big_blind": [200.0] * 6,
                "saw_flop": [1, 1, 0, 1, 0, 1],
                "went_to_showdown": [1, 0, 0, 1, 0, 0],
                "position": ["BTN", "CO", "MP", "UTG", "SB", "BB"],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div."""
        from dash import html

        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = _build_session_position_table(self._kpis(), conn)
        conn.close()
        assert isinstance(result, html.Div)

    def test_shows_position_names(self):
        """Table rows include position abbreviations."""
        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = str(_build_session_position_table(self._kpis(), conn))
        conn.close()
        assert "BTN" in result

    def test_shows_vpip_values(self):
        """Table cells show VPIP percentages."""
        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = str(_build_session_position_table(self._kpis(), conn))
        conn.close()
        # BTN has 1/1 = 100% VPIP
        assert "100.0" in result

    def test_traffic_light_color_applied(self):
        """Cells carry a backgroundColor from the traffic light palette."""
        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = str(_build_session_position_table(self._kpis(), conn))
        conn.close()
        # Any of the three pastel hex codes must appear
        assert any(color in result for color in ("#d4edda", "#fff3cd", "#f8d7da"))

    def test_empty_dataframe_no_crash(self):
        """Empty kpis_df returns a Div without raising."""
        import pandas as pd

        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = _build_session_position_table(pd.DataFrame(), conn)
        conn.close()
        assert result is not None


# ---------------------------------------------------------------------------
# TestBackgroundCallbackSetup
# ---------------------------------------------------------------------------


class TestBackgroundCallbackSetup:
    """Tests for DiskcacheManager setup and background callback wiring (step 7a)."""

    def test_diskcache_importable(self):
        """diskcache package is installed and importable."""
        import diskcache  # noqa: F401

    def test_create_app_accepts_background_manager(self, tmp_path):
        """create_app(background_callback_manager=...) does not raise."""
        import diskcache
        from dash import DiskcacheManager

        from pokerhero.frontend.app import create_app

        cache = diskcache.Cache(str(tmp_path / "cache"))
        manager = DiskcacheManager(cache)
        app = create_app(db_path=":memory:", background_callback_manager=manager)
        assert app is not None

    def test_background_manager_stored_in_config(self, tmp_path):
        """Provided manager is stored in app.server.config under BACKGROUND_MANAGER."""
        import diskcache
        from dash import DiskcacheManager

        from pokerhero.frontend.app import create_app

        cache = diskcache.Cache(str(tmp_path / "cache"))
        manager = DiskcacheManager(cache)
        app = create_app(db_path=":memory:", background_callback_manager=manager)
        assert app.server.config["BACKGROUND_MANAGER"] is manager


# ---------------------------------------------------------------------------
# TestIdentifyPrimaryVillain
# ---------------------------------------------------------------------------


class TestIdentifyPrimaryVillain:
    """Tests for the identify_primary_villain stats helper."""

    @pytest.fixture
    def conn(self, tmp_path):
        from pokerhero.database.db import init_db

        c = init_db(tmp_path / "test.db")
        yield c
        c.close()

    def _seed(self, conn, n_villains: int = 1, add_aggressor: bool = False):
        """Seed session/hand/players/actions.

        Returns (session_id, hand_id, hero_id, villain_ids, hero_sequence).
        When add_aggressor=True, villain_ids[1] BETs on FLOP before hero acts.
        """
        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        villain_ids = []
        for i in range(n_villains):
            vid = conn.execute(
                "INSERT INTO players (username, preferred_name)"
                f" VALUES ('villain{i}', 'V{i}')"
            ).lastrowid
            villain_ids.append(vid)
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-01-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp)"
            " VALUES ('H1', ?, 1000, 0, 0, '2024-01-01T00:00:00')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, 1, 1, 0, 0, -200)",
            (hid, hero_id),
        )
        for vid in villain_ids:
            conn.execute(
                "INSERT INTO hand_players"
                " (hand_id, player_id, position, starting_stack,"
                "  vpip, pfr, three_bet, went_to_showdown, net_result)"
                " VALUES (?, ?, 'BB', 5000, 1, 1, 0, 0, 100)",
                (hid, vid),
            )
        seq = 1
        for vid in villain_ids:
            conn.execute(
                "INSERT INTO actions"
                " (hand_id, player_id, is_hero, street, action_type,"
                "  amount, amount_to_call, pot_before, is_all_in, sequence)"
                " VALUES (?, ?, 0, 'PREFLOP', 'RAISE', 300, 0, 150, 0, ?)",
                (hid, vid, seq),
            )
            seq += 1
        if add_aggressor and len(villain_ids) >= 2:
            conn.execute(
                "INSERT INTO actions"
                " (hand_id, player_id, is_hero, street, action_type,"
                "  amount, amount_to_call, pot_before, is_all_in, sequence)"
                " VALUES (?, ?, 0, 'FLOP', 'BET', 300, 0, 800, 0, ?)",
                (hid, villain_ids[1], seq),
            )
            seq += 1
        hero_seq = seq
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'FLOP', 'CALL', 300, 300, 800, 0, ?)",
            (hid, hero_id, hero_seq),
        )
        conn.commit()
        return sid, hid, hero_id, villain_ids, hero_seq

    def test_heads_up_returns_the_villain(self, conn):
        """Heads-up: identify_primary_villain returns the single non-hero player."""
        from pokerhero.analysis.stats import identify_primary_villain

        _, hid, hero_id, villain_ids, hero_seq = self._seed(conn, n_villains=1)
        result = identify_primary_villain(conn, hid, hero_id, hero_seq, "FLOP")
        assert result == villain_ids[0]

    def test_multiway_returns_last_aggressor_on_street(self, conn):
        """Multi-way: last BET/RAISE before hero on this street is primary villain."""
        from pokerhero.analysis.stats import identify_primary_villain

        _, hid, hero_id, villain_ids, hero_seq = self._seed(
            conn, n_villains=2, add_aggressor=True
        )
        result = identify_primary_villain(conn, hid, hero_id, hero_seq, "FLOP")
        assert result == villain_ids[1]  # villain1 bet on the flop

    def test_multiway_no_aggressor_returns_most_observed(self, conn):
        """Multi-way, no FLOP aggressor: villain with most session hands returned."""
        from pokerhero.analysis.stats import identify_primary_villain

        sid, hid, hero_id, villain_ids, hero_seq = self._seed(
            conn, n_villains=2, add_aggressor=False
        )
        # Give villain_ids[0] extra hands to make them "most observed"
        for i in range(5):
            extra_hid = conn.execute(
                "INSERT INTO hands"
                " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
                "  rake, timestamp)"
                " VALUES (?, ?, 500, 0, 0, '2024-01-01T00:01:00')",
                (f"HX{i}", sid),
            ).lastrowid
            conn.execute(
                "INSERT INTO hand_players"
                " (hand_id, player_id, position, starting_stack,"
                "  vpip, pfr, three_bet, went_to_showdown, net_result)"
                " VALUES (?, ?, 'BB', 5000, 1, 0, 0, 0, 100)",
                (extra_hid, villain_ids[0]),
            )
        conn.commit()
        result = identify_primary_villain(conn, hid, hero_id, hero_seq, "FLOP")
        assert result == villain_ids[0]


# ---------------------------------------------------------------------------
# TestCalculateSessionEvs
# ---------------------------------------------------------------------------


class TestCalculateSessionEvs:
    """Tests for the calculate_session_evs orchestrator."""

    _FAST_SETTINGS: dict[str, float] = {
        "range_vpip_prior": 26.0,
        "range_pfr_prior": 14.0,
        "range_3bet_prior": 6.0,
        "range_4bet_prior": 3.0,
        "range_prior_weight": 30.0,
        "range_sample_count": 50.0,  # small for test speed
        "range_continue_pct_passive": 65.0,
        "range_continue_pct_aggressive": 40.0,
    }

    @pytest.fixture
    def db_file(self, tmp_path):
        from pokerhero.database.db import init_db

        db_path = str(tmp_path / "test.db")
        conn = init_db(db_path)
        yield conn, db_path
        conn.close()

    def _seed_hand(
        self,
        conn,
        hero_cards: str | None = "Ac Kd",
        villain_cards: str | None = None,
        villain_pfr: int = 1,
        villain_three_bet: int = 0,
        board_flop: str | None = "Qs Jd 2c",
        board_turn: str | None = "7h",
        board_river: str | None = "3s",
        hero_action_street: str = "RIVER",
        villain_flop_action: str | None = None,
        villain_turn_action: str | None = None,
    ) -> tuple[int, int, int, int, int]:
        """Seed session/hand/players/actions.

        Returns (session_id, hand_id, hero_id, villain_id, hero_action_id).
        """
        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        villain_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('villain', 'Villain')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-01-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('H1', ?, 1200, 0, 0, '2024-01-01T00:00:00', ?, ?, ?)",
            (sid, board_flop, board_turn, board_river),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, ?, 1, 1, 0, 0, -400)",
            (hid, hero_id, hero_cards),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, ?, 1, ?, ?, 0, 400)",
            (hid, villain_id, villain_cards, villain_pfr, villain_three_bet),
        )
        seq = 1
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'RAISE', 300, 0, 150, 0, ?)",
            (hid, villain_id, seq),
        )
        seq += 1
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'PREFLOP', 'CALL', 300, 300, 150, 0, ?)",
            (hid, hero_id, seq),
        )
        seq += 1
        if villain_flop_action:
            conn.execute(
                "INSERT INTO actions"
                " (hand_id, player_id, is_hero, street, action_type,"
                "  amount, amount_to_call, pot_before, is_all_in, sequence)"
                " VALUES (?, ?, 0, 'FLOP', ?, 200, 0, 600, 0, ?)",
                (hid, villain_id, villain_flop_action, seq),
            )
            seq += 1
        if villain_turn_action:
            conn.execute(
                "INSERT INTO actions"
                " (hand_id, player_id, is_hero, street, action_type,"
                "  amount, amount_to_call, pot_before, is_all_in, sequence)"
                " VALUES (?, ?, 0, 'TURN', ?, 200, 0, 1000, 0, ?)",
                (hid, villain_id, villain_turn_action, seq),
            )
            seq += 1
        hero_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, ?, 'CALL', 400, 400, 800, 0, ?)",
            (hid, hero_id, hero_action_street, seq),
        ).lastrowid
        conn.commit()
        return sid, hid, hero_id, villain_id, hero_action_id

    def test_exact_ev_written_when_villain_cards_known(self, db_file):
        """CALL on RIVER with known villain cards writes ev_type='exact' to cache."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        sid, _, hero_id, _, action_id = self._seed_hand(
            conn,
            hero_cards="Ac Kd",
            villain_cards="2c 3d",
            board_flop="Qs Jd 4h",
            board_turn="7s",
            board_river="8h",
            hero_action_street="RIVER",
        )
        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, action_id, hero_id)
        assert row is not None
        assert row["ev_type"] == "exact"
        assert 0.0 <= float(row["equity"]) <= 1.0

    def test_range_ev_written_for_flop_action_no_history(self, db_file):
        """CALL on FLOP with unknown villain cards writes ev_type='range'."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        sid, _, hero_id, _, action_id = self._seed_hand(
            conn,
            hero_cards="Ac Kd",
            villain_cards=None,
            villain_pfr=1,
            board_flop="Qs Jd 2h",
            board_turn=None,
            board_river=None,
            hero_action_street="FLOP",
        )
        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, action_id, hero_id)
        assert row is not None
        assert row["ev_type"] == "range"
        assert row["contracted_range_size"] is not None
        assert int(row["contracted_range_size"]) >= 5

    def test_range_ev_river_action_uses_street_history(self, db_file):
        """CALL on RIVER with villain BET on FLOP+TURN uses 2-street contraction."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        sid, _, hero_id, _, action_id = self._seed_hand(
            conn,
            hero_cards="Ac Kd",
            villain_cards=None,
            villain_pfr=1,
            board_flop="Qs Jd 2h",
            board_turn="7s",
            board_river="8c",
            hero_action_street="RIVER",
            villain_flop_action="BET",
            villain_turn_action="BET",
        )
        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, action_id, hero_id)
        assert row is not None
        assert row["ev_type"] == "range"
        assert int(row["contracted_range_size"]) >= 5

    def test_action_skipped_when_hero_cards_unknown(self, db_file):
        """Hero action with NULL hole_cards produces no cache row."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        sid, _, hero_id, _, action_id = self._seed_hand(
            conn,
            hero_cards=None,
            villain_cards="2c 3d",
            hero_action_street="RIVER",
        )
        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n == 0
        assert get_action_ev(conn, action_id, hero_id) is None

    def test_returns_count_of_rows_written(self, db_file):
        """Return value equals the number of action_ev_cache rows written."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs

        sid, _, hero_id, _, _ = self._seed_hand(
            conn,
            hero_cards="Ac Kd",
            villain_cards="2c 3d",
            board_flop="Qs Jd 4h",
            board_turn="7s",
            board_river="8h",
            hero_action_street="RIVER",
        )
        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        count = conn.execute(
            "SELECT COUNT(*) FROM action_ev_cache WHERE hero_id = ?", (hero_id,)
        ).fetchone()[0]
        assert n == count

    def test_fold_facing_bet_writes_cache_row(self, db_file):
        """FOLD with amount_to_call > 0 (facing bet) writes EV to cache."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        # Seed a hand where the hero FOLDS on the river facing a bet
        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_fold', 'HeroFold')"
        ).lastrowid
        villain_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('vil_fold', 'VilFold')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-02-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('HF1', ?, 1200, 0, 0, '2024-02-01T00:00:00',"
            " 'Qs Jd 4h', '7s', '8h')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, 'Ac Kd', 1, 1, 0, 0, -200)",
            (hid, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, '2c 3d', 1, 1, 0, 1, 200)",
            (hid, villain_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'RIVER', 'BET', 400, 0, 800, 0, 1)",
            (hid, villain_id),
        )
        fold_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'FOLD', 0, 400, 800, 0, 2)",
            (hid, hero_id),
        ).lastrowid
        conn.commit()

        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, fold_action_id, hero_id)
        assert row is not None

    def test_fold_not_facing_bet_skipped(self, db_file):
        """FOLD with amount_to_call = 0 (e.g. open fold) is not cached."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_ofold', 'HeroOFold')"
        ).lastrowid
        villain_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('vil_ofold', 'VilOFold')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-03-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('HO1', ?, 600, 0, 0, '2024-03-01T00:00:00',"
            " 'Qs Jd 4h', '7s', '8h')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, 'Ac Kd', 0, 0, 0, 0, 0)",
            (hid, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, '2c 3d', 1, 0, 0, 0, 0)",
            (hid, villain_id),
        )
        # Hero open-folds preflop (amount_to_call = 0, just the open)
        fold_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'PREFLOP', 'FOLD', 0, 0, 150, 0, 1)",
            (hid, hero_id),
        ).lastrowid
        conn.commit()

        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n == 0
        row = get_action_ev(conn, fold_action_id, hero_id)
        assert row is None

    def test_multiway_exact_ev_when_multiple_villain_cards_known(self, db_file):
        """Multiway hand with 2 known villain hands writes ev_type='exact_multiway'."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_mw', 'HeroMW')"
        ).lastrowid
        v1_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('villain1_mw', 'V1')"
        ).lastrowid
        v2_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('villain2_mw', 'V2')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-04-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('MW1', ?, 2000, 0, 0, '2024-04-01T00:00:00',"
            " 'Qs Jd 4h', '7s', '8c')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, 'Ac Kd', 1, 1, 0, 1, -400)",
            (hid, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'CO', 5000, '2c 3d', 1, 1, 0, 1, 200)",
            (hid, v1_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, '9c 8s', 1, 0, 0, 1, 200)",
            (hid, v2_id),
        )
        # Preflop: V1 raises, V2 calls, Hero calls
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'RAISE', 300, 0, 150, 0, 1)",
            (hid, v1_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'CALL', 300, 300, 450, 0, 2)",
            (hid, v2_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'PREFLOP', 'CALL', 300, 300, 750, 0, 3)",
            (hid, hero_id),
        )
        # River: V1 bets, V2 calls, Hero calls
        hero_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'CALL', 400, 400, 1600, 0, 6)",
            (hid, hero_id),
        ).lastrowid
        conn.commit()

        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, hero_action_id, hero_id)
        assert row is not None
        assert row["ev_type"] == "exact_multiway"
        assert 0.0 <= float(row["equity"]) <= 1.0

    def test_multiway_exact_ev_lower_than_headsup(self, db_file):
        """Multiway equity must be ≤ heads-up equity for the same hero hand."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        # --- Heads-up hand ---
        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_cmp', 'HeroCmp')"
        ).lastrowid
        v1_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('v1_cmp', 'V1Cmp')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-05-01')"
        ).lastrowid
        hid_hu = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('CmpHU', ?, 1200, 0, 0, '2024-05-01T00:00:00',"
            " 'Ah 8d 2c', '5s', '3h')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, '7s 8s', 1, 1, 0, 1, -400)",
            (hid_hu, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, '2d 3d', 1, 1, 0, 1, 400)",
            (hid_hu, v1_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'RAISE', 300, 0, 150, 0, 1)",
            (hid_hu, v1_id),
        )
        hu_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'CALL', 400, 400, 800, 0, 2)",
            (hid_hu, hero_id),
        ).lastrowid

        # --- Multiway hand (same hero cards, same board, same primary villain) ---
        v2_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('v2_cmp', 'V2Cmp')"
        ).lastrowid
        hid_mw = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('CmpMW', ?, 2000, 0, 0, '2024-05-01T00:01:00',"
            " 'Ah 8d 2c', '5s', '3h')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, '7s 8s', 1, 1, 0, 1, -400)",
            (hid_mw, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'CO', 5000, '2d 3d', 1, 1, 0, 1, 200)",
            (hid_mw, v1_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, 'Jc Tc', 1, 0, 0, 1, 200)",
            (hid_mw, v2_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'RAISE', 300, 0, 150, 0, 1)",
            (hid_mw, v1_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'CALL', 300, 300, 450, 0, 2)",
            (hid_mw, v2_id),
        )
        mw_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'CALL', 400, 400, 1600, 0, 3)",
            (hid_mw, hero_id),
        ).lastrowid
        conn.commit()

        calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        hu_row = get_action_ev(conn, hu_action_id, hero_id)
        mw_row = get_action_ev(conn, mw_action_id, hero_id)
        assert hu_row is not None and mw_row is not None
        assert float(mw_row["equity"]) <= float(hu_row["equity"])

    def test_bet_action_has_fold_equity(self, db_file):
        """BET action writes fold_equity_pct to action_ev_cache."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_fe', 'HeroFE')"
        ).lastrowid
        villain_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('vil_fe', 'VilFE')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-06-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('FE1', ?, 1200, 0, 0, '2024-06-01T00:00:00',"
            " 'Qs Jd 4h', '7s', '8c')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, '2d 3c', 1, 1, 0, 1, -400)",
            (hid, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, 'Ac Kd', 1, 0, 0, 1, 400)",
            (hid, villain_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'CALL', 100, 100, 150, 0, 1)",
            (hid, villain_id),
        )
        # Hero BETS on the river (a bluff with 2d3c)
        bet_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'BET', 400, 0, 800, 0, 2)",
            (hid, hero_id),
        ).lastrowid
        conn.commit()

        n = calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        assert n >= 1
        row = get_action_ev(conn, bet_action_id, hero_id)
        assert row is not None
        assert row["fold_equity_pct"] is not None
        assert 0.0 < float(row["fold_equity_pct"]) < 100.0

    def test_call_action_has_no_fold_equity(self, db_file):
        """CALL action has fold_equity_pct = NULL."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        sid, _, hero_id, _, action_id = self._seed_hand(
            conn,
            hero_cards="Ac Kd",
            villain_cards="2c 3d",
            board_flop="Qs Jd 4h",
            board_turn="7s",
            board_river="8h",
            hero_action_street="RIVER",
        )
        calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        row = get_action_ev(conn, action_id, hero_id)
        assert row is not None
        assert row["fold_equity_pct"] is None

    def test_bet_ev_includes_fold_equity_component(self, db_file):
        """BET EV with fold equity must be higher than pure showdown EV for a bluff."""
        conn, db_path = db_file
        from pokerhero.analysis.stats import calculate_session_evs
        from pokerhero.database.db import get_action_ev

        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('hero_fecmp', 'HeroFECmp')"
        ).lastrowid
        villain_id = conn.execute(
            "INSERT INTO players (username, preferred_name)"
            " VALUES ('vil_fecmp', 'VilFECmp')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-07-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp, board_flop, board_turn, board_river)"
            " VALUES ('FECmp', ?, 1200, 0, 0, '2024-07-01T00:00:00',"
            " 'Qs Jd 4h', '7s', '8c')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, '2d 3c', 1, 1, 0, 1, -400)",
            (hid, hero_id),
        )
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BB', 5000, 'Ac Kd', 1, 0, 0, 1, 400)",
            (hid, villain_id),
        )
        conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 0, 'PREFLOP', 'CALL', 100, 100, 150, 0, 1)",
            (hid, villain_id),
        )
        bet_action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'BET', 400, 0, 800, 0, 2)",
            (hid, hero_id),
        ).lastrowid
        conn.commit()

        calculate_session_evs(db_path, sid, hero_id, self._FAST_SETTINGS)
        row = get_action_ev(conn, bet_action_id, hero_id)
        assert row is not None

        # Compute pure showdown EV for comparison:
        # showdown_ev = equity * pot_to_win - wager
        equity = float(row["equity"])
        pot_to_win = 800 + 400  # pot_before + wager
        wager = 400
        showdown_ev = equity * pot_to_win - wager
        actual_ev = float(row["ev"])
        # With fold equity, EV must be strictly higher than showdown EV
        assert actual_ev > showdown_ev


# ---------------------------------------------------------------------------
# TestGetSessionEvStatus
# ---------------------------------------------------------------------------


class TestGetSessionEvStatus:
    """Tests for get_session_ev_status query function."""

    @pytest.fixture
    def conn(self, tmp_path):
        from pokerhero.database.db import init_db

        c = init_db(str(tmp_path / "test.db"))
        yield c
        c.close()

    def _seed(self, conn):
        """Seed minimal session + hand + player + action.

        Returns (sid, action_id, player_id).
        """
        player_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-01-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp)"
            " VALUES ('H1', ?, 1000, 0, 0, '2024-01-01T00:00:00')",
            (sid,),
        ).lastrowid
        action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'FLOP', 'CALL', 100, 100, 200, 0, 1)",
            (hid, player_id),
        ).lastrowid
        conn.commit()
        return sid, action_id, player_id

    def test_no_cache_rows_returns_zero(self, conn):
        """Session with no action_ev_cache rows returns (0, None)."""
        from pokerhero.analysis.queries import get_session_ev_status

        sid, _, _ = self._seed(conn)
        count, computed_at = get_session_ev_status(conn, sid)
        assert count == 0
        assert computed_at is None

    def test_with_cache_rows_returns_count_and_date(self, conn):
        """Session with cache rows returns (n, computed_at string)."""
        from pokerhero.analysis.queries import get_session_ev_status

        sid, action_id, player_id = self._seed(conn)
        conn.execute(
            "INSERT INTO action_ev_cache"
            " (action_id, hero_id, equity, ev, ev_type, sample_count, computed_at)"
            " VALUES (?, ?, 0.6, 10.0, 'exact', 1000, '2024-01-15T12:00:00')",
            (action_id, player_id),
        )
        conn.commit()
        count, computed_at = get_session_ev_status(conn, sid)
        assert count == 1
        assert computed_at is not None
        assert "2024-01-15" in str(computed_at)


# ---------------------------------------------------------------------------
# TestEvStatusLabel
# ---------------------------------------------------------------------------


class TestEvStatusLabel:
    """Tests for _ev_status_label helper in sessions.py."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    @pytest.fixture
    def conn(self, tmp_path):
        from pokerhero.database.db import init_db

        c = init_db(str(tmp_path / "test.db"))
        yield c
        c.close()

    def _seed(self, conn):
        """Seed minimal session + action. Returns (sid, action_id, player_id)."""
        player_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-01-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp)"
            " VALUES ('H1', ?, 1000, 0, 0, '2024-01-01T00:00:00')",
            (sid,),
        ).lastrowid
        action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'FLOP', 'CALL', 100, 100, 200, 0, 1)",
            (hid, player_id),
        ).lastrowid
        conn.commit()
        return sid, action_id, player_id

    def test_no_rows_returns_calculate_label(self, conn):
        """Session with no cache rows returns a label containing the 📊 emoji."""
        from pokerhero.frontend.pages.sessions import _ev_status_label

        sid, _, _ = self._seed(conn)
        label = _ev_status_label(conn, sid)
        assert "📊" in label

    def test_with_rows_returns_ready_label_with_date(self, conn):
        """Session with cache rows returns a label containing ✅ and the date."""
        from pokerhero.frontend.pages.sessions import _ev_status_label

        sid, action_id, player_id = self._seed(conn)
        conn.execute(
            "INSERT INTO action_ev_cache"
            " (action_id, hero_id, equity, ev, ev_type, sample_count, computed_at)"
            " VALUES (?, ?, 0.6, 10.0, 'exact', 1000, '2024-03-20T12:00:00')",
            (action_id, player_id),
        )
        conn.commit()
        label = _ev_status_label(conn, sid)
        assert "✅" in label
        assert "2024-03-20" in label


class TestBatchEvStatusLabels:
    """H3: _batch_ev_status_labels returns labels for multiple sessions in one query."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    @pytest.fixture
    def conn(self, tmp_path):
        from pokerhero.database.db import init_db

        c = init_db(str(tmp_path / "test.db"))
        yield c
        c.close()

    def _seed_sessions(self, conn, n=3):
        """Create n sessions with one hand+action each; return list of session ids."""
        pid = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        sids = []
        for i in range(n):
            sid = conn.execute(
                "INSERT INTO sessions"
                " (game_type, limit_type, max_seats,"
                "  small_blind, big_blind, ante, start_time)"
                " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, ?)",
                (f"2024-01-0{i + 1}",),
            ).lastrowid
            hid = conn.execute(
                "INSERT INTO hands"
                " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
                "  rake, timestamp)"
                " VALUES (?, ?, 1000, 0, 0, '2024-01-01T00:00:00')",
                (f"H{i}", sid),
            ).lastrowid
            conn.execute(
                "INSERT INTO actions"
                " (hand_id, player_id, is_hero, street, action_type,"
                "  amount, amount_to_call, pot_before, is_all_in, sequence)"
                " VALUES (?, ?, 1, 'FLOP', 'CALL', 100, 100, 200, 0, 1)",
                (hid, pid),
            )
            sids.append(sid)
        conn.commit()
        return sids, pid

    def test_returns_dict_keyed_by_session_id(self, conn):
        from pokerhero.frontend.pages.sessions import _batch_ev_status_labels

        sids, _ = self._seed_sessions(conn, 2)
        result = _batch_ev_status_labels(conn, sids)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(sids)

    def test_all_calculate_when_no_cache(self, conn):
        from pokerhero.frontend.pages.sessions import _batch_ev_status_labels

        sids, _ = self._seed_sessions(conn, 3)
        result = _batch_ev_status_labels(conn, sids)
        for sid in sids:
            assert "📊" in result[sid]

    def test_mixed_status(self, conn):
        """One session with cache, two without — only the cached one shows ✅."""
        from pokerhero.frontend.pages.sessions import _batch_ev_status_labels

        sids, pid = self._seed_sessions(conn, 3)
        # Add cache row for first session only
        action_id = conn.execute(
            "SELECT a.id FROM actions a JOIN hands h ON a.hand_id = h.id"
            " WHERE h.session_id = ? LIMIT 1",
            (sids[0],),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO action_ev_cache"
            " (action_id, hero_id, equity, ev, ev_type, sample_count, computed_at)"
            " VALUES (?, ?, 0.6, 10.0, 'exact', 1000, '2024-03-20T12:00:00')",
            (action_id, pid),
        )
        conn.commit()
        result = _batch_ev_status_labels(conn, sids)
        assert "✅" in result[sids[0]]
        assert "📊" in result[sids[1]]
        assert "📊" in result[sids[2]]


# ---------------------------------------------------------------------------
# TestSessionTableEvColumn
# ---------------------------------------------------------------------------


class TestSessionTableEvColumn:
    """Tests for the EV Status column added to the session DataTable."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_df(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1],
                "start_time": ["2026-01-10"],
                "small_blind": [50],
                "big_blind": [100],
                "hands_played": [20],
                "net_profit": [500.0],
                "is_favorite": [0],
                "ev_status": ["📊 Calculate"],
            }
        )

    def test_column_names_includes_ev_status(self):
        """Session table columns include the EV Status column."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        col_names = [c["name"] for c in result.columns]
        assert "EV Status" in col_names

    def test_ev_status_data_in_rows(self):
        """Each data row contains an 'ev_status' key."""
        from pokerhero.frontend.pages.sessions import _build_session_table

        result = _build_session_table(self._make_df())
        assert all("ev_status" in row for row in result.data)


# ---------------------------------------------------------------------------
# TestCalculateEvSection
# ---------------------------------------------------------------------------


class TestCalculateEvSection:
    """Tests for _build_calculate_ev_section render helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_returns_html_div(self):
        """_build_calculate_ev_section returns an html.Div."""
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_calculate_ev_section

        result = _build_calculate_ev_section()
        assert isinstance(result, html.Div)

    def test_has_calculate_button(self):
        """Section contains a component with id 'calculate-ev-btn'."""
        from pokerhero.frontend.pages.sessions import _build_calculate_ev_section

        result = _build_calculate_ev_section()
        assert "calculate-ev-btn" in repr(result)


# ---------------------------------------------------------------------------
# TestBuildEvCell
# ---------------------------------------------------------------------------


class TestBuildEvCell:
    """Tests for _build_ev_cell display helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _exact_row(self, ev: float = 10.0, equity: float = 0.67) -> dict[str, object]:
        return {
            "action_id": 1,
            "hero_id": 1,
            "equity": equity,
            "ev": ev,
            "ev_type": "exact",
            "blended_vpip": None,
            "blended_pfr": None,
            "blended_3bet": None,
            "villain_preflop_action": None,
            "contracted_range_size": None,
            "sample_count": 1000,
            "computed_at": "2024-01-01T00:00:00",
        }

    def _range_row(self, ev: float = 3.4, equity: float = 0.54) -> dict[str, object]:
        return {
            "action_id": 1,
            "hero_id": 1,
            "equity": equity,
            "ev": ev,
            "ev_type": "range",
            "blended_vpip": 0.26,
            "blended_pfr": 0.14,
            "blended_3bet": 0.06,
            "villain_preflop_action": "3bet",
            "contracted_range_size": 31,
            "sample_count": 1000,
            "computed_at": "2024-01-01T00:00:00",
        }

    def test_no_cache_returns_dash(self):
        """None cache_row returns the dash placeholder string."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        assert _build_ev_cell(None, "CALL") == "—"

    def test_exact_shows_equity_percent(self):
        """Exact EV row output contains 'Equity:' text."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._exact_row(), "CALL")
        assert "Equity:" in repr(result)

    def test_exact_shows_ev_value(self):
        """Exact EV row output contains 'EV:' text."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._exact_row(), "CALL")
        assert "EV:" in repr(result)

    def test_exact_call_neg_ev_shows_fold_better(self):
        """CALL with negative exact EV shows fold comparison."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._exact_row(ev=-5.0), "CALL")
        assert "Fold" in repr(result)

    def test_exact_bet_neg_ev_no_fold_comparison(self):
        """BET with negative exact EV does NOT show fold comparison."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._exact_row(ev=-5.0), "BET")
        assert "Fold" not in repr(result)

    def test_range_shows_est_prefix(self):
        """Range EV row uses 'Est.' prefix on equity and EV values."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._range_row(), "CALL")
        assert "Est." in repr(result)

    def test_range_shows_info_tooltip(self):
        """Range EV row includes a ℹ tooltip element."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        result = _build_ev_cell(self._range_row(), "CALL")
        assert "ℹ" in repr(result)

    def test_fold_pos_ev_shows_should_have_called(self):
        """FOLD with positive call-EV shows a 'should have called' warning."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        # ev=+8.4 means calling would have been +EV → folding was a mistake
        result = repr(_build_ev_cell(self._exact_row(ev=8.4), "FOLD")).lower()
        assert "call" in result

    def test_fold_neg_ev_shows_good_fold(self):
        """FOLD with negative call-EV confirms the fold was correct."""
        from pokerhero.frontend.pages.sessions import _build_ev_cell

        # ev=-3.2 means calling would have been -EV → fold was correct
        result = repr(_build_ev_cell(self._exact_row(ev=-3.2), "FOLD")).lower()
        assert "fold" in result


# ---------------------------------------------------------------------------
# TestGetSessionShowdownEvs
# ---------------------------------------------------------------------------


class TestGetSessionShowdownEvs:
    """Tests for get_session_showdown_evs query function."""

    @pytest.fixture
    def conn(self, tmp_path):
        from pokerhero.database.db import init_db

        c = init_db(str(tmp_path / "test.db"))
        yield c
        c.close()

    def _seed(self, conn, *, with_ev_cache: bool = False, street: str = "RIVER"):
        """Seed session/hand/players/action; optionally insert an exact ev cache row.

        Returns (session_id, action_id, hero_id).
        """
        hero_id = conn.execute(
            "INSERT INTO players (username, preferred_name) VALUES ('hero', 'Hero')"
        ).lastrowid
        sid = conn.execute(
            "INSERT INTO sessions"
            " (game_type, limit_type, max_seats,"
            "  small_blind, big_blind, ante, start_time)"
            " VALUES ('NLHE', 'No Limit', 6, 50, 100, 0, '2024-01-01')"
        ).lastrowid
        hid = conn.execute(
            "INSERT INTO hands"
            " (source_hand_id, session_id, total_pot, uncalled_bet_returned,"
            "  rake, timestamp)"
            " VALUES ('H1', ?, 1000, 0, 0, '2024-01-01T00:00:00')",
            (sid,),
        ).lastrowid
        conn.execute(
            "INSERT INTO hand_players"
            " (hand_id, player_id, position, starting_stack, hole_cards,"
            "  vpip, pfr, three_bet, went_to_showdown, net_result)"
            " VALUES (?, ?, 'BTN', 5000, 'Ah Kh', 1, 1, 0, 1, -500)",
            (hid, hero_id),
        )
        action_id = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, ?, 'CALL', 100, 100, 200, 0, 1)",
            (hid, hero_id, street),
        ).lastrowid
        if with_ev_cache:
            conn.execute(
                "INSERT INTO action_ev_cache"
                " (action_id, hero_id, equity, ev, ev_type, sample_count, computed_at)"
                " VALUES (?, ?, 0.75, 12.5, 'exact', 1000, '2024-01-15T12:00:00')",
                (action_id, hero_id),
            )
        conn.commit()
        return sid, action_id, hero_id

    def test_empty_when_no_cache(self, conn):
        """Session with no action_ev_cache rows returns empty DataFrame."""
        from pokerhero.analysis.queries import get_session_showdown_evs

        sid, _, hero_id = self._seed(conn, with_ev_cache=False)
        df = get_session_showdown_evs(conn, sid, hero_id)
        assert df.empty

    def test_returns_equity_for_exact_river_action(self, conn):
        """Exact EV cache row on RIVER is returned with equity and net_result."""
        from pokerhero.analysis.queries import get_session_showdown_evs

        sid, _, hero_id = self._seed(conn, with_ev_cache=True, street="RIVER")
        df = get_session_showdown_evs(conn, sid, hero_id)
        assert len(df) == 1
        assert abs(float(df.iloc[0]["equity"]) - 0.75) < 0.001
        assert float(df.iloc[0]["net_result"]) == pytest.approx(-500.0)

    def test_deduplicates_multiple_qualifying_actions_per_hand(self, conn):
        """Multiple exact EV cache rows for the same hand yield one row."""
        from pokerhero.analysis.queries import get_session_showdown_evs

        sid, action_id, hero_id = self._seed(conn, with_ev_cache=True, street="RIVER")
        # Insert a second cache row for a different action in the SAME hand
        hid = conn.execute(
            "SELECT hand_id FROM actions WHERE id = ?", (action_id,)
        ).fetchone()[0]
        action_id2 = conn.execute(
            "INSERT INTO actions"
            " (hand_id, player_id, is_hero, street, action_type,"
            "  amount, amount_to_call, pot_before, is_all_in, sequence)"
            " VALUES (?, ?, 1, 'RIVER', 'BET', 200, 0, 400, 1, 2)",
            (hid, hero_id),
        ).lastrowid
        conn.execute(
            "INSERT INTO action_ev_cache"
            " (action_id, hero_id, equity, ev, ev_type, sample_count, computed_at)"
            " VALUES (?, ?, 0.80, 20.0, 'exact', 1000, '2024-01-15T12:00:01')",
            (action_id2, hero_id),
        )
        conn.commit()
        df = get_session_showdown_evs(conn, sid, hero_id)
        assert len(df) == 1
        # Should pick the LATEST action (action_id2, equity=0.80), not the first.
        assert abs(float(df.iloc[0]["equity"]) - 0.80) < 0.001

    def test_returns_equity_for_exact_flop_action(self, conn):
        """Exact EV cache row on FLOP is returned (not filtered out by street)."""
        from pokerhero.analysis.queries import get_session_showdown_evs

        sid, _, hero_id = self._seed(conn, with_ev_cache=True, street="FLOP")
        df = get_session_showdown_evs(conn, sid, hero_id)
        assert len(df) == 1
        assert abs(float(df.iloc[0]["equity"]) - 0.75) < 0.001


# ===========================================================================
# TestFlaggedHandsLinks — lucky/unlucky hands link to action view
# ===========================================================================


class TestFlaggedHandsLinks:
    """Flagged hands (Lucky/Unlucky) must be clickable links to the action view."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_ev_df(self) -> "pd.DataFrame":  # noqa: F821
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [42],
                "source_hand_id": ["HS-42"],
                "equity": [0.25],  # wins with low equity → Lucky
                "net_result": [200.0],
            }
        )

    def test_flagged_hand_contains_link_to_action_view(self):
        """Lucky hand entry must be a dcc.Link with hand_id and session_id."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        result = str(_build_flagged_hands_list(self._make_ev_df(), session_id=5))
        assert "hand_id=42" in result, "hand_id not found in link"
        assert "session_id=5" in result, "session_id not found in link"

    def test_flagged_hand_link_points_to_sessions_path(self):
        """Link href must use /sessions path."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        result = str(_build_flagged_hands_list(self._make_ev_df(), session_id=7))
        assert "/sessions" in result

    def test_flagged_hand_still_shows_source_hand_id(self):
        """Link text must still display the source_hand_id (display label)."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        result = str(_build_flagged_hands_list(self._make_ev_df(), session_id=5))
        assert "HS-42" in result


# ===========================================================================
# TestSessionPositionTablePnl — position table includes Net P&L column
# ===========================================================================


class TestSessionPositionTablePnl:
    """Position breakdown table must include a Net P&L column."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _make_kpis_df(self) -> "pd.DataFrame":  # noqa: F821
        import pandas as pd

        return pd.DataFrame(
            {
                "position": ["BTN", "BTN", "BB"],
                "vpip": [1, 0, 1],
                "pfr": [1, 0, 0],
                "net_result": [150.0, -50.0, 30.0],
                "went_to_showdown": [0, 0, 0],
                "hole_cards": [None, None, None],
                "big_blind": [100, 100, 100],
                "saw_flop": [1, 0, 0],
            }
        )

    def _call_position_table(self) -> str:

        from pokerhero.database.db import init_db
        from pokerhero.frontend.pages.sessions import _build_session_position_table

        conn = init_db(":memory:")
        result = str(_build_session_position_table(self._make_kpis_df(), conn))
        conn.close()
        return result

    def test_position_table_has_net_pnl_header(self):
        """Position table must include a 'Net P&L' column header."""
        assert "Net P&L" in self._call_position_table()

    def test_position_table_shows_btn_pnl(self):
        """Position table must show the summed P&L for BTN (150 + -50 = +100)."""
        result = self._call_position_table()
        assert "+100" in result


# ---------------------------------------------------------------------------
# TestSearchInputWiring
# ---------------------------------------------------------------------------


class TestSearchInputWiring:
    """Verify _render wiring for URL-based and consumed-search navigation."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_render_callback_has_search_as_input_not_state(self):
        """_pages_location.search must be an Input of _render, not a State.

        When a dcc.Link changes only the URL search (same pathname), Dash only
        fires callbacks whose inputs changed. If search is registered as State,
        clicking a flagged-hand link (/sessions?session_id=X&hand_id=Y) from
        the session report view never triggers _render and navigation silently
        fails.
        """
        import pytest
        from dash._callback import GLOBAL_CALLBACK_MAP

        search_entry = {"id": "_pages_location", "property": "search"}

        for key, cb in GLOBAL_CALLBACK_MAP.items():
            if "drill-down-content" in key and "children" in key:
                inputs = cb.get("inputs", [])
                state = cb.get("state", [])
                assert search_entry in inputs, (
                    "_pages_location.search must be an Input of _render "
                    "so intra-page dcc.Link clicks trigger re-render"
                )
                assert search_entry not in state
                return

        pytest.fail("Could not find _render callback in GLOBAL_CALLBACK_MAP")

    def test_render_callback_has_consumed_search_state(self):
        """_render must have consumed-search as State and Output."""
        import pytest
        from dash._callback import GLOBAL_CALLBACK_MAP

        consumed_state = {"id": "consumed-search", "property": "data"}

        for key, cb in GLOBAL_CALLBACK_MAP.items():
            if (
                "drill-down-content" in key
                and "children" in key
                and "consumed-search" in key
            ):
                state = cb.get("state", [])
                assert consumed_state in state, (
                    "_render must have consumed-search as State "
                    "to track which URL params have been consumed"
                )
                return

        pytest.fail("consumed-search not found as Output in _render callback")


# ---------------------------------------------------------------------------
# TestLoadSessionReportGuard
# ---------------------------------------------------------------------------


class TestLoadSessionReportGuard:
    """_load_session_report guard must allow both URL-based and click-based nav.

    The guard needs both drill-down-state AND _pages_location.search as State:
    - URL navigation (dashboard highlights): store is stale (default level),
      but URL has correct params → allow via URL check.
    - Click-based navigation (session row click): URL may be empty,
      but store has correct level=report → allow via store check.
    """

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_callback_has_both_search_and_store_state(self):
        """_load_session_report must have both URL search and store as State."""
        import pytest
        from dash._callback import GLOBAL_CALLBACK_MAP

        search_entry = {"id": "_pages_location", "property": "search"}
        store_entry = {"id": "drill-down-state", "property": "data"}

        for _key, cb in GLOBAL_CALLBACK_MAP.items():
            if any(
                i.get("id") == "pending-session-report" for i in cb.get("inputs", [])
            ):
                state = cb.get("state", [])
                assert search_entry in state, (
                    "_load_session_report must have _pages_location.search "
                    "as State for URL-based guard"
                )
                assert store_entry in state, (
                    "_load_session_report must have drill-down-state "
                    "as State for click-based guard"
                )
                return

        pytest.fail("Could not find _load_session_report in GLOBAL_CALLBACK_MAP")

    def test_allows_report_when_url_matches(self):
        """Must not PreventUpdate when URL says report, even if store is default."""
        import dash

        from pokerhero.frontend.pages.sessions import _load_session_report

        try:
            _load_session_report(
                session_id=0,
                state={"level": "sessions"},
                search="?session_id=0",
            )
        except TypeError:
            pytest.fail("_load_session_report does not accept both state and search")
        except dash.exceptions.PreventUpdate:
            pytest.fail("PreventUpdate raised despite URL matching report-level")

    def test_allows_report_when_store_matches(self):
        """Must not PreventUpdate when store says report, even if URL is empty."""
        import dash

        from pokerhero.frontend.pages.sessions import _load_session_report

        try:
            _load_session_report(
                session_id=5,
                state={"level": "report", "session_id": 5},
                search="",
            )
        except TypeError:
            pytest.fail("_load_session_report does not accept both state and search")
        except dash.exceptions.PreventUpdate:
            pytest.fail("PreventUpdate raised despite store matching report-level")

    def test_raises_prevent_update_when_url_has_hand_id(self):
        """Must raise PreventUpdate when URL has hand_id (actions view)."""
        import dash

        from pokerhero.frontend.pages.sessions import _load_session_report

        try:
            _load_session_report(
                session_id=5,
                state={"level": "sessions"},
                search="?session_id=5&hand_id=10",
            )
            pytest.fail("Should have raised PreventUpdate")
        except TypeError:
            pytest.fail("_load_session_report does not accept both state and search")
        except dash.exceptions.PreventUpdate:
            pass  # Expected


# ---------------------------------------------------------------------------
# TestRenderInitialCallParsesURL
# ---------------------------------------------------------------------------


class TestRenderInitialCallParsesURL:
    """_render must parse URL params on initial page load (cross-page nav).

    Uses a consumed-search store to track which URL params have been applied.
    On fresh page load the store is empty, so any search params are new and
    get parsed.  After consumption, subsequent callback fires from click-based
    navigation see the same consumed value and skip URL parsing.
    """

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_render_parses_url_on_fresh_page_load(self):
        """_render returns actions-level content when search has hand_id.

        On a fresh page load (consumed_search is empty), the URL must be
        parsed regardless of what triggered the callback.
        """
        import unittest.mock as mock

        import dash

        from pokerhero.frontend.pages.sessions import _render

        fake_ctx = mock.MagicMock()
        # Simulate trigger being drill-down-state (store init on page load)
        fake_ctx.triggered = [
            {"prop_id": "drill-down-state.data", "value": {"level": "sessions"}}
        ]

        with (
            mock.patch.object(dash, "callback_context", fake_ctx),
            mock.patch(
                "pokerhero.frontend.pages.sessions._render_actions",
                return_value=(
                    "actions-content",
                    "Hand #1",
                ),
            ) as mock_actions,
            mock.patch(
                "pokerhero.frontend.pages.sessions._get_db_path",
                return_value=":memory:",
            ),
            mock.patch(
                "pokerhero.frontend.pages.sessions._get_session_label",
                return_value="Session 1",
            ),
        ):
            result = _render(
                state={"level": "sessions"},
                pathname="/sessions",
                _ev_result=None,
                search="?session_id=1&hand_id=1",
                consumed_search="",
            )

        mock_actions.assert_called_once()
        content = result[0]
        assert content == "actions-content", (
            f"Expected actions-level content but got: {content!r}. "
            "URL params were not parsed on initial page load."
        )

    def test_render_parses_url_on_fresh_page_load_report_level(self):
        """_render returns report placeholder when search has session_id.

        Simulates initial load for /sessions?session_id=5 (Best Session
        highlight from dashboard).
        """
        import unittest.mock as mock

        import dash

        from pokerhero.frontend.pages.sessions import _render

        fake_ctx = mock.MagicMock()
        fake_ctx.triggered = [
            {"prop_id": "drill-down-state.data", "value": {"level": "sessions"}}
        ]

        with (
            mock.patch.object(dash, "callback_context", fake_ctx),
            mock.patch(
                "pokerhero.frontend.pages.sessions._get_db_path",
                return_value=":memory:",
            ),
            mock.patch(
                "pokerhero.frontend.pages.sessions._get_session_label",
                return_value="Session 5",
            ),
        ):
            result = _render(
                state={"level": "sessions"},
                pathname="/sessions",
                _ev_result=None,
                search="?session_id=5",
                consumed_search="",
            )

        pending = result[3]
        assert pending == 5, (
            f"Expected pending-session-report=5 but got {pending!r}. "
            "URL params were not parsed on initial page load."
        )

    def test_render_skips_consumed_url_on_click_nav(self):
        """_render ignores URL when it matches consumed_search (click nav).

        After URL params are consumed, a subsequent callback fire from a
        click-based nav (e.g. breadcrumb) should use the store, not the
        stale URL.
        """
        import unittest.mock as mock

        import dash

        from pokerhero.frontend.pages.sessions import _render

        fake_ctx = mock.MagicMock()
        fake_ctx.triggered = [
            {"prop_id": "drill-down-state.data", "value": {"level": "sessions"}}
        ]

        with (
            mock.patch.object(dash, "callback_context", fake_ctx),
            mock.patch(
                "pokerhero.frontend.pages.sessions._render_sessions",
                return_value="sessions-list",
            ) as mock_sessions,
            mock.patch(
                "pokerhero.frontend.pages.sessions._get_db_path",
                return_value=":memory:",
            ),
        ):
            result = _render(
                state={"level": "sessions"},
                pathname="/sessions",
                _ev_result=None,
                search="?session_id=1&hand_id=1",
                consumed_search="?session_id=1&hand_id=1",
            )

        mock_sessions.assert_called_once()
        content = result[0]
        assert content == "sessions-list", (
            f"Expected sessions-list but got: {content!r}. "
            "Already-consumed URL params should be ignored."
        )
