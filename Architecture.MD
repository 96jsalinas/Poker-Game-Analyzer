# System Architecture: PokerHero-Analyzer

This document outlines the high-level architecture, technology stack, and data flow for the PokerHero-Analyzer application. The system is designed to parse PokerStars hand histories, store them efficiently, perform complex mathematical evaluations, and serve the insights to a web-based user interface.

## 🏗️ Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Database** | SQLite | Serverless, zero-configuration, and stores the entire database in a local file. Perfect for a fast, local analytical tool. |
| **DB Access** | Raw SQL (`sqlite3`) | Eliminates ORM overhead. Allows for highly optimized, complex analytical queries tailored specifically to our schema. |
| **Data Manipulation** | Pandas & NumPy | Industry standards for aggregating session data, calculating win rates, and manipulating time-series data for the frontend. |
| **Poker Engine** | PokerKit | Handles state management, hand evaluation, and equity calculations. Provides robust foundations for complex poker math. |
| **Frontend UI** | Dash (Plotly) | Pure-Python web framework purpose-built for interactive data dashboards. Tight integration with Pandas and Plotly charts, and sufficient UI flexibility for the drill-down hand replayer (Session → Hand → Action). |

> **Design Philosophy:** Storage is cheap; compute at query time is not. Derived values are pre-calculated at parse time wherever possible. See `DataStructure.MD` for the full "Numbers First, Space is Cheap" rationale.

## 🔄 Data Flow Pipeline

The application follows a strictly linear data processing pipeline, moving from raw text to interactive web insights.

1. **Ingestion:** The user selects a directory containing PokerStars `.txt` hand history files.
   > ⚠️ **Known format quirk:** PokerStars `.txt` exports are UTF-8 encoded and may include a BOM (`\ufeff`). The ingestion pipeline opens files with `encoding="utf-8-sig"` which transparently strips any BOM. Additionally, CRLF line endings are normalised to `\n` before splitting. If a file is empty (produces zero hand blocks after splitting), a warning is logged and the file is skipped.
2. **Parsing & Validation:** A Python parsing module reads the raw text, uses regex to extract hand actions, and validates the sequence (ensuring pots balance and actions make logical sense).
3. **Storage:** The parsed, structured data is committed to the SQLite database using raw SQL `INSERT` statements, adhering to the atomic relational schema.
  > ⚠️ **np.int64 parameter bug:** All query functions cast `player_id`, `session_id`, and `hand_id` parameters to Python `int()` before passing to `pd.read_sql_query`. SQLite3 does not reliably accept `numpy.int64` (the type pandas returns for integer columns) as bind parameters — it silently returns empty results in some versions.
4. **Analysis Engine:** Upon a frontend request, the Python backend queries the SQLite database. Data is loaded into Pandas DataFrames.
5. **Mathematical Evaluation:** EV is **pre-computed and cached** in `action_ev_cache` via the explicit "📊 Calculate EVs" action — it is never computed on page load. Other metrics (SPR, MDF, Pot Odds) are pre-calculated at parse time. PokerKit and Pandas handle equity sampling.
6. **Presentation:** The analyzed DataFrames are passed to the web frontend for rendering charts, tables, and hand replayers.

> **DB-First Principle:** Heavy computations (EV, equity) are stored in the database and read at display time. The session report renders instantly by reading `action_ev_cache`; recalculation only happens when the user explicitly requests it.

## 📂 Current Directory Structure

All modules are implemented. The frontend uses Dash multi-page routing.

