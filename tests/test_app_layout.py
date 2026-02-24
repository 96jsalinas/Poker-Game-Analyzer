"""Tests for the frontend page layout and app registration."""


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
    def setup_method(self):
        from pokerhero.frontend.app import create_app

        create_app(db_path=":memory:")

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

    def test_layout_has_currency_toggle(self):
        """Sessions page must define a session-filter-currency RadioItems."""
        import inspect

        from pokerhero.frontend.pages import sessions

        src = inspect.getsource(sessions)
        assert "session-filter-currency" in src


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

    def test_layout_has_currency_toggle(self):
        """Dashboard layout must contain a dashboard-currency RadioItems."""
        from pokerhero.frontend.pages.dashboard import layout

        comp = layout() if callable(layout) else layout
        assert "dashboard-currency" in str(comp)

    def test_currency_toggle_default_is_all(self):
        """Dashboard currency toggle must default to 'all'."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert '"dashboard-currency"' in src
        assert '"all"' in src

    def test_callback_has_currency_input(self):
        """Dashboard callback must have dashboard-currency as an Input."""
        import inspect

        from pokerhero.frontend.pages import dashboard

        src = inspect.getsource(dashboard)
        assert 'Input("dashboard-currency"' in src


class TestThemeToggle:
    def test_layout_has_theme_store(self):
        """App layout must contain a dcc.Store with id 'theme-store'."""
        from pokerhero.frontend.app import create_app

        app = create_app(db_path=":memory:")
        assert "theme-store" in str(app.layout)

    def test_layout_has_toggle_button(self):
        """App layout must contain a theme toggle button with id 'theme-toggle-btn'."""
        from pokerhero.frontend.app import create_app

        app = create_app(db_path=":memory:")
        assert "theme-toggle-btn" in str(app.layout)

    def test_theme_store_default_is_light(self):
        """Theme store must default to 'light'."""
        from pokerhero.frontend.app import create_app

        app = create_app(db_path=":memory:")
        assert "light" in str(app.layout)

    def test_toggle_button_uses_face_emoji(self):
        """Toggle button must use the sun-with-face or new-moon-with-face emoji."""
        from pokerhero.frontend.app import create_app

        app = create_app(db_path=":memory:")
        layout_str = str(app.layout)
        assert "\U0001f31e" in layout_str or "\U0001f31a" in layout_str

    def test_theme_css_exists(self):
        """assets/theme.css must exist next to the app module."""
        from pathlib import Path

        import pokerhero.frontend.app as app_module

        assets = Path(app_module.__file__).parent / "assets" / "theme.css"
        assert assets.exists()

    def test_theme_css_has_pnl_positive_var(self):
        """theme.css must define --pnl-positive custom property in dark mode."""
        from pathlib import Path

        import pokerhero.frontend.app as app_module

        css_text = (
            Path(app_module.__file__).parent / "assets" / "theme.css"
        ).read_text()
        assert "--pnl-positive" in css_text

    def test_theme_css_has_bg_hero_row_var(self):
        """theme.css must define --bg-hero-row custom property in dark mode."""
        from pathlib import Path

        import pokerhero.frontend.app as app_module

        css_text = (
            Path(app_module.__file__).parent / "assets" / "theme.css"
        ).read_text()
        assert "--bg-hero-row" in css_text
