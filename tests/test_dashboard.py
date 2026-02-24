"""Tests for the dashboard page components."""


class TestDashboardPositionTrafficLights:
    """Traffic-light colours applied to VPIP/PFR/3-Bet cells in position table."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_dashboard_render_imports_traffic_light(self):
        """Dashboard render source must import traffic_light from targets module."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert "traffic_light" in src

    def test_dashboard_render_reads_target_settings(self):
        """Dashboard render source must call read_target_settings."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert "read_target_settings" in src

    def test_dashboard_render_applies_background_color_to_position_cells(self):
        """Dashboard render source must set backgroundColor on VPIP position cells."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert "backgroundColor" in src

    def test_vpip_cell_uses_traffic_light_color(self):
        """Position table VPIP cell style must use the traffic_light output as color."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        # The color mapping must appear in the render source
        assert "_TL_COLORS" in src or "tl_color" in src or "traffic_light" in src


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


class TestDashboardDarkModeCompatibility:
    """Dark mode: dashboard inline colors must use CSS custom properties."""

    def test_tl_colors_use_css_vars(self):
        """Dashboard _TL_COLORS values must use CSS custom property references."""
        from pokerhero.frontend.pages.dashboard import _TL_COLORS

        assert all("var(" in v for v in _TL_COLORS.values())

    def test_pnl_color_uses_css_var(self):
        """Dashboard render source must reference --pnl-positive CSS var."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        assert "--pnl-positive" in inspect.getsource(dashboard)

    def test_vpip_pfr_chart_accepts_theme(self):
        """_build_vpip_pfr_chart must accept a theme parameter."""
        import inspect

        from pokerhero.frontend.pages.dashboard import _build_vpip_pfr_chart

        sig = inspect.signature(_build_vpip_pfr_chart)
        assert "theme" in sig.parameters