```text
pokerhero-analyzer/
├── src/
│   └── pokerhero/
│       ├── __init__.py
│       ├── parser/               # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── models.py         # SessionData, HandData, HandPlayerData, ActionData, ParsedHand
│       │   └── hand_parser.py    # HandParser — regex-based PokerStars text parser
│       ├── database/             # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── schema.sql        # CREATE TABLE statements for all tables (sessions, hands,
│       │   │                         # hand_players, actions, players, settings, target_settings,
│       │   │                         # action_ev_cache) + indexes on actions (hand_id, player_id,
│       │   │                         # hand_id+sequence)
│       │   └── db.py             # get_connection, init_db, upsert_player, insert_*, save_parsed_hand,
│       │                         # update_session_financials, get_setting, set_setting, clear_all_data,
│       │                         # get_action_ev, save_action_evs, get_range_settings
│       ├── ingestion/            # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── splitter.py       # split_hands — splits raw session text into hand blocks
│       │   └── pipeline.py       # IngestResult, ingest_file — with re-buy detection
│       ├── analysis/             # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── queries.py        # get_sessions, get_hands, get_actions, get_hero_hand_players,
│       │   │                     # get_hero_timeline, get_hero_actions, get_hero_opportunity_actions,
│       │   │                     # get_export_data, get_session_player_stats,
│       │   │                     # get_session_kpis, get_session_hero_actions,
│       │   │                     # get_session_hero_ev_actions, get_session_ev_status,
│       │   │                     # get_session_allin_evs → DataFrames;
│       │   │                     # all hero query functions accept optional currency_type='real'|'play'|None
│       │   ├── ranges.py         # HAND_RANKING (169 hands), build_range (4 pre-flop action types),
│       │   │                     # blend_vpip, blend_pfr, blend_3bet, expand_combos (dead-card filtering),
│       │   │                     # score_combo_vs_board (draw-aware), contract_range
│       │   └── stats.py          # vpip_pct, pfr_pct, win_rate_bb100, aggression_factor, wtsd_pct,
│       │                         # total_profit, three_bet_pct, cbet_pct, compute_equity, compute_ev,
│       │                         # compute_equity_vs_range, identify_primary_villain,
│       │                         # calculate_session_evs (EV orchestrator),
│       │                         # classify_player (TAG/LAG/Nit/Fish archetype classification)
│       ├── frontend/             # ✅ Implemented (multi-page Dash app)
│       │   ├── __init__.py
│       │   ├── app.py            # create_app() — use_pages=True shell, exposes DB_PATH via Flask config;
│       │   │                     # dcc.Store(id="theme-store") + 🌚/🌞 toggle button + _toggle_theme,
│       │   │                     # _sync_theme_button, clientside_callback to toggle body.dark class
│       │   ├── assets/
│       │   │   └── theme.css     # CSS custom properties (:root light defaults + body.dark overrides);
│       │   │                     # Dash 4 design token overrides; color-scheme:dark for native controls;
│       │   │                     # DataTable, Plotly, and traffic-light dark mode rules
│       │   ├── upload_handler.py # handle_upload() — decode base64, call ingest_file
│       │   └── pages/
│       │       ├── __init__.py
│       │       ├── home.py       # "/" — navigation hub with links to Upload, Sessions, Dashboard, Settings, Guide
│       │       ├── upload.py     # "/upload" — drag-and-drop ingestion; hero username persisted to settings
│       │       ├── sessions.py   # "/sessions" — 4-level drill-down: session list → session report
│       │       │                 # → hand list → action replay; _describe_hand() uses PokerKit to identify
│       │       │                 # best hand at showdown; _build_opponent_profile_card() renders
│       │       │                 # TAG/LAG/Nit/Fish badges; _render_session_report() assembles
│       │       │                 # KPI strip, narrative, EV summary (reads action_ev_cache),
│       │       │                 # Lucky/Unlucky flagged hands; _build_calculate_ev_section() button
│       │       │                 # triggers calculate_session_evs via synchronous callback
│       │       ├── dashboard.py  # "/dashboard" — KPI cards, bankroll graph, positional stats table
│       │       ├── guide.py      # "/guide" — in-app user guide: stat definitions, app walkthrough
│       │       └── settings.py   # "/settings" — hero username, Clear DB, Export CSV, range settings
│       └── config.py             # DB_PATH (overridable via POKERHERO_DB_PATH env var), setup_logging()
├── tests/
│   ├── fixtures/                 # 17 .txt hand history snippets (see TestingStrategy.MD)
│   ├── test_parser.py            # 177 tests across 16 classes
│   ├── test_database.py          # 83 tests across 9 classes (incl. TestSettings, TestFavorites, currency storage, action_ev_cache, old-schema detection)
│   ├── test_ingestion.py         # 35 tests for pipeline, financials, re-buy detection, logging
│   ├── test_sessions.py          # 232 tests: card rendering, hero row highlighting, math cell, sessions nav/breadcrumb/state,
│   │                             # session/hand filters (EV quality + persistence), favourites, DataTable sorting, format helpers,
│   │                             # EV cell display, background callback wiring, EV summary (all-in text, ev_calculated),
│   │                             # flagged hands, showdown section, villain summary, archetype badge, opponent profile card/panel,
│   │                             # session report view + nav, dark mode compatibility, allin_exact pipeline fixes
│   ├── test_dashboard.py         # 32 tests: position traffic light colouring, KPI highlights, VPIP/PFR gap chart,
│   │                             # stat header tooltips, dark mode compatibility
│   ├── test_app_layout.py        # 28 tests: multi-page app registration, home/upload/sessions/dashboard page layouts,
│   │                             # theme toggle (store, button, face emojis, CSS vars)
│   ├── test_settings.py          # 39 tests: main settings page layout, target settings sub-page
│   ├── test_upload.py            # 9 tests: upload handler, logging
│   ├── test_guide.py             # 6 tests: guide page registration and stat sections
│   └── test_analysis.py          # 222 tests: queries and stats (vpip, pfr, win_rate, AF, wtsd, timeline,
│                                 # 3-bet, c-bet, EV, action_ev_cache, currency filter, session player stats,
│                                 # player archetype classification, ranges, blend formulas, contraction,
│                                 # ev_flags session scope isolation)
├── data/
│   └── histories/                # Raw .txt session files (git-ignored)
└── pyproject.toml
```

