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
* **Pipeline Integrity:** Test the flow of `Raw Text -> Parser -> SQL Insert -> Pandas Read`. Ensure that a complete, simple hand history accurately populates all 5 relational tables (`Sessions`, `Hands`, `Players`, `Hand_Players`, `Actions`).

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
| `cash_dead_blind_and_uncalled_bet.txt` | Cash | Dead blind + uncalled bet combined edge case |
| `cash_side_pot_multiway_allin.txt` | Cash | Multiway all-in with side pot; tests `total_pot` vs eligible pot |
| `tournament_standard_with_antes.txt` | Tournament | Standard tournament hand with antes; tests `ante` parsing |
| `tournament_uncalled_bet.txt` | Tournament | Tournament uncalled bet returned |
| `tournament_two_way_split_pot.txt` | Tournament | Split pot divided evenly between two players |
| `tournament_hero_active_multiple_streets.txt` | Tournament | Hero active on flop/turn/river; tests multi-street SPR/MDF |
| `tournament_disconnected_timed_out.txt` | Tournament | Player disconnects mid-hand; tests noise-line handling |

## 🛠️ 4. Tooling & Execution

* **Framework:** `pytest` will be the primary testing framework due to its concise syntax and powerful fixture management.
* **Data Mocking:** `pandas.testing.assert_frame_equal` will be used extensively to verify analytical outputs match expected DataFrame structures.

## 🚨 5. Bug Fixing Policy
When a bug is discovered (e.g., the app miscalculates EV on a specific river card):
1. Copy the raw PokerStars hand history into a new fixture file.
2. Write a test asserting the correct EV for that hand. (The test will fail).
3. Fix the parser/math logic.
4. Verify the test passes, ensuring the bug is permanently documented and prevented from regressing.