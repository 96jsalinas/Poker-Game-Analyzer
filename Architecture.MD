# System Architecture: PokerHero-Analyzer

This document outlines the high-level architecture, technology stack, and data flow for the PokerHero-Analyzer application. The system is designed to parse PokerStars hand histories, store them efficiently, perform complex mathematical evaluations, and serve the insights to a web-based user interface.

## 🏗️ Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Database** | SQLite | Serverless, zero-configuration, and stores the entire database in a local file. Perfect for a fast, local analytical tool. |
| **DB Access** | Raw SQL (`sqlite3`) | Eliminates ORM overhead. Allows for highly optimized, complex analytical queries tailored specifically to our schema. |
| **Data Manipulation** | Pandas & NumPy | Industry standards for aggregating session data, calculating win rates, and manipulating time-series data for the frontend. |
| **Poker Engine** | PokerKit | Handles state management, hand evaluation, and equity calculations. Provides robust foundations for complex poker math. |
| **Frontend UI** | Web-Based (TBD) | A decoupled web frontend (e.g., Streamlit, Dash, or custom API + JS) allows for a modern, responsive interface while keeping the Python backend modular. |

## 🔄 Data Flow Pipeline

The application follows a strictly linear data processing pipeline, moving from raw text to interactive web insights.

1. **Ingestion:** The user selects a directory containing PokerStars `.txt` hand history files.
2. **Parsing & Validation:** A Python parsing module reads the raw text, uses regex to extract hand actions, and validates the sequence (ensuring pots balance and actions make logical sense).
3. **Storage:** The parsed, structured data is committed to the SQLite database using raw SQL `INSERT` statements, adhering to the atomic relational schema.
4. **Analysis Engine:** Upon a frontend request, the Python backend queries the SQLite database. Data is loaded into Pandas DataFrames.
5. **Mathematical Evaluation:** PokerKit and Pandas process the data to calculate complex metrics (EV, Pot Odds, SPR, MDF) for specific hands or aggregate sessions.
6. **Presentation:** The analyzed DataFrames are passed to the web frontend for rendering charts, tables, and hand replayers.

## 📂 Proposed Directory Structure

To maintain separation of concerns, the repository is structured into distinct modules.

* `data/` - Stores the `poker_analyzer.db` SQLite file and a subfolder for raw `.txt` hand histories.
* `database/` - Contains the `schema.sql` file and Python scripts for executing raw database connections and queries.
* `parser/` - Houses the logic for reading PokerStars text files and translating them into data dictionaries.
* `analysis/` - The core math engine utilizing Pandas, NumPy, and PokerKit to evaluate database records.
* `frontend/` - (TBD) The web-based UI files and routing logic.
* `tests/` - Unit tests and mock hand histories to ensure parsing and math accuracy.