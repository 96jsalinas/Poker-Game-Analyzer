# Data Structure Definition: PokerHero-Analyzer (v2.0)

This schema is optimized for high-speed numerical analysis. It follows a **"Numbers First, Space is Cheap"** design philosophy: storage is cheap; compute at query time is not. Derived values (SPR, MDF, Pot Odds inputs) are pre-calculated at parse time and stored alongside raw data to guarantee instant UI responsiveness.



## 🏗️ 1. Sessions Table
Defines the environment and stakes for a block of hands.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK (autoincrement) | Unique session identifier. |
| `game_type` | Enum | NLHE (No Limit Hold'em), PLO (Pot Limit Omaha), etc. |
| `limit_type` | Enum | No Limit, Pot Limit, Fixed Limit. |
| `max_seats` | Integer | Table size (e.g., 2, 6, 9). |
| `small_blind` | Decimal | Small blind value. |
| `big_blind` | Decimal | Big blind value. |
| `ante` | Decimal | Value of ante (0 if no ante). |
| `start_time` | DateTime | Timestamp of session start. |
| `hero_buy_in` | Decimal | Total chips invested across the session (initial buy-in + all re-buys). A re-buy is detected when hero's `starting_stack` at hand N exceeds `starting_stack + net_result` from hand N-1. |
| `hero_cash_out` | Decimal | Total chips Hero finished with (final hand's `starting_stack + net_result`). |
| `is_favorite` | Boolean | User-marked favourite session (0 = normal, 1 = favourite). Toggled via `toggle_session_favorite()` in `db.py`. |
| `currency` | TEXT NOT NULL DEFAULT 'PLAY' | Currency of the session: `'USD'` (dollar cash game), `'EUR'` (euro cash game), or `'PLAY'` (play-money or tournament chips). Detected from the currency symbol in the hand header at parse time. |

---

## 🃏 2. Hands Table
A specific deal of cards. Includes "Uncalled Bet" logic for financial balancing.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK (autoincrement) | Internal hand identifier, generated on ingestion. |
| `source_hand_id` | TEXT UNIQUE NOT NULL | Original hand ID from the source app (e.g. PokerStars). Used for deduplication — prevents importing the same hand twice. Not exposed in the UI. |
| `session_id` | INTEGER FK | Link to `Sessions`. |
| `board_flop` | String | e.g., "Ah Kh Qh". |
| `board_turn` | String | e.g., "Js". |
| `board_river` | String | e.g., "Td". |
| `total_pot` | Decimal | Pre-rake pot size (Total invested - Uncalled Bet). To get the net pot, use `Pot_Net = total_pot - rake`. |
| `uncalled_bet_returned` | Decimal | Excess bet returned to the last aggressor. |
| `rake` | Decimal | House fee taken. |
| `timestamp` | DateTime | When the hand occurred. |
| `is_favorite` | Boolean | User-marked favourite hand (0 = normal, 1 = favourite). Toggled via `toggle_hand_favorite()` in `db.py`. |

---

## 👤 3. Hand_Players Table
The "State" of a player for a specific hand. Stores flags for fast stat-checking.
| Column | Type | Description |
| :--- | :--- | :--- |
| `hand_id` | INTEGER FK | Link to `Hands`. |
| `player_id` | INTEGER FK | Link to `Players`. Composite PK with `hand_id`. |
| `position` | Enum | BTN, SB, BB, UTG, MP, CO, etc. |
| `starting_stack` |Decimal | Chips at the very start of the hand. |
| `hole_cards` | String | Hero's cards (or villain cards if shown). |
| `vpip` | Boolean | Did the player voluntarily put money in? |
| `pfr` | Boolean | Did the player raise pre-flop? |
| `went_to_showdown` | Boolean | Did the hand reach the showdown for this player? |
| `net_result` | Decimal | Final profit/loss for this hand (numeric). |

---

## ⚡ 4. Actions Table
Atomic actions. Stores "Contextual Math" to allow for instant Pot Odds analysis.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK (autoincrement) | Internal ID. |
| `hand_id` | INTEGER FK | Link to `Hands`. |
| `player_id` | INTEGER FK | Link to `Players`. |
| `street` | Enum | PREFLOP, FLOP, TURN, RIVER. |
| `action_type` | Enum | FOLD, CHECK, CALL, BET, RAISE, ALL_IN. |
| `amount` | Decimal | Total bet/raise size on the current street (not the incremental cost). e.g., if Hero raises to $35 over a $10 bet, `amount = 35`. |
| `amount_to_call` | Decimal | The total facing bet size Hero must match (e.g., villain bet $25 → `amount_to_call = 25`). Note: this is NOT the incremental cost — if Hero already committed $10, the incremental cost = `amount_to_call - prior_commitment`. |
| `pot_before` | Decimal | The total pot size *before* this action. |
| `is_all_in` | Boolean | Flag to trigger "Effective Stack" logic. |
| `sequence` | Integer | Global order of actions in the hand (1, 2, 3...). |
| `spr` | Decimal | Stack-to-Pot Ratio, pre-calculated at flop commencement. NULL for all other streets/actions. |
| `mdf` | Decimal | Minimum Defense Frequency, pre-calculated when Hero faces a bet. NULL otherwise. |

## 👤 5. Players
Stores players.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK (autoincrement) | Internal ID. |
| `username` | String | Player username to check on the logs. |
| `preferred_name` | String | Preferred name defined by user for interface. |

---

## ⚙️ 6. Settings Table
A simple key/value store for persistent application configuration.
| Column | Type | Description |
| :--- | :--- | :--- |
| `key` | TEXT PK | Setting name (e.g. `hero_username`). |
| `value` | TEXT NOT NULL | Setting value as a string. |

**Known keys:**
| Key | Default | Description |
| :--- | :--- | :--- |
| `hero_username` | — | The PokerStars username of the hero player. Set via the Upload page. |
| `equity_sample_count` | `"2000"` | Monte Carlo samples for equity estimation in the Session Report. |
| `lucky_equity_threshold` | `"40"` | Integer percentage (0–100). Hero wins below this equity → 🍀 Lucky. |
| `unlucky_equity_threshold` | `"60"` | Integer percentage (0–100). Hero loses above this equity → 😞 Unlucky. |
| `min_hands_classification` | `"15"` | Minimum hands observed before an opponent archetype badge is shown. |

---

## 🎯 7. Target Settings Table
Dedicated table for position-specific traffic-light target ranges. Separate from the generic key-value `settings` table.

| Column | Type | Description |
| :--- | :--- | :--- |
| `stat` | TEXT (PK) | Statistic name: `'vpip'`, `'pfr'`, or `'3bet'`. |
| `position` | TEXT (PK) | Canonical position: `'utg'`, `'mp'`, `'co'`, `'btn'`, `'sb'`, `'bb'`. |
| `green_min` | REAL NOT NULL | Lower bound of the green (optimal) zone, inclusive. |
| `green_max` | REAL NOT NULL | Upper bound of the green (optimal) zone, inclusive. |
| `yellow_min` | REAL NOT NULL | Lower bound of the yellow (marginal) zone, inclusive. Must be ≤ `green_min`. |
| `yellow_max` | REAL NOT NULL | Upper bound of the yellow (marginal) zone, inclusive. Must be ≥ `green_max`. |

**18 rows total** (6 positions × 3 stats). All values are REAL percentage floats (e.g. `18.0` = 18%).

**Position mapping at lookup time**: `UTG+1 → utg`, `MP+1 → mp` via `canonical_position()` in `targets.py`.

**Default values** (TAG profile, written to DB on first access via `ensure_target_settings_table(conn)`):
| Position | VPIP green | VPIP yellow | PFR green | PFR yellow | 3-Bet green | 3-Bet yellow |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| UTG | 12–18 | 9–21 | 10–15 | 7–18 | 3–6 | 1–9 |
| MP | 14–20 | 11–23 | 11–17 | 8–20 | 3–7 | 1–10 |
| CO | 18–26 | 14–30 | 13–20 | 10–24 | 5–9 | 3–12 |
| BTN | 28–40 | 22–48 | 18–28 | 14–34 | 7–12 | 4–15 |
| SB | 28–38 | 22–45 | 12–20 | 9–25 | 8–14 | 5–18 |
| BB | 30–42 | 24–50 | 8–14 | 5–18 | 10–16 | 6–20 |

**Key functions** (`src/pokerhero/analysis/targets.py`):
* `ensure_target_settings_table(conn)` — creates table and inserts defaults if it doesn't exist.
* `read_target_settings(conn) -> dict[tuple[str, str], TargetBounds]` — returns all 18 rows as a dict keyed by `(stat, position)`.
* `traffic_light(value, green_min, green_max, yellow_min, yellow_max) -> Literal["green","yellow","red"]` — classifies a stat value against the zone bounds.

---

## 🔢 8. Hand Equity Cache Table
Pre-computed Monte Carlo equity results, persisted to avoid recomputation on repeated session report views.

| Column | Type | Description |
| :--- | :--- | :--- |
| `hand_id` | INTEGER FK (PK) | Link to `Hands`. |
| `hero_id` | INTEGER FK (PK) | Link to `Players` (the hero). Composite PK with `hand_id`. |
| `equity` | REAL NOT NULL | Hero's win equity (0.0–1.0) computed via `compute_equity_multiway`. |
| `sample_count` | INTEGER NOT NULL | Monte Carlo sample count used for this result. Used for staleness detection — if the user changes the `equity_sample_count` setting, rows with a mismatched `sample_count` are treated as cache misses and recomputed. |

**Key functions** (`src/pokerhero/database/db.py`):
* `get_hand_equity(conn, hand_id, hero_id, sample_count) -> float | None` — returns cached equity if `sample_count` matches, else `None`.
* `set_hand_equity(conn, hand_id, hero_id, equity, sample_count) -> None` — upsert via `INSERT OR REPLACE`.

**Migration:** The table is created by `CREATE TABLE IF NOT EXISTS` in `schema.sql`, so `init_db()` creates it transparently on existing databases.

### `get_session_showdown_hands` output schema
| Column | Type | Notes |
| :--- | :--- | :--- |
| `villain_cards` | `str` | Pipe-separated hole-card pairs for all villains who showed cards (e.g. `"Kh Qd"` heads-up; `"Kh Qd\|9c 8c"` for two opponents). Consumed by `compute_equity_multiway`. |
| `villain_username` | `str` | Comma-separated list of all villain usernames who showed cards. |



These dataclasses are what `HandParser.parse()` returns. Field names differ from the DB schema in several places — the mapping is noted below.

### `SessionData`
| Field | Type | Notes |
| :--- | :--- | :--- |
| `table_name` | `str` | Table name string from the log |
| `game_type` | `str` | e.g. `"NLHE"` |
| `limit_type` | `str` | e.g. `"No Limit"` |
| `small_blind` | `Decimal` | |
| `big_blind` | `Decimal` | |
| `ante` | `Decimal` | `0` if no ante |
| `max_seats` | `int` | |
| `is_tournament` | `bool` | |
| `tournament_id` | `str \| None` | |
| `tournament_level` | `str \| None` | e.g. `"Level I"` |
| `currency` | `str` | `'USD'`, `'EUR'`, or `'PLAY'` (default). Detected from `€`/`$` symbol in the cash header; always `'PLAY'` for tournaments. |
> ⚠️ `SessionData` has no `start_time`. Pass `hand.timestamp.isoformat()` to `insert_session(start_time=...)`.

### `HandData`
| Field | Type | DB column |
| :--- | :--- | :--- |
| `hand_id` | `str` | `hands.source_hand_id` (source app ID, used for deduplication) |
| `timestamp` | `datetime` | `hands.timestamp` |
| `button_seat` | `int` | not stored in DB |
| `board_flop` | `str \| None` | |
| `board_turn` | `str \| None` | |
| `board_river` | `str \| None` | |
| `total_pot` | `Decimal` | |
| `rake` | `Decimal` | |
| `uncalled_bet_returned` | `Decimal` | |

### `HandPlayerData`
| Field | Type | Notes |
| :--- | :--- | :--- |
| `username` | `str` | used as key in `player_id_map` |
| `seat` | `int` | not stored in DB |
| `starting_stack` | `Decimal` | |
| `position` | `str` | BTN / SB / BB / UTG / UTG+1 / MP / MP+1 / CO |
| `hole_cards` | `str \| None` | e.g. `"As Kd"` |
| `net_result` | `Decimal` | |
| `vpip` | `bool` | stored as INTEGER 0/1 in DB |
| `pfr` | `bool` | stored as INTEGER 0/1 in DB |
| `went_to_showdown` | `bool` | stored as INTEGER 0/1 in DB |
| `is_hero` | `bool` | not stored in DB; derived via `player_id_map` lookup |

### `ActionData`
| Field | Type | Notes |
| :--- | :--- | :--- |
| `sequence` | `int` | |
| `player` | `str` | username → `player_id` via `player_id_map` |
| `is_hero` | `bool` | stored as INTEGER 0/1 in DB |
| `street` | `str` | `PREFLOP / FLOP / TURN / RIVER` |
| `action_type` | `str` | `POST_BLIND / POST_ANTE / FOLD / CHECK / CALL / BET / RAISE` |
| `amount` | `Decimal` | total bet/raise size on street; 0 for FOLD/CHECK |
| `amount_to_call` | `Decimal` | facing bet Hero must match; 0 for BET/CHECK/FOLD/POST_* |
| `pot_before` | `Decimal` | running pot before this action |
| `is_all_in` | `bool` | |
| `spr` | `Decimal \| None` | set only on first hero FLOP action |
| `mdf` | `Decimal \| None` | set only when `is_hero=True` and `amount_to_call > 0` |

### `ParsedHand`
Top-level container returned by `HandParser(hero="username").parse(text)`:
- `session: SessionData`
- `hand: HandData`
- `players: list[HandPlayerData]`
- `actions: list[ActionData]`

---

## 📈 Analysis Logic (Derived)

All formulas are defined in `AnalysisLogic.MD` as the single source of truth. The columns below support those calculations:

### 1. Pot Odds
When `is_hero = True`, your script can calculate Pot Odds instantly:
$$Pot\ Odds = \frac{amount\_to\_call}{pot\_before + amount\_to\_call}$$

### 2. Aggression Factor (AF)
Calculated by:
$$\frac{Total\ Bets + Total\ Raises}{Total\ Calls}$$
*Using the `action_type` column across all `Actions` for a specific `player_id`. See `AnalysisLogic.MD` for the divide-by-zero fallback rule.*

### 3. WTSD%
See `AnalysisLogic.MD` for the full definition. Uses `Hand_Players.went_to_showdown`.