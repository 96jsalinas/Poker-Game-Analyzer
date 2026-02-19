# Data Structure Definition: PokerHero-Analyzer (v2.0)

This schema is optimized for high-speed numerical analysis. It follows a **"Numbers First, Space is Cheap"** design philosophy: storage is cheap; compute at query time is not. Derived values (SPR, MDF, Pot Odds inputs) are pre-calculated at parse time and stored alongside raw data to guarantee instant UI responsiveness.



## 🏗️ 1. Sessions Table
Defines the environment and stakes for a block of hands.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | PK | Unique session identifier. |
| `game_type` | Enum | NLHE (No Limit Hold'em), PLO (Pot Limit Omaha), etc. |
| `limit_type` | Enum | No Limit, Pot Limit, Fixed Limit. |
| `max_seats` | Integer | Table size (e.g., 2, 6, 9). |
| `small_blind` | Decimal | Small blind value. |
| `big_blind` | Decimal | Big blind value. |
| `ante` | Decimal | Value of ante (0 if no ante). |
| `start_time` | DateTime | Timestamp of session start. |
| `hero_buy_in` | Decimal | Total chips Hero started with. |
| `hero_cash_out` | Decimal | Total chips Hero finished with. |

---

## 🃏 2. Hands Table
A specific deal of cards. Includes "Uncalled Bet" logic for financial balancing.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | PK | Unique Hand ID (from PokerStars log). |
| `session_id` | FK | Link to `Sessions`. |
| `board_flop` | String | e.g., "Ah Kh Qh". |
| `board_turn` | String | e.g., "Js". |
| `board_river` | String | e.g., "Td". |
| `total_pot` | Decimal | Pre-rake pot size (Total invested - Uncalled Bet). To get the net pot, use `Pot_Net = total_pot - rake`. |
| `uncalled_bet_returned` | Decimal | Excess bet returned to the last aggressor. |
| `rake` | Decimal | House fee taken. |
| `timestamp` | DateTime | When the hand occurred. |

---

## 👤 3. Hand_Players Table
The "State" of a player for a specific hand. Stores flags for fast stat-checking.
| Column | Type | Description |
| :--- | :--- | :--- |
| `hand_id` | FK | Link to `Hands`. |
| `player_id` | FK | Link to `Players`. |
| `position` | Enum | BTN, SB, BB, UTG, MP, CO, etc. |
| `starting_stack` | Decimal | Chips at the very start of the hand. |
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
| `id` | PK | Internal ID. |
| `hand_id` | FK | Link to `Hands`. |
| `player_id` | FK | Link to `Players`. |
| `is_hero` | Boolean | Optimization flag for Hero-only queries. |
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
| `id` | PK | Internal ID. |
| `username` | String | Player username to check on the logs. |
| `preferred_name` | String | Preferred name defined by user for interface. |

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