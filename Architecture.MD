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
   > ⚠️ **Known format quirk:** PokerStars `.txt` exports are UTF-8 encoded with a BOM (`\ufeff`) prepended. The splitter discards any content before the first `PokerStars Hand #` header to handle this transparently. Always open these files with `encoding="utf-8"` (not `utf-8-sig`) — the splitter filters the BOM as a by-product of its header-prefix check.
2. **Parsing & Validation:** A Python parsing module reads the raw text, uses regex to extract hand actions, and validates the sequence (ensuring pots balance and actions make logical sense).
3. **Storage:** The parsed, structured data is committed to the SQLite database using raw SQL `INSERT` statements, adhering to the atomic relational schema.
  > ⚠️ **np.int64 parameter bug:** All query functions cast `player_id`, `session_id`, and `hand_id` parameters to Python `int()` before passing to `pd.read_sql_query`. SQLite3 does not reliably accept `numpy.int64` (the type pandas returns for integer columns) as bind parameters — it silently returns empty results in some versions.
4. **Analysis Engine:** Upon a frontend request, the Python backend queries the SQLite database. Data is loaded into Pandas DataFrames.
5. **Mathematical Evaluation:** PokerKit and Pandas process the data to calculate complex metrics (EV, Pot Odds, SPR, MDF) for specific hands or aggregate sessions.
6. **Presentation:** The analyzed DataFrames are passed to the web frontend for rendering charts, tables, and hand replayers.

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
│       │   ├── schema.sql        # CREATE TABLE statements for all 6 tables (incl. settings)
│       │   └── db.py             # get_connection, init_db, upsert_player, insert_*, save_parsed_hand,
│       │                         # update_session_financials, get_setting, set_setting, clear_all_data
│       ├── ingestion/            # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── splitter.py       # split_hands — splits raw session text into hand blocks
│       │   └── pipeline.py       # IngestResult, ingest_file — with re-buy detection
│       ├── analysis/             # ✅ Implemented
│       │   ├── __init__.py
│       │   ├── queries.py        # get_sessions, get_hands, get_actions, get_hero_hand_players,
│       │   │                     # get_hero_timeline, get_hero_actions, get_export_data → DataFrames
│       │   └── stats.py          # vpip_pct, pfr_pct, win_rate_bb100, aggression_factor, wtsd_pct,
│       │                         # total_profit, three_bet_pct, cbet_pct, compute_equity, compute_ev
│       ├── frontend/             # ✅ Implemented (multi-page Dash app)
│       │   ├── __init__.py
│       │   ├── app.py            # create_app() — use_pages=True shell, exposes DB_PATH via Flask config
│       │   ├── upload_handler.py # handle_upload() — decode base64, call ingest_file
│       │   └── pages/
│       │       ├── __init__.py
│       │       ├── home.py       # "/" — navigation hub with links to Upload, Sessions, Dashboard, Settings
│       │       ├── upload.py     # "/upload" — drag-and-drop ingestion; hero username persisted to settings
│       │       ├── sessions.py   # "/sessions" — session list → hand list drill-down
│       │       ├── dashboard.py  # "/dashboard" — KPI cards, bankroll graph, positional stats table
│       │       └── settings.py   # "/settings" — hero username, Clear DB, Export CSV
│       └── config.py             # DB_PATH (overridable via POKERHERO_DB_PATH env var), setup_logging()
├── tests/
│   ├── fixtures/                 # 15 .txt hand history snippets (see TestingStrategy.MD)
│   ├── test_parser.py            # 150 tests across 14 classes
│   ├── test_database.py          # 52 tests across 8 classes (incl. TestSettings)
│   ├── test_ingestion.py         # 28 tests for pipeline, financials, re-buy detection, logging
│   ├── test_frontend.py          # 54 tests for upload handler, multi-page app, page layouts, cards, action view math, dashboard, settings
│   └── test_analysis.py          # 66 tests for queries and stats (vpip, pfr, win_rate, AF, wtsd, timeline, 3-bet, c-bet, EV, equity cache, date filter)
├── data/
│   └── histories/                # Raw .txt session files (git-ignored)
└── pyproject.toml
```

## ⚠️ Known Limitations

### PokerStars format only
The parser (`hand_parser.py`) is tightly coupled to the PokerStars `.txt` hand history export format. No other poker platform's export format (e.g. GGPoker, 888poker, partypoker) is supported. Feeding a non-PokerStars file into the ingestion pipeline will result in parse errors or silently empty output. If multi-platform support is added in the future, the parser module will need to be refactored into a platform-specific adapter pattern.