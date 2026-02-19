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

Poker hand histories contain hundreds of edge cases. The `tests/fixtures/` directory must contain raw `.txt` snippets for the following specific scenarios:

* **Standard Hands:** Normal pre-flop raise, c-bet, fold.
* **Split Pots:** Hands where the pot is divided evenly among multiple players.
* **Side Pots & Multi-way All-ins:** Crucial for testing the `total_pot` vs. `eligible_pot` math.
* **Uncalled Bets Returned:** Hands where a player bets, everyone folds, and the bet is returned (ensuring pot totals balance).
* **Dead Blinds / Straddles:** Edge cases in pre-flop posting.
* **Incomplete Hands:** Hands where a player disconnects or the server crashes mid-hand.

## 🛠️ 4. Tooling & Execution

* **Framework:** `pytest` will be the primary testing framework due to its concise syntax and powerful fixture management.
* **Data Mocking:** `pandas.testing.assert_frame_equal` will be used extensively to verify analytical outputs match expected DataFrame structures.

## 🚨 5. Bug Fixing Policy
When a bug is discovered (e.g., the app miscalculates EV on a specific river card):
1. Copy the raw PokerStars hand history into a new fixture file.
2. Write a test asserting the correct EV for that hand. (The test will fail).
3. Fix the parser/math logic.
4. Verify the test passes, ensuring the bug is permanently documented and prevented from regressing.