## ⚠️ Dash Component Gotchas

Recurring pitfalls specific to the Dash/Plotly frontend layer.

### `dcc.Input` type allow-list
`dcc.Input` only accepts these values for the `type` prop: `"text"`, `"number"`, `"password"`, `"email"`, `"range"`, `"search"`, `"tel"`, `"url"`, `"hidden"`. It does **not** support `"date"`. For date entry fields, use `dcc.Input(type="text")` with a `YYYY-MM-DD` placeholder and compare values as strings in the callback.

### `dash.html` has no `Input` component
The `dash.html` namespace mirrors common HTML block/container elements but does **not** expose `<input>`. Attempting `html.Input(...)` raises `AttributeError: module 'dash.html' has no attribute 'Input'` at runtime. Use `dcc.Input` for all interactive input fields.

### Pattern-matching callbacks fire on component mount (`n_clicks=0`)
When a callback re-renders a container that holds pattern-matching components (e.g. `{"type": "session-row"}`), Dash fires every matching callback for each newly-mounted component with `n_clicks=0`. This causes phantom navigation or side-effects. Always guard the top of pattern-matching `n_clicks` callbacks with:
```python
if not ctx.triggered[0].get("value"):
    raise dash.exceptions.PreventUpdate
```

### CSS `data-*` attributes are not type-safe on Dash components
Passing `**{"data-tip": tooltip}` as a keyword argument to `html.Span()` is rejected by mypy (incompatible type for positional arg). Use a nested child `html.Span(["?", html.Span(tooltip, className="stat-tip")])` with a CSS `:hover` rule to reveal the inner span instead.

---

## ⚠️ Known Limitations

### PokerStars format only
The parser (`hand_parser.py`) is tightly coupled to the PokerStars `.txt` hand history export format. No other poker platform's export format (e.g. GGPoker, 888poker, partypoker) is supported. Feeding a non-PokerStars file into the ingestion pipeline will result in parse errors or silently empty output. If multi-platform support is added in the future, the parser module will need to be refactored into a platform-specific adapter pattern.

### Multi-currency support (USD and EUR)
The parser handles both USD (`$`) and EUR (`€`) PokerStars cash game hand histories. EUR files prefix `€` before every monetary value (stacks, blinds, action amounts, pots) and include a ` EUR` suffix inside the blind parentheses in the header (e.g. `Hold'em No Limit (€0.02/€0.05 EUR)`). The currency symbol is captured by `([€$])?` as group 2 in `_RE_CASH_HEADER`, which shifts all subsequent group indices by one. `_parse_headers()` maps the captured symbol to `'EUR'` / `'USD'` / `'PLAY'` and stores it on `SessionData.currency`. Play-money and tournament chip files use bare numbers with no currency prefix — these always produce `currency='PLAY'`.