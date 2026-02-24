# Testing Strategy & Policy: PokerHero-Analyzer

Because PokerHero-Analyzer relies heavily on accurate mathematical calculations (EV, MDF, SPR) and precise text parsing of fragile PokerStars logs, a rigorous testing strategy is mandatory. A single misparsed line or incorrect pot calculation renders the entire analysis invalid.

## 🧪 1. Core Philosophy: Test-Driven Development (TDD)
This project strictly adheres to a **Fail-First (Red-Green-Refactor)** methodology. No new feature, parser rule, or mathematical function will be written without a failing test preceding it.

### The TDD Workflow
1. **Red (Write the Test):** Write a test defining the expected behavior of a new feature, edge case, or bug fix. Run it. It *must* fail.
2. **Green (Write the Code):** Write the minimum amount of Python or SQL code necessary to make the test pass.
3. **Refactor (Optimize):** Clean up the code, optimize Pandas DataFrames/SQL queries, and ensure all tests still pass.

## 🏗️ 2. The Testing Pyramid

### A. Unit Tests (Fast & Isolated)
* **Parser Rules:** Test individual regex strings against isolated lines of PokerStars text (e.g., extracting "hero_buy_in" from a header).
* **Math Engine:** Test isolated calculations (e.g., passing `pot=100`, `call=50` to a `calculate_pot_odds()` function and asserting it returns `0.333`).
* **PokerKit Integration:** Ensure PokerKit accurately evaluates specific board textures and hand equities before integrating with the database.

### B. Integration Tests (Database & Pipeline)
* **In-Memory SQLite:** All database tests will use an in-memory SQLite database (`sqlite3.connect(':memory:')`) to ensure tests run instantly and don't corrupt the main database.
* **Pipeline Integrity:** Test the flow of `Raw Text -> Parser -> SQL Insert -> Pandas Read`. Ensure that a complete, simple hand history accurately populates all 6 relational tables (`Sessions`, `Hands`, `Players`, `Hand_Players`, `Actions`, `Settings`).

### C. End-to-End (E2E) & System Tests
* **Session Processing:** Feed an entire 500-hand `.txt` session file into the ingestion pipeline and verify total `hero_cash_out` matches the mathematical sum of all `net_result` rows.

## 📁 3. Test Data & Fixtures Strategy

Poker hand histories contain hundreds of edge cases. The `tests/fixtures/` directory contains raw `.txt` snippets, one scenario per file. All fixtures use hero username `jsalinas96`.

| Filename | Game | Scenario covered |
| :--- | :--- | :--- |
| `cash_hero_wins_showdown.txt` | Cash | Hero wins at showdown; baseline for net_result, VPIP, PFR |
| `cash_hero_loses_showdown.txt` | Cash | Hero loses at showdown; villain wins uncalled bet scenario |
| `cash_hero_raises_preflop.txt` | Cash | Hero raises preflop; used for SPR and MDF calculations |
| `cash_standard_hero_folds_preflop.txt` | Cash | Hero folds preflop; tests zero net_result and VPIP=False |
| `cash_uncalled_bet_returned.txt` | Cash | Aggressor's uncalled bet returned; tests `uncalled_bet_returned` field |
| `cash_hero_rebuy.txt` | Cash | Hero goes all-in and loses (starting_stack=42368), then re-buys 50000 in the next hand; tests re-buy detection and hero_buy_in accumulation |
| `cash_dead_blind_and_uncalled_bet.txt` | Cash | Dead blind + uncalled bet combined edge case |
| `cash_side_pot_multiway_allin.txt` | Cash | Multiway all-in with side pot; tests `total_pot` vs eligible pot |
| `cash_decimal_blinds.txt` | Cash | Real-money micro-stakes hand with `$0.01/$0.02` blinds; tests decimal blind parsing |
| `cash_hero_bb_3bets.txt` | Cash | Hero posts BB then 3-bets preflop; tests SPR calculation when BB is the aggressor |
| `cash_eur_blinds.txt` | Cash | Real-money EUR hand with `€` currency prefix on all amounts and ` EUR` suffix in header; tests multi-currency parsing |
| `tournament_standard_with_antes.txt` | Tournament | Standard tournament hand with antes; tests `ante` parsing |
| `tournament_uncalled_bet.txt` | Tournament | Tournament uncalled bet returned |
| `tournament_two_way_split_pot.txt` | Tournament | Split pot divided evenly between two players |
| `tournament_hero_active_multiple_streets.txt` | Tournament | Hero active on flop/turn/river; tests multi-street SPR/MDF |
| `tournament_disconnected_timed_out.txt` | Tournament | Player disconnects mid-hand; tests noise-line handling |

## 🛠️ 4. Tooling & Execution

* **Framework:** `pytest` will be the primary testing framework due to its concise syntax and powerful fixture management.
* **Data Mocking:** `pandas.testing.assert_frame_equal` will be used extensively to verify analytical outputs match expected DataFrame structures.
* **Current test count (601 total):**

| File | Tests | Scope |
| :--- | :--- | :--- |
| `test_parser.py` | 164 | 15 classes — parser rules, SPR/MDF, re-buy, multi-street, EUR currency format, currency detection (USD/EUR/PLAY) |
| `test_frontend.py` | 214 | Upload handler, multi-page routing, page layouts, action view math, dashboard KPIs/highlights, filter controls (incl. game type toggle), guide page, showdown section (incl. winner + hand description + net result display), favourites, DataTable sorting, decimal format helpers, opponent profile cards, profiles panel, villain summary line, first-action archetype badge, session report view (KPI strip, narrative, EV summary, flagged hands, equity-unavailable note), session report navigation (breadcrumb + browse button wiring), settings analysis controls (sample count, lucky/unlucky thresholds, min-hands) |
| `test_analysis.py` | 122 | Queries and stats: VPIP, PFR, Win Rate, AF, WTSD, timeline, 3-bet (incl. blind-position regression), c-bet, EV, equity cache, date filter, currency filter, session player stats, player archetype classification (incl. min_hands kwarg), session analysis queries (get_session_kpis, get_session_hero_actions, get_session_showdown_hands), compute_equity_multiway, multiway showdown query (pipe-separated villain_cards) |
| `test_database.py` | 62 | 9 classes — schema, inserts, deduplication, settings, favourites, currency storage |
| `test_ingestion.py` | 28 | Pipeline, financials, re-buy detection, logging |

## 🚨 5. Bug Fixing Policy
When a bug is discovered (e.g., the app miscalculates EV on a specific river card):
1. Copy the raw PokerStars hand history into a new fixture file.
2. Write a test asserting the correct EV for that hand. (The test will fail).
3. Fix the parser/math logic.
4. Verify the test passes, ensuring the bug is permanently documented and prevented from regressing.