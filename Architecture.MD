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
2. **Parsing & Validation:** A Python parsing module reads the raw text, uses regex to extract hand actions, and validates the sequence (ensuring pots balance and actions make logical sense).
3. **Storage:** The parsed, structured data is committed to the SQLite database using raw SQL `INSERT` statements, adhering to the atomic relational schema.
4. **Analysis Engine:** Upon a frontend request, the Python backend queries the SQLite database. Data is loaded into Pandas DataFrames.
5. **Mathematical Evaluation:** PokerKit and Pandas process the data to calculate complex metrics (EV, Pot Odds, SPR, MDF) for specific hands or aggregate sessions.
6. **Presentation:** The analyzed DataFrames are passed to the web frontend for rendering charts, tables, and hand replayers.

## 📂 Current Directory Structure

Parser and database modules are implemented. Analysis and frontend are pending.

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
│       │   ├── schema.sql        # CREATE TABLE statements for all 5 tables
│       │   └── db.py             # get_connection, init_db, upsert_player, insert_*, save_parsed_hand
│       ├── analysis/             # 🔲 Pending — math engine (EV, SPR, MDF, VPIP, PFR, AF)
│       └── frontend/             # 🔲 Pending — Dash app
├── tests/
│   ├── fixtures/                 # 12 .txt hand history snippets (see TestingStrategy.MD)
│   ├── test_parser.py            # 137 tests across 12 classes
│   └── test_database.py          # 44 tests across 7 classes
├── data/
│   └── histories/                # Raw .txt session files (git-ignored)
└── pyproject.toml
```