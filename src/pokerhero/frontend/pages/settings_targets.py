"""Target stats settings sub-page — per-position green/yellow zone configuration.

Provides a dedicated settings page at ``/settings/targets`` with inputs for the
green and yellow range bounds for VPIP, PFR, and 3-Bet at each of the six
canonical positions.  Values are persisted to the ``target_settings`` table.
"""

from __future__ import annotations

import sqlite3

import dash
from dash import Input, Output, callback, dcc, html

from pokerhero.analysis.targets import (
    POSITIONS,
    TARGET_DEFAULTS,
    ensure_target_settings_table,
    read_target_settings,
)
from pokerhero.database.db import get_connection, init_db

dash.register_page(__name__, path="/settings/targets", name="Target Stats")  # type: ignore[no-untyped-call]

_SECTION_STYLE = {
    "marginBottom": "32px",
    "padding": "20px",
    "border": "1px solid var(--border, #e0e0e0)",
    "borderRadius": "8px",
    "background": "var(--bg-2, #fafafa)",
}

_STAT_LABELS: dict[str, str] = {
    "vpip": "VPIP — Voluntarily Put In Pot",
    "pfr": "PFR — Pre-Flop Raise",
    "3bet": "3-Bet",
}

_POS_LABELS: dict[str, str] = {
    "utg": "UTG",
    "mp": "MP",
    "co": "CO",
    "btn": "BTN",
    "sb": "SB",
    "bb": "BB",
}

_BOUND_LABELS: dict[str, str] = {
    "green-min": "Green Min",
    "green-max": "Green Max",
    "yellow-min": "Yellow Min",
    "yellow-max": "Yellow Max",
}

_BOUND_KEYS: tuple[str, ...] = ("green-min", "green-max", "yellow-min", "yellow-max")


def _field_id(stat: str, pos: str, bound: str) -> str:
    """Return the plain component ID string for a target bounds input."""
    return f"target-{stat}-{pos}-{bound}"


