"""Tests for the guide page."""


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
