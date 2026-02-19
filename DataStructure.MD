# Data Structure Definition: PokerHero-Analyzer (v2.0)

This schema is optimized for high-speed numerical analysis. It follows a "Numbers First" approach, storing pre-calculated state data to minimize runtime computation for EV and Pot Odds.



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
| `total_pot` | Decimal | Final pot size (Total invested - Uncalled Bet). |
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
| `amount` | Decimal | The amount of the specific bet/raise. |
| `amount_to_call` | Decimal | What the player *faced* before acting (for Pot Odds). |
| `pot_before` | Decimal | The total pot size *before* this action. |
| `is_all_in` | Boolean | Flag to trigger "Effective Stack" logic. |
| `sequence` | Integer | Global order of actions in the hand (1, 2, 3...). |

## 👤 5. Players
Stores players.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | PK | Internal ID. |
| `username` | String | Player username to check on the logs. |
| `preferred_name` | String | Preferred name defined by user for interface. |

---

## 📈 Analysis Logic (Derived)

### 1. Pot Odds
When `is_hero = True`, your script can calculate Pot Odds instantly:
$$Pot\ Odds = \frac{amount\_to\_call}{pot\_before + amount\_to\_call}$$

### 2. Aggression Factor (AF)
Calculated by:
$$\frac{Total\ Bets + Total\ Raises}{Total\ Calls}$$
*Using the `action_type` column across all `Actions` for a specific `player_id`.*

### 3. WTSD% (Went to Showdown)
$$\frac{Count(Hand\_Players.went\_to\_showdown = True)}{Count(Hands\ Played)}$$