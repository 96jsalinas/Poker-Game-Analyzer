"""Home page — navigation hub for PokerHero Analyzer."""

from __future__ import annotations

import dash
from dash import dcc, html

dash.register_page(__name__, path="/", name="Home")  # type: ignore[no-untyped-call]

_BUTTON_STYLE = {
    "display": "block",
    "width": "260px",
    "padding": "18px",
    "margin": "12px auto",
    "fontSize": "16px",
    "cursor": "pointer",
    "borderRadius": "8px",
    "border": "2px solid #0074D9",
    "background": "var(--bg-2, #fff)",
    "color": "#0074D9",
    "textAlign": "center",
    "textDecoration": "none",
}

layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "500px",
        "margin": "60px auto",
        "textAlign": "center",
    },
    children=[
        html.H1("♠ PokerHero Analyzer"),
        html.P(
            "Your personal poker analysis hub.",
            style={"color": "var(--text-3, #555)", "marginBottom": "32px"},
        ),
        dcc.Link("📤  Upload Files", href="/upload", style=_BUTTON_STYLE),
        dcc.Link("🔍  Review Sessions", href="/sessions", style=_BUTTON_STYLE),
        dcc.Link("📊  Overall Stats", href="/dashboard", style=_BUTTON_STYLE),
        dcc.Link("⚙️  Settings", href="/settings", style=_BUTTON_STYLE),
        dcc.Link("📖  User Guide", href="/guide", style=_BUTTON_STYLE),
    ],
)
