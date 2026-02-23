"""Guide page — in-app user guide and statistic definitions."""

from __future__ import annotations

import dash
from dash import html

dash.register_page(__name__, path="/guide", name="Guide")  # type: ignore[no-untyped-call]

_HEADING_STYLE = {"color": "#0074D9", "marginTop": "32px", "marginBottom": "8px"}
_SUBHEADING_STYLE = {"color": "#333", "marginTop": "24px", "marginBottom": "4px"}
_FORMULA_STYLE = {
    "background": "#f5f7fa",
    "border": "1px solid #dde",
    "borderRadius": "4px",
    "padding": "8px 14px",
    "fontFamily": "monospace",
    "fontSize": "13px",
    "margin": "8px 0 12px",
}
_TABLE_STYLE = {
    "width": "100%",
    "borderCollapse": "collapse",
    "marginBottom": "16px",
    "fontSize": "13px",
}
_TH = {
    "background": "#0074D9",
    "color": "#fff",
    "padding": "6px 10px",
    "textAlign": "left",
}
_TD_EVEN = {"padding": "6px 10px", "borderBottom": "1px solid #eee"}
_TD_ODD = {**_TD_EVEN, "background": "#f9f9f9"}

_CONTAINER = {
    "fontFamily": "sans-serif",
    "maxWidth": "860px",
    "margin": "0 auto",
    "padding": "24px 20px 60px",
    "color": "#222",
    "lineHeight": "1.6",
}


def _section_heading(text: str) -> html.H2:
    return html.H2(text, style=_HEADING_STYLE)


def _stat_heading(text: str) -> html.H3:
    return html.H3(text, style=_SUBHEADING_STYLE)


def _formula(text: str) -> html.Pre:
    return html.Pre(text, style=_FORMULA_STYLE)


def _kv_table(rows: list[tuple[str, str]]) -> html.Table:
    """Render a two-column key/value table."""
    header = html.Tr([html.Th("Term", style=_TH), html.Th("Definition", style=_TH)])
    body_rows = [
        html.Tr(
            [
                html.Td(k, style=_TD_ODD if i % 2 == 0 else _TD_EVEN),
                html.Td(v, style=_TD_ODD if i % 2 == 0 else _TD_EVEN),
            ]
        )
        for i, (k, v) in enumerate(rows)
    ]
    return html.Table([html.Thead(header), html.Tbody(body_rows)], style=_TABLE_STYLE)


