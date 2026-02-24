"""Target range settings and traffic-light classification for poker statistics.

Stores per-position green/yellow zone bounds for VPIP, PFR, and 3-Bet.  Values
are REAL percentages (e.g. 18.0 = 18 %).  Bounds are loaded from the
``target_settings`` table; defaults represent a balanced TAG profile.

Traffic-light logic
-------------------
- **green**  : ``green_min <= value <= green_max``
- **yellow** : ``yellow_min <= value <= yellow_max`` (and not green)
- **red**    : outside the yellow zone

Yellow bounds must fully enclose the green bounds to allow asymmetric zones.

Position mapping
----------------
The settings table stores six canonical positions.  The broader
``UTG+1`` and ``MP+1`` positions found in full-ring games are mapped
to ``utg`` and ``mp`` at lookup time.
"""

from __future__ import annotations

from sqlite3 import Connection
from typing import Literal

from typing_extensions import TypedDict

POSITIONS: tuple[str, ...] = ("utg", "mp", "co", "btn", "sb", "bb")

_POSITION_ALIAS: dict[str, str] = {
    "utg+1": "utg",
    "mp+1": "mp",
}


class TargetBounds(TypedDict):
    """Green and yellow zone bounds for a single (stat, position) pair."""

    green_min: float
    green_max: float
    yellow_min: float
    yellow_max: float


# Defaults represent a balanced TAG (Tight-Aggressive) profile.
TARGET_DEFAULTS: dict[tuple[str, str], TargetBounds] = {
    # ── VPIP ──────────────────────────────────────────────────────────────
    ("vpip", "utg"): TargetBounds(
        green_min=12, green_max=18, yellow_min=9, yellow_max=21
    ),
    ("vpip", "mp"): TargetBounds(
        green_min=14, green_max=20, yellow_min=11, yellow_max=23
    ),
    ("vpip", "co"): TargetBounds(
        green_min=18, green_max=26, yellow_min=14, yellow_max=30
    ),
    ("vpip", "btn"): TargetBounds(
        green_min=28, green_max=40, yellow_min=22, yellow_max=48
    ),
    ("vpip", "sb"): TargetBounds(
        green_min=28, green_max=38, yellow_min=22, yellow_max=45
    ),
    ("vpip", "bb"): TargetBounds(
        green_min=30, green_max=42, yellow_min=24, yellow_max=50
    ),
    # ── PFR ───────────────────────────────────────────────────────────────
    ("pfr", "utg"): TargetBounds(
        green_min=10, green_max=15, yellow_min=7, yellow_max=18
    ),
    ("pfr", "mp"): TargetBounds(
        green_min=11, green_max=17, yellow_min=8, yellow_max=20
    ),
    ("pfr", "co"): TargetBounds(
        green_min=13, green_max=20, yellow_min=10, yellow_max=24
    ),
    ("pfr", "btn"): TargetBounds(
        green_min=18, green_max=28, yellow_min=14, yellow_max=34
    ),
    ("pfr", "sb"): TargetBounds(
        green_min=12, green_max=20, yellow_min=9, yellow_max=25
    ),
    ("pfr", "bb"): TargetBounds(green_min=8, green_max=14, yellow_min=5, yellow_max=18),
    # ── 3-Bet ─────────────────────────────────────────────────────────────
    ("3bet", "utg"): TargetBounds(green_min=3, green_max=6, yellow_min=1, yellow_max=9),
    ("3bet", "mp"): TargetBounds(green_min=3, green_max=7, yellow_min=1, yellow_max=10),
    ("3bet", "co"): TargetBounds(green_min=5, green_max=9, yellow_min=3, yellow_max=12),
    ("3bet", "btn"): TargetBounds(
        green_min=7, green_max=12, yellow_min=4, yellow_max=15
    ),
    ("3bet", "sb"): TargetBounds(
        green_min=8, green_max=14, yellow_min=5, yellow_max=18
    ),
    ("3bet", "bb"): TargetBounds(
        green_min=10, green_max=16, yellow_min=6, yellow_max=20
    ),
}


def traffic_light(
    value: float,
    green_min: float,
    green_max: float,
    yellow_min: float,
    yellow_max: float,
) -> Literal["green", "yellow", "red"]:
    """Classify *value* against green and yellow zone bounds.

    Args:
        value: The observed statistic (percentage, e.g. 18.5).
        green_min: Lower bound of the green (optimal) zone, inclusive.
        green_max: Upper bound of the green (optimal) zone, inclusive.
        yellow_min: Lower bound of the yellow (marginal) zone, inclusive.
            Must be ≤ green_min.
        yellow_max: Upper bound of the yellow (marginal) zone, inclusive.
            Must be ≥ green_max.

    Returns:
        ``'green'`` when within the green range, ``'yellow'`` when outside
        green but within yellow, ``'red'`` when outside yellow.
    """
    if green_min <= value <= green_max:
        return "green"
    if yellow_min <= value <= yellow_max:
        return "yellow"
    return "red"


def canonical_position(position: str) -> str:
    """Map full-ring alias positions to the six canonical positions.

    ``'UTG+1'`` → ``'utg'``, ``'MP+1'`` → ``'mp'``, others lowercased.
    """
    return _POSITION_ALIAS.get(position.lower(), position.lower())


def ensure_target_settings_table(conn: Connection) -> None:
    """Create the ``target_settings`` table if it does not exist.

    Safe to call on every connection — uses ``CREATE TABLE IF NOT EXISTS``.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS target_settings (
            stat       TEXT NOT NULL,
            position   TEXT NOT NULL,
            green_min  REAL NOT NULL,
            green_max  REAL NOT NULL,
            yellow_min REAL NOT NULL,
            yellow_max REAL NOT NULL,
            PRIMARY KEY (stat, position)
        )
        """
    )
    conn.commit()


def read_target_settings(conn: Connection) -> dict[tuple[str, str], TargetBounds]:
    """Load all target bounds from ``target_settings``, falling back to defaults.

    Rows present in the DB override the corresponding ``TARGET_DEFAULTS``
    entry.  Rows absent from the DB use the default value.  The table is
    created automatically if it does not exist yet.

    Args:
        conn: Open SQLite connection (may be an in-memory database).

    Returns:
        Mapping of ``(stat, position)`` → :class:`TargetBounds`.
    """
    ensure_target_settings_table(conn)

    result: dict[tuple[str, str], TargetBounds] = dict(TARGET_DEFAULTS)

    rows = conn.execute(
        "SELECT stat, position, green_min, green_max, yellow_min, yellow_max "
        "FROM target_settings"
    ).fetchall()

    for stat, pos, gmin, gmax, ymin, ymax in rows:
        result[(stat, pos)] = TargetBounds(
            green_min=gmin,
            green_max=gmax,
            yellow_min=ymin,
            yellow_max=ymax,
        )

    return result
