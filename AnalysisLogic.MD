# Analysis Logic & Statistical Definitions (Hyper-Specific)

This document serves as the definitive source of truth for all mathematical calculations and data processing rules within the PokerHero-Analyzer.

---

## 🏗️ 1. Data Processing Conventions

### A. The "Amount" Rule
To maintain compatibility with raw PokerStars logs while enabling easy math:
* **`Actions.amount`**: Stores the **Total Bet/Raise Size** on the current street.
* **`incremental_cost`**: A derived value (not stored). Calculated as `Actions.amount - prior_commitment`, where `prior_commitment` is what the player already put in on this street. Used to update the player's stack.
    * *Example*: Pot is 20. Player A bets 10. Hero raises to 35.
    * `Actions.amount` for Hero = 35.
    * `incremental_cost` for Hero = 35 (nothing previously committed).
    * *Example 2*: Player A calls.
    * `Actions.amount` for Player A = 35.
    * `incremental_cost` for Player A = 25 (35 total - 10 already committed).
* **`Actions.amount_to_call`**: The total facing bet size stored at parse time (equals the previous aggressor's `amount`). Different from `incremental_cost` — use `amount_to_call` for Pot Odds, use `incremental_cost` for stack updates.

### B. Uncalled Bets & Rake
* **Uncalled Bet**: Any amount of a bet/raise that is not matched by a caller. 
* **Net Pot**: 
  $$Pot_{Net} = (\sum Actions_{Amount} - Uncalled\_Bet) - Rake$$
* **Hero Net Result**:
  $$Result = (Pot_{Net} \text{ if Hero wins}) - \sum Hero\_Incremental\_Costs$$

---

## 📈 2. Situational Math (Real-time Analysis)

### A. Stack-to-Pot Ratio (SPR)
Calculated only at the **commencement of the Flop**.
$$SPR = \frac{Stack_{Effective}}{Pot_{Flop\_Start}}$$
* **$Stack_{Effective}$**: The smallest stack between Hero and the active Villain(s).
* **Logic**: If multiple Villains are in, use the largest stack among Villains that Hero can effectively play for, capped by Hero's own stack.

### B. Minimum Defense Frequency (MDF)
The mathematical "line in the sand" to prevent being exploited by bluffs.
$$MDF = \frac{Pot_{Before}}{Pot_{Before} + Bet_{Size}}$$
* **$Pot_{Before}$**: The total pot before the current bet was placed.
* **$Bet_{Size}$**: The current bet/raise amount Hero is facing.

### C. Pot Odds
The required equity to make a "break-even" call.
$$Pot\_Odds = \frac{Call\_Amount}{Pot_{Total\_Current} + Call\_Amount}$$
* **$Call\_Amount$**: The specific amount Hero must add to stay in the hand.
* **$Pot_{Total\_Current}$**: The pot size including all bets already on the table.

---

## 📊 3. Player Frequency Statistics (The Dashboard)

### A. VPIP (Voluntarily Put In Pot)
$$VPIP = \frac{Count(\text{Hands where Hero calls/raises Pre-flop})}{Total\_Hands}$$
* **Constraint**: Excludes "checking" in the Big Blind or folding. Posting blinds is NOT voluntary.

### B. PFR (Pre-Flop Raise)
$$PFR = \frac{Count(\text{Hands where Hero raises/3-bets Pre-flop})}{Total\_Hands}$$

### C. 3-Bet % ✅ Implemented
$$3Bet\% = \frac{Count(\text{Hero raises vs a previous raiser})}{Count(\text{Opportunities to 3-bet})}$$
* **Opportunity**: Occurs if a player opened the pot with a raise before Hero's action.

### D. C-Bet % (Continuation Bet) ✅ Implemented
$$CBet\% = \frac{Count(\text{Hero bets Flop})}{Count(\text{Opportunities to C-bet})}$$
* **Opportunity**: Hero was the **last aggressor** on the Pre-flop street and the hand reached the Flop.

### E. Aggression Factor (AF)
A measure of post-flop aggression.
$$AF = \frac{\sum (Bets + Raises)}{\sum Calls}$$
* **Note**: Calculated for Post-flop streets only. Folds and Checks are ignored.
* **Fallback**: When player has 0 calls post-flop, give a max integer value to avoid divide by zero error

### F. WTSD% (Went to Showdown)
The frequency a player reaches showdown after seeing the flop.
$$WTSD\% = \frac{Count(Hand\_Players.went\_to\_showdown = True)}{Count(\text{Hands where player saw the Flop})}$$

---

## 🧪 4. Expected Value (EV) Logic

When the Hero goes **All-in**, or the hand reaches **Showdown**:
$$EV_{Action} = (Equity \times Pot_{to\_Win}) - ((1 - Equity) \times Amount_{to\_Lose})$$

* **Equity**: The % chance of winning based on Hero's cards vs. Villain's cards (or range).
* **Pot to Win**: The current pot + Villain's call/bet.
* **Amount to Lose**: The amount Hero must risk to make the play.

---

## ⚠️ 5. Business Rules for SQL Integrity
1. **Atomicity**: No single `Actions` row should represent two players.
2. **Dead Money**: Blinds and Antes are treated as "Dead Money" immediately upon the next action.
3. **Sequence**: The `sequence` integer must be globally unique within a `hand_id` to allow perfect reconstruction of the game tree.