layout = html.Div(
    style=_CONTAINER,
    children=[
        # ── Header ────────────────────────────────────────────────────────
        html.H1("📖 User Guide", style={"marginBottom": "4px"}),
        html.P(
            "Everything you need to know to use PokerHero-Analyzer and understand your stats.",  # noqa: E501
            style={"color": "#555", "marginBottom": "4px"},
        ),
        html.P(
            html.A("← Back to Home", href="/"),
            style={"color": "#0074D9", "marginBottom": "16px"},
        ),
        html.Hr(),
        # ── Getting Started ───────────────────────────────────────────────
        _section_heading("🚀 Getting Started"),
        html.Ol(
            [
                html.Li(
                    [
                        html.Strong("Set your hero username"),
                        " — go to ",
                        html.A("Settings", href="/settings"),
                        " and enter the PokerStars screen name you play under."
                        " This tells the app which player in each hand history is you.",
                    ]
                ),
                html.Li(
                    [
                        html.Strong("Upload your hand histories"),
                        " — go to ",
                        html.A("Upload Files", href="/upload"),
                        " and drag-and-drop your PokerStars ",
                        html.Code(".txt"),
                        " export files. The app skips duplicates automatically.",
                    ]
                ),
                html.Li(
                    [
                        html.Strong("Explore your stats"),
                        " — head to ",
                        html.A("Overall Stats", href="/dashboard"),
                        " for a high-level overview, or ",
                        html.A("Review Sessions", href="/sessions"),
                        " to drill into individual games.",
                    ]
                ),
            ],
            style={"paddingLeft": "20px"},
        ),
        # ── Dashboard ─────────────────────────────────────────────────────
        _section_heading("📊 The Dashboard"),
        html.P(
            "The dashboard aggregates your performance across all imported hands."
            " Use the time-period radio buttons (7 days / 1 month / 1 year / All time)"
            " at the top to scope every metric to a specific window."
        ),
        _kv_table(
            [
                (
                    "Total Profit/Loss",
                    "Your net result in chips/currency across the selected period.",
                ),
                (
                    "Win Rate (bb/100)",
                    "Big blinds won per 100 hands — the standard measure of profitability.",  # noqa: E501
                ),
                ("Sessions", "Number of distinct sessions imported in the period."),
                ("Hands", "Total hands dealt to you in the period."),
                ("VPIP%", "How often you voluntarily put chips in pre-flop."),
                ("PFR%", "How often you raised pre-flop."),
            ]
        ),
        html.P(
            [
                html.Strong("VPIP/PFR Gap chart: "),
                "A stacked horizontal bar showing PFR% (green), Call/Limp% (blue — the gap),"  # noqa: E501
                " and Fold% (grey). A small gap between VPIP and PFR indicates a tight-aggressive (TAG) style.",  # noqa: E501
            ]
        ),
        html.P(
            [
                html.Strong("Positional stats table: "),
                "Breaks your play down by seat (BTN, CO, SB, BB, etc.). Hover the ",
                html.Code("?"),
                " badge on each column header to see the exact formula.",
            ]
        ),
        html.P(
            [
                html.Strong("Highlights: "),
                "Four cards showing your biggest hand win/loss and best/worst session."
                " Click any card to jump straight to that hand or session.",
            ]
        ),
        # ── Review Sessions ───────────────────────────────────────────────
        _section_heading("🔍 Review Sessions"),
        html.P(
            "Four drill-down levels:"
            " Session List → Session Report → Hand List → Hand Detail."
            " Use the breadcrumb trail to navigate back up."
        ),
        html.H4("Level 1 — Session List", style={"marginTop": "16px"}),
        html.P(
            "All your sessions in a table (date, stakes, hands played, net result)."
            " Filter by date range, stakes, P&L range, or minimum hand count."
            " Click a row to open the Session Report for that session."
        ),
        html.H4("Level 2 — Session Report", style={"marginTop": "16px"}),
        html.P("A narrative overview of your performance in the selected session."),
        html.Ul(
            [
                html.Li(
                    [
                        html.Strong("KPI strip — "),
                        "five at-a-glance cards: Hands played, VPIP%, PFR%,"
                        " Aggression Factor (AF), and Win Rate in bb/100.",
                    ]
                ),
                html.Li(
                    [
                        html.Strong("Narrative paragraph — "),
                        "a short written summary describing your stats.",
                    ]
                ),
                html.Li(
                    [
                        html.Strong("EV Summary — "),
                        "if villain cards were known at showdown or all-in, this shows"
                        " whether you ran above equity (👍), below equity (👎), or near"
                        " equity (~). Lucky = won with < 40% equity."
                        " Unlucky = lost with > 60% equity.",
                    ]
                ),
                html.Li(
                    [
                        html.Strong("Notable Hands — "),
                        "lists each hand flagged as 🍀 Lucky or 😞 Unlucky with the"
                        " equity percentage at the time.",
                    ]
                ),
            ]
        ),
        html.P("Click Browse all N hands to proceed to the full hand list."),
        html.H4("Level 3 — Hand List", style={"marginTop": "16px"}),
        html.P(
            "Every hand in a session (Hand ID, hole cards, final pot, net result)."
            " Filter by P&L range, position, saw-flop, or showdown."
            " Click a row to see the full action replay."
        ),
        html.H4("Level 4 — Hand Detail", style={"marginTop": "16px"}),
        html.P(
            "A chronological replay grouped by street."
            " Hero decision points show Pot Odds%, MDF%, SPR, and EV (on all-in / showdown spots)."  # noqa: E501
        ),
        html.P(
            [
                html.Strong("Villain summary line: "),
                "Directly below the board, a 'Villains:' line lists every opponent"
                " in the hand with their archetype badge — so you know who you're up"
                " against before reading the action sequence.",
            ]
        ),
        html.P(
            [
                html.Strong("First-action badge: "),
                "The very first time a villain acts in the hand, their archetype"
                " badge appears inline in the action row. Later rows from the same"
                " player are clean — no repetition.",
            ]
        ),
        # ── Opponent Profiles ─────────────────────────────────────────────
        _section_heading("👥 Opponent Profiles"),
        html.P(
            "The app automatically profiles opponents using their pre-flop statistics"
            " accumulated during the session. A player must appear in at least"
            " 15 hands before a classification is shown — below that the sample is"
            " too small to be reliable."
        ),
        html.P(
            [
                "Profiles appear in three places: the ",
                html.Strong("👥 Opponent Profiles"),
                " button on the Hand List expands a panel of profile cards; the ",
                html.Strong("Villain summary line"),
                " in Hand Detail shows all opponents before the action log; and the ",
                html.Strong("Showdown section"),
                " carries the badge next to each villain's hole cards.",
            ]
        ),
        html.H4("The Four Archetypes", style={"marginTop": "16px"}),
        html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Badge", style=_TH),
                            html.Th("VPIP", style=_TH),
                            html.Th("Aggression", style=_TH),
                            html.Th("What it means", style=_TH),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(
                                    html.Span(
                                        "TAG",
                                        style={
                                            "background": "#2980b9",
                                            "color": "#fff",
                                            "borderRadius": "4px",
                                            "padding": "2px 8px",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    style=_TD_ODD,
                                ),
                                html.Td("< 25%", style=_TD_ODD),
                                html.Td("High (PFR/VPIP ≥ 0.5)", style=_TD_ODD),
                                html.Td(
                                    "Tight-Aggressive — plays a narrow, strong range"
                                    " and usually raises rather than calls."
                                    " The most common winning player profile.",
                                    style=_TD_ODD,
                                ),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td(
                                    html.Span(
                                        "LAG",
                                        style={
                                            "background": "#e67e22",
                                            "color": "#fff",
                                            "borderRadius": "4px",
                                            "padding": "2px 8px",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    style=_TD_EVEN,
                                ),
                                html.Td("≥ 25%", style=_TD_EVEN),
                                html.Td("High (PFR/VPIP ≥ 0.5)", style=_TD_EVEN),
                                html.Td(
                                    "Loose-Aggressive — plays many hands and attacks"
                                    " frequently. Can be very strong or very"
                                    " exploitable depending on post-flop skill.",
                                    style=_TD_EVEN,
                                ),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td(
                                    html.Span(
                                        "Nit",
                                        style={
                                            "background": "#7f8c8d",
                                            "color": "#fff",
                                            "borderRadius": "4px",
                                            "padding": "2px 8px",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    style=_TD_ODD,
                                ),
                                html.Td("< 25%", style=_TD_ODD),
                                html.Td("Low (PFR/VPIP < 0.5)", style=_TD_ODD),
                                html.Td(
                                    "Tight-Passive — enters very few pots and mostly"
                                    " calls when they do. Their range is strong but"
                                    " their play is predictable.",
                                    style=_TD_ODD,
                                ),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td(
                                    html.Span(
                                        "Fish",
                                        style={
                                            "background": "#27ae60",
                                            "color": "#fff",
                                            "borderRadius": "4px",
                                            "padding": "2px 8px",
                                            "fontWeight": "700",
                                        },
                                    ),
                                    style=_TD_EVEN,
                                ),
                                html.Td("≥ 25%", style=_TD_EVEN),
                                html.Td("Low (PFR/VPIP < 0.5)", style=_TD_EVEN),
                                html.Td(
                                    "Loose-Passive — calls too wide and rarely raises."
                                    " The most profitable opponent at your table.",
                                    style=_TD_EVEN,
                                ),
                            ]
                        ),
                    ]
                ),
            ],
            style=_TABLE_STYLE,
        ),
        html.H4("How to Adjust Against Each Type", style={"marginTop": "16px"}),
        html.Dl(
            [
                html.Dt(
                    [
                        html.Span(
                            "TAG",
                            style={
                                "background": "#2980b9",
                                "color": "#fff",
                                "borderRadius": "4px",
                                "padding": "1px 6px",
                                "fontWeight": "700",
                                "marginRight": "6px",
                            },
                        ),
                        "Tight-Aggressive",
                    ],
                    style={"fontWeight": "600", "marginTop": "12px"},
                ),
                html.Dd(
                    html.Ul(
                        [
                            html.Li(
                                "Respect their aggression — a TAG raising usually"
                                " has it. Avoid bluffing into their strong ranges."
                            ),
                            html.Li(
                                "3-bet or fold against their opens; cold-calling in"
                                " position works with hands that play well post-flop."
                            ),
                            html.Li(
                                "Semi-bluffs and well-timed bluffs on scare cards have"
                                " merit — they can fold when the board hits your range."
                            ),
                            html.Li(
                                "Thin value-bet less; they will fold dominated hands"
                                " rather than pay off."
                            ),
                        ],
                        style={"paddingLeft": "18px", "marginTop": "4px"},
                    )
                ),
                html.Dt(
                    [
                        html.Span(
                            "LAG",
                            style={
                                "background": "#e67e22",
                                "color": "#fff",
                                "borderRadius": "4px",
                                "padding": "1px 6px",
                                "fontWeight": "700",
                                "marginRight": "6px",
                            },
                        ),
                        "Loose-Aggressive",
                    ],
                    style={"fontWeight": "600", "marginTop": "12px"},
                ),
                html.Dd(
                    html.Ul(
                        [
                            html.Li(
                                "Call down lighter — their wide range contains many"
                                " bluffs and semi-bluffs."
                            ),
                            html.Li(
                                "Position is critical; try to play pots in position"
                                " against a LAG wherever possible."
                            ),
                            html.Li(
                                "Don't try to out-bluff them — they are less likely to"
                                " fold once they commit."
                            ),
                            html.Li(
                                "Let them barrel into your strong hands rather than"
                                " raising, which may stop the action."
                            ),
                        ],
                        style={"paddingLeft": "18px", "marginTop": "4px"},
                    )
                ),
                html.Dt(
                    [
                        html.Span(
                            "Nit",
                            style={
                                "background": "#7f8c8d",
                                "color": "#fff",
                                "borderRadius": "4px",
                                "padding": "1px 6px",
                                "fontWeight": "700",
                                "marginRight": "6px",
                            },
                        ),
                        "Tight-Passive",
                    ],
                    style={"fontWeight": "600", "marginTop": "12px"},
                ),
                html.Dd(
                    html.Ul(
                        [
                            html.Li(
                                "Steal their blinds aggressively — they fold too often"
                                " pre-flop."
                            ),
                            html.Li(
                                "When a Nit shows aggression, give them credit; their"
                                " range is extremely value-heavy."
                            ),
                            html.Li(
                                "Don't pay off big bets — they almost always have a"
                                " strong hand when they raise."
                            ),
                            html.Li(
                                "Bluffing is profitable in unopened pots but fold"
                                " quickly when they fight back."
                            ),
                        ],
                        style={"paddingLeft": "18px", "marginTop": "4px"},
                    )
                ),
                html.Dt(
                    [
                        html.Span(
                            "Fish",
                            style={
                                "background": "#27ae60",
                                "color": "#fff",
                                "borderRadius": "4px",
                                "padding": "1px 6px",
                                "fontWeight": "700",
                                "marginRight": "6px",
                            },
                        ),
                        "Loose-Passive",
                    ],
                    style={"fontWeight": "600", "marginTop": "12px"},
                ),
                html.Dd(
                    html.Ul(
                        [
                            html.Li(
                                "Value bet relentlessly and bet larger than you might"
                                " against thinking players — Fish call too wide."
                            ),
                            html.Li(
                                "Never slow-play your strong hands; extract maximum"
                                " value every street."
                            ),
                            html.Li(
                                "Avoid bluffing — Fish call down with weak pairs and"
                                " draws and cannot be pushed off hands."
                            ),
                            html.Li(
                                "When a Fish raises (which is rare), give them credit;"
                                " they tend to only raise with strong holdings."
                            ),
                        ],
                        style={"paddingLeft": "18px", "marginTop": "4px"},
                    )
                ),
            ],
            style={"margin": "0"},
        ),
        # ── Stat Definitions ─────────────────────────────────────────────
        _section_heading("📐 Statistic Definitions"),
        _stat_heading("VPIP — Voluntarily Put In Pot"),
        _formula("VPIP = Hands where you called or raised pre-flop  ÷  Total Hands"),
        html.P(
            "How often you enter the pot voluntarily. 20–28% is typical for a TAG cash-game player."  # noqa: E501
            " Posting blinds does not count as voluntary."
        ),
        _stat_heading("PFR — Pre-Flop Raise"),
        _formula("PFR = Hands where you raised pre-flop  ÷  Total Hands"),
        html.P(
            "How aggressively you open or re-raise pre-flop. Always ≤ VPIP."
            " The VPIP−PFR gap is how often you limp or cold-call — a wide gap suggests passive tendencies."  # noqa: E501
        ),
        _stat_heading("3-Bet%"),
        _formula(
            "3-Bet% = Times you re-raised a pre-flop raiser  ÷  Opportunities to 3-bet"
        ),
        html.P(
            "An opportunity occurs whenever someone opens with a raise before your action."  # noqa: E501
            " 5–12% is a typical range for a solid TAG player."
        ),
        _stat_heading("C-Bet% — Continuation Bet"),
        _formula(
            "C-Bet% = Times you bet the flop as the pre-flop aggressor\n"
            "          ÷  Times you were pre-flop aggressor and saw the flop"
        ),
        html.P(
            "How often you follow through with a flop bet after raising pre-flop."
            " Very high C-Bet% (>85%) can be exploitable; very low (<40%) may signal post-flop passivity."  # noqa: E501
        ),
        _stat_heading("AF — Aggression Factor"),
        _formula("AF = (Post-flop Bets + Post-flop Raises)  ÷  Post-flop Calls"),
        html.P(
            "Measures post-flop aggression vs passivity. AF > 2.0 is aggressive; below 1.0 is passive."  # noqa: E501
            " Folds and checks are excluded."
        ),
        _stat_heading("Win Rate (bb/100)"),
        _formula("Win Rate = (Total net chips won  ÷  Total hands)  × 100"),
        html.P(
            "The gold-standard profitability metric. Positive = winning player."
            " 5+ bb/100 is considered strong for live cash games."
        ),
        _stat_heading("SPR — Stack-to-Pot Ratio"),
        _formula("SPR = Effective stack at flop  ÷  Pot at start of flop"),
        html.P(
            "Calculated once at the start of the flop. Guides commitment decisions:"
        ),
        _kv_table(
            [
                ("SPR < 4", "Very low — easy to commit with top pair or better."),
                ("SPR 4–13", "Medium — implied odds and draws matter."),
                ("SPR > 13", "Deep — premium hands required to stack off."),
            ]
        ),
        _stat_heading("Pot Odds"),
        _formula("Pot Odds = Amount to Call  ÷  (Total Pot after Call)"),
        html.P(
            "The minimum equity (% chance of winning) you need for a break-even call."
            " If pot odds are 25% and your equity is 30%, calling has positive EV."
        ),
        _stat_heading("MDF — Minimum Defense Frequency"),
        _formula("MDF = Pot before bet  ÷  (Pot before bet + Bet size)"),
        html.P(
            "The minimum fraction of your range you must continue with to prevent the villain"  # noqa: E501
            " from profiting with pure bluffs."
            " If you fold more than 1−MDF, your opponent can bluff profitably regardless of their cards."  # noqa: E501
        ),
        _stat_heading("EV — Expected Value"),
        _formula("EV = (Equity × Pot to Win)  −  ((1 − Equity) × Amount to Lose)"),
        html.P(
            "Shown on all-in spots and showdowns when villain cards are visible."
            " Positive EV (green) = the action was profitable long-term."
            " Negative EV (red) = the action lost expected value."
            " Displayed as '—' when villain cards are unknown."
        ),
        html.P(
            [
                html.Strong("How equity is calculated: "),
                "PokerKit's ",
                html.Code("calculate_equities"),
                " function runs a Monte Carlo simulation — 5,000 random board"
                " run-outs sampled from the remaining deck, evaluated with"
                " standard 5-card high-hand rules. Results are cached per"
                " unique (hole cards + board) combination so repeated views"
                " of the same hand are instant.",
            ]
        ),
        html.P(
            html.Em(
                "Note: equity is only available when the villain's exact hole"
                " cards are known (showdown or all-in). Range-based equity"
                " is not currently supported."
            ),
            style={"color": "#666", "fontSize": "13px"},
        ),
        html.Hr(style={"marginTop": "40px"}),
        html.P(
            html.A("← Back to Home", href="/"),
            style={"color": "#0074D9"},
        ),
    ],
)
