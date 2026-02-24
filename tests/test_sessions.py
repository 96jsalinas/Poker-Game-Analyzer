"""Tests for the sessions page components."""

import pytest


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

    def _showdown_df(
        self,
        net_result: float = 5000.0,
        hero_cards: str = "Ah Kh",
        villain_cards: str = "2c 3d",
    ):
        import pandas as pd

        # Complete 5-card board: Ah Kh has royal flush (equity ≈ 1.0)
        return pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#100"],
                "hero_cards": [hero_cards],
                "villain_username": ["villain"],
                "villain_cards": [villain_cards],
                "board": ["Qh Jh Th 9d 2s"],
                "net_result": [net_result],
                "total_pot": [6000.0],
            }
        )

    def test_returns_html_div(self):
        """Result is an html.Div for both empty and non-empty input."""
        import pandas as pd
        from dash import html

        from pokerhero.frontend.pages.sessions import _build_ev_summary

        assert isinstance(_build_ev_summary(pd.DataFrame()), html.Div)

    def test_empty_shows_no_showdown_message(self):
        """Empty DataFrame produces a message indicating no showdown data."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_ev_summary

        text = str(_build_ev_summary(pd.DataFrame())).lower()
        assert "no" in text or "0" in text

    def test_nonempty_mentions_showdown(self):
        """Non-empty DataFrame mentions showdown in the output."""
        from pokerhero.frontend.pages.sessions import _build_ev_summary

        text = str(_build_ev_summary(self._showdown_df())).lower()
        assert "showdown" in text

    def test_unlucky_outcome_shows_below_equity(self):
        """Hero had near-100% equity (royal flush) but lost → below equity verdict."""
        from pokerhero.frontend.pages.sessions import _build_ev_summary

        # Ah Kh vs 2c 3d on Qh Jh Th 9d 2s: hero equity ≈ 1.0, but hero loses
        result = _build_ev_summary(self._showdown_df(net_result=-3000.0))
        assert "below" in str(result).lower()

    def test_ev_summary_shows_unavailable_note_for_bad_cards(self):
        """Row with unparseable card strings shows an equity-unavailable note."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_ev_summary

        df = pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#999"],
                "hero_cards": ["XX XX"],
                "villain_username": ["villain"],
                "villain_cards": ["YY YY"],
                "board": [""],
                "net_result": [100.0],
                "total_pot": [200.0],
            }
        )
        result = str(_build_ev_summary(df))
        assert "unavailable" in result.lower()


# ---------------------------------------------------------------------------
# TestBuildFlaggedHandsList
# ---------------------------------------------------------------------------


class TestBuildFlaggedHandsList:
    """Tests for _build_flagged_hands_list pure UI helper."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def _hand_df(
        self,
        net_result: float = 5000.0,
        hero_cards: str = "Ah Kh",
        villain_cards: str = "2c 3d",
    ):
        import pandas as pd

        return pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#100"],
                "hero_cards": [hero_cards],
                "villain_username": ["villain"],
                "villain_cards": [villain_cards],
                "board": ["Qh Jh Th 9d 2s"],
                "net_result": [net_result],
                "total_pot": [6000.0],
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

        assert _build_flagged_hands_list(self._hand_df(net_result=5000.0)) is not None

    def test_unlucky_hand_flagged(self):
        """Hero had near-100% equity but lost → flagged as Unlucky."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        # Ah Kh vs 2c 3d on Qh Jh Th 9d 2s: equity ≈ 1.0 but hero loses
        result = _build_flagged_hands_list(self._hand_df(net_result=-3000.0))
        assert "Unlucky" in str(result)

    def test_lucky_hand_flagged(self):
        """Hero had near-zero equity but won → flagged as Lucky."""
        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        # 2c 3d vs Ah Kh on Qh Jh Th 9d 2s: equity ≈ 0.0 but hero wins
        result = _build_flagged_hands_list(
            self._hand_df(hero_cards="2c 3d", villain_cards="Ah Kh", net_result=5000.0)
        )
        assert "Lucky" in str(result)

    def test_flagged_hands_shows_unavailable_for_bad_cards(self):
        """Row with unparseable card strings appears as equity-unavailable entry."""
        import pandas as pd

        from pokerhero.frontend.pages.sessions import _build_flagged_hands_list

        df = pd.DataFrame(
            {
                "hand_id": [1],
                "source_hand_id": ["#999"],
                "hero_cards": ["XX XX"],
                "villain_username": ["villain"],
                "villain_cards": ["YY YY"],
                "board": [""],
                "net_result": [100.0],
                "total_pot": [200.0],
            }
        )
        result = str(_build_flagged_hands_list(df))
        assert "unavailable" in result.lower()


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
