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
| `play_money_two_hand_session.txt` | Play Money | Two-hand play-money session used by `test_analysis.py` integration tests |

## 🛠️ 4. Tooling & Execution

* **Framework:** `pytest` will be the primary testing framework due to its concise syntax and powerful fixture management.
* **Data Mocking:** `pandas.testing.assert_frame_equal` will be used extensively to verify analytical outputs match expected DataFrame structures.
* **Current test count (863 total):**

| File | Tests | Scope |
| :--- | :--- | :--- |
| `test_parser.py` | 177 | 16 classes — parser rules, SPR/MDF, multiway SPR effective stack, re-buy, multi-street, EUR currency format, currency detection (USD/EUR/PLAY), regex hardening (multi-dot rejection) |
| `test_sessions.py` | 232 | 33 classes — card rendering, hero row highlighting, math cell, sessions nav/breadcrumb/state, session/hand filters (incl. EV quality filter + filter persistence), favourites, DataTable sorting, format helpers (cards text, blind, P&L incl. scientific notation prevention), showdown section (winner + hand description + net result), villain summary line, first-action archetype badge, opponent profile card/panel, session report view (KPI strip, narrative, position breakdown table with traffic lights + Net P&L, EV summary all-in text + ev_calculated empty state, flagged hands with navigation links, equity-unavailable note), batch EV-status labels, dark mode compatibility (CSS vars for P&L, hero row, traffic lights, KPI strip), allin_exact pipeline (gate from known_villain_cards, multiway row written, CALL pot_to_win includes subsequent calls, secondary villain cards used), fold equity for BET/RAISE, search-input wiring, load-session-report guard, cross-page URL parsing, street header board cards |
| `test_analysis.py` | 222 | Queries and stats: VPIP, PFR, Win Rate, AF, WTSD, timeline, 3-bet (incl. blind-position regression, 4-bet exclusion), c-bet, EV, equity cache, date filter, currency filter, session player stats, player archetype classification (incl. min_hands kwarg), session analysis queries, compute_equity_multiway, multiway showdown query, traffic_light (green/yellow/red zones, asymmetric, boundary), read_target_settings (defaults, DB override), straight draw detection (boundary OESD, gutshot, 3-to-a-straight exclusion, tight loop bound verification), ev_flags session scope isolation |
| `test_database.py` | 83 | 9 classes — schema, inserts, deduplication, settings, favourites, currency storage, hand equity cache table (incl. old-schema detection in init_db, get_action_ev range preference), actions indexes |
| `test_dashboard.py` | 32 | 5 classes — position traffic light colouring, KPI highlights (biggest win/loss/best/worst session), VPIP/PFR gap chart, stat header tooltips, dark mode compatibility (CSS vars, theme param), _fmt_pnl scientific notation prevention |
| `test_app_layout.py` | 28 | 5 classes — multi-page app registration, home/upload/sessions/dashboard page layouts, theme toggle (store, button, face emojis, CSS custom property vars) |
| `test_ingestion.py` | 35 | Pipeline, financials, re-buy detection, logging, BOM handling, CRLF normalisation, orphaned session cleanup, IntegrityError classification, empty file warning |
| `test_settings.py` | 39 | 3 classes — main settings page layout, target settings sub-page (/settings/targets — layout, 6-position inputs, load callback defaults, link from main settings), server-side range validation |
| `test_upload.py` | 9 | 3 classes — upload handler (valid/invalid file, duplicate skip, summary message), upload handler logging, malformed input guard |
| `test_guide.py` | 6 | 1 class — guide page registration and stat section presence |

**File organisation strategy:** one test file per app page or source module. `test_frontend.py` was retired when it grew beyond 1,800 lines and 39 classes; its contents were split along page/feature boundaries.

## 🚨 5. Bug Fixing Policy
When a bug is discovered (e.g., the app miscalculates EV on a specific river card):
1. Copy the raw PokerStars hand history into a new fixture file.
2. Write a test asserting the correct EV for that hand. (The test will fail).
3. Fix the parser/math logic.
4. Verify the test passes, ensuring the bug is permanently documented and prevented from regressing.