def _bounds_row(stat: str, pos: str) -> html.Tr:
    """Build one table row with four inputs for a (stat, position) pair."""
    defaults = TARGET_DEFAULTS[(stat, pos)]
    bound_map = {
        "green-min": defaults["green_min"],
        "green-max": defaults["green_max"],
        "yellow-min": defaults["yellow_min"],
        "yellow-max": defaults["yellow_max"],
    }
    cells: list[html.Td | html.Th] = [
        html.Td(
            _POS_LABELS[pos],
            style={"fontWeight": "600", "paddingRight": "16px", "width": "60px"},
        )
    ]
    for bound in _BOUND_KEYS:
        cells.append(
            html.Td(
                html.Div(
                    [
                        dcc.Input(
                            id=_field_id(stat, pos, bound),
                            type="number",
                            min=0,
                            max=100,
                            step=1,
                            value=bound_map[bound],
                            style={
                                "width": "70px",
                                "padding": "4px 6px",
                                "fontSize": "13px",
                            },
                        ),
                        html.Span(
                            id=f"target-{stat}-{pos}-{bound}-saved",
                            style={
                                "marginLeft": "4px",
                                "fontSize": "11px",
                                "color": "var(--text-4, #888)",
                            },
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                style={"paddingRight": "8px"},
            )
        )
    return html.Tr(cells)


def _stat_section(stat: str) -> html.Div:
    """Build the full section for one stat (vpip / pfr / 3bet)."""
    header_cells = [html.Th("Position", style={"paddingRight": "16px"})]
    for bound in _BOUND_KEYS:
        header_cells.append(
            html.Th(
                _BOUND_LABELS[bound],
                style={
                    "paddingRight": "8px",
                    "fontSize": "12px",
                    "color": "var(--text-3, #555)",
                    "fontWeight": "600",
                },
            )
        )
    rows = [html.Tr(header_cells)] + [_bounds_row(stat, pos) for pos in POSITIONS]
    return html.Div(
        style=_SECTION_STYLE,
        children=[
            html.H3(_STAT_LABELS[stat], style={"marginTop": 0}),
            html.P(
                "Green zone = optimal range. Yellow zone = marginal (must fully "
                "enclose green). Red = outside yellow.",
                style={"color": "var(--text-3, #666)", "fontSize": "13px"},
            ),
            html.Table(
                rows,
                style={"borderCollapse": "collapse"},
            ),
        ],
    )


layout = html.Div(
    style={
        "fontFamily": "sans-serif",
        "maxWidth": "760px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H2("🎯 Target Stats"),
        dcc.Link(
            "← Back to Settings",
            href="/settings",
            style={"fontSize": "13px", "color": "#0074D9"},
        ),
        html.Hr(),
        html.P(
            "Configure per-position traffic-light targets for VPIP, PFR, and 3-Bet. "
            "Defaults represent a balanced TAG profile — novice users can leave these "
            "unchanged.",
            style={
                "color": "var(--text-3, #555)",
                "fontSize": "14px",
                "marginBottom": "24px",
            },
        ),
        *[_stat_section(stat) for stat in ("vpip", "pfr", "3bet")],
    ],
)


def _get_db_path() -> str:
    result: str = dash.get_app().server.config.get("DB_PATH", ":memory:")  # type: ignore[no-untyped-call]
    return result


def _open_conn(db_path: str) -> sqlite3.Connection:
    if db_path == ":memory:":
        return init_db(":memory:")
    return get_connection(db_path)


# ---------------------------------------------------------------------------
# Load callback — pre-populate all inputs on page visit
# ---------------------------------------------------------------------------

_ALL_OUTPUT_IDS: list[str] = [
    _field_id(stat, pos, bound)
    for stat in ("vpip", "pfr", "3bet")
    for pos in POSITIONS
    for bound in _BOUND_KEYS
]


@callback(
    [Output(fid, "value") for fid in _ALL_OUTPUT_IDS],
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def _load_targets(pathname: str) -> list[float]:
    """Load all target bounds from DB (or defaults) on page visit."""
    if pathname != "/settings/targets":
        raise dash.exceptions.PreventUpdate
    db_path = _get_db_path()
    conn = _open_conn(db_path)
    try:
        targets = read_target_settings(conn)
    finally:
        conn.close()

    result: list[float] = []
    for stat in ("vpip", "pfr", "3bet"):
        for pos in POSITIONS:
            bounds = targets[(stat, pos)]
            result.append(bounds["green_min"])
            result.append(bounds["green_max"])
            result.append(bounds["yellow_min"])
            result.append(bounds["yellow_max"])
    return result


# ---------------------------------------------------------------------------
# Save callbacks — one per (stat, position), triggered on any bound change
# ---------------------------------------------------------------------------


def _make_save_callback(stat: str, pos: str) -> None:
    """Register a save callback for one (stat, position) pair."""
    inputs = [Input(_field_id(stat, pos, b), "value") for b in _BOUND_KEYS]
    output = Output(f"target-{stat}-{pos}-green-min-saved", "children")

    @callback(output, *inputs, prevent_initial_call=True)
    def _save(
        gmin: float | None,
        gmax: float | None,
        ymin: float | None,
        ymax: float | None,
        _stat: str = stat,
        _pos: str = pos,
    ) -> str:
        if gmin is None or gmax is None or ymin is None or ymax is None:
            return ""
        gmin_f, gmax_f, ymin_f, ymax_f = (
            float(gmin),
            float(gmax),
            float(ymin),
            float(ymax),
        )
        db_path = _get_db_path()
        if db_path == ":memory:":
            return ""
        conn = get_connection(db_path)
        try:
            ensure_target_settings_table(conn)
            conn.execute(
                "INSERT OR REPLACE INTO target_settings "
                "(stat, position, green_min, green_max, yellow_min, yellow_max) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (_stat, _pos, gmin_f, gmax_f, ymin_f, ymax_f),
            )
            conn.commit()
        finally:
            conn.close()
        return "✓"


for _stat in ("vpip", "pfr", "3bet"):
    for _pos in POSITIONS:
        _make_save_callback(_stat, _pos)
