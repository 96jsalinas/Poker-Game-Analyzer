"""Tests for the settings page layout."""


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

    def test_layout_has_sample_count_input(self):
        """Settings layout must contain a settings-sample-count input."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "settings-sample-count" in str(comp)

    def test_layout_has_lucky_threshold_input(self):
        """Settings layout must contain a settings-lucky-threshold input."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "settings-lucky-threshold" in str(comp)

    def test_layout_has_unlucky_threshold_input(self):
        """Settings layout must contain a settings-unlucky-threshold input."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "settings-unlucky-threshold" in str(comp)

    def test_layout_has_min_hands_input(self):
        """Settings layout must contain a settings-min-hands input."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "settings-min-hands" in str(comp)


class TestSettingsTargetsPage:
    """Tests for the /settings/targets sub-page."""

    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

    def test_page_registered_at_settings_targets(self):
        """Settings targets page must be registered at /settings/targets."""
        import dash

        paths = [p["path"] for p in dash.page_registry.values()]
        assert "/settings/targets" in paths

    def test_settings_page_links_to_targets(self):
        """Main settings layout must contain a link to /settings/targets."""
        from pokerhero.frontend.pages.settings import layout

        comp = layout() if callable(layout) else layout
        assert "/settings/targets" in str(comp)

    def test_layout_has_vpip_inputs_for_all_positions(self):
        """Settings targets layout has green_min inputs for all 6 VPIP positions."""
        from pokerhero.frontend.pages.settings_targets import layout

        comp = layout() if callable(layout) else layout
        comp_str = str(comp)
        for pos in ("utg", "mp", "co", "btn", "sb", "bb"):
            assert f"target-vpip-{pos}-green-min" in comp_str, (
                f"Missing vpip {pos} green_min input"
            )
            assert f"target-vpip-{pos}-green-max" in comp_str, (
                f"Missing vpip {pos} green_max input"
            )
            assert f"target-vpip-{pos}-yellow-min" in comp_str, (
                f"Missing vpip {pos} yellow_min input"
            )
            assert f"target-vpip-{pos}-yellow-max" in comp_str, (
                f"Missing vpip {pos} yellow_max input"
            )

    def test_layout_has_pfr_inputs_for_all_positions(self):
        """Settings targets layout must have bound inputs for all 6 PFR positions."""
        from pokerhero.frontend.pages.settings_targets import layout

        comp = layout() if callable(layout) else layout
        comp_str = str(comp)
        for pos in ("utg", "mp", "co", "btn", "sb", "bb"):
            assert f"target-pfr-{pos}-green-min" in comp_str, (
                f"Missing pfr {pos} green_min input"
            )

    def test_layout_has_3bet_inputs_for_all_positions(self):
        """Settings targets layout must have bound inputs for all 6 3-Bet positions."""
        from pokerhero.frontend.pages.settings_targets import layout

        comp = layout() if callable(layout) else layout
        comp_str = str(comp)
        for pos in ("utg", "mp", "co", "btn", "sb", "bb"):
            assert f"target-3bet-{pos}-green-min" in comp_str, (
                f"Missing 3bet {pos} green_min input"
            )

    def test_load_callback_returns_defaults_for_memory_db(self):
        """Load callback returns TARGET_DEFAULTS values for an in-memory DB."""
        from pokerhero.analysis.targets import TARGET_DEFAULTS
        from pokerhero.frontend.pages.settings_targets import _load_targets

        result = _load_targets("/settings/targets")
        defaults = TARGET_DEFAULTS[("vpip", "btn")]
        # Result is a flat list of values in (stat, position, bound) order.
        # Just verify it is a list with at least one numeric value matching a default.
        assert isinstance(result, list)
        assert any(v == defaults["green_min"] for v in result)
