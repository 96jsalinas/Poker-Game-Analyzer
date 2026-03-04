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
* **$Stack_{Effective}$**: `min(Hero_Stack, max(Active_Villain_Stacks))`. Hero can play for their full stack against the deepest remaining villain; the shallowest villain is irrelevant for Hero's strategic SPR decision.

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
* **Opportunity**: Occurs if **exactly one** raise has occurred before Hero's first *voluntary* action. If two or more raises preceded Hero (pot already 3-bet), it is a 4-bet+ opportunity and is **not** counted. Blind posts (`POST_BLIND`, `POST_ANTE`) are excluded when determining Hero's first action — without this, SB/BB positions would never register any opportunities.

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

### G. Player Archetype Classification ✅ Implemented

Opponents are classified into one of four archetypes using a 2×2 matrix of **VPIP** (Tight/Loose) and **Aggression Ratio** (PFR / VPIP, Passive/Aggressive).

**Thresholds:**
* VPIP threshold: `25%` — at or above → Loose; below → Tight
* Aggression ratio threshold: `0.5` — at or above → Aggressive; below → Passive
* Minimum hands: `15` — fewer than 15 hands seen → returns `None` (no classification)

**Archetype matrix:**

| VPIP \ Aggression | Passive | Aggressive |
|:-----------------:|:-------:|:----------:|
| Tight (< 25%)     | Nit     | TAG        |
| Loose (≥ 25%)     | Fish    | LAG        |

**Implementation:** `classify_player(vpip_pct, pfr_pct, hands_played, min_hands=15)` in `stats.py`. When VPIP = 0, the aggression ratio defaults to 0.0 (Passive), yielding **Nit**. The `min_hands` threshold is user-configurable via the **Settings → Analysis Settings** page (stored as `min_hands_classification` in the settings table).

### H. Confidence Tiers for Opponent Reads ✅ Implemented

Once an opponent has cleared the `min_hands` threshold and receives an archetype badge, the badge's visual style reflects the **confidence tier** — how reliable the read is based on sample size.

**Tier thresholds (fixed, not user-configurable):**

| Tier | Hands range | Badge appearance |
|:-----|:-----------:|:----------------|
| Preliminary | `min_hands` – 49 | Faded (opacity 0.55) |
| Standard | 50 – 99 | Full opacity (default) |
| Confirmed | ≥ 100 | Full opacity + "✓" suffix |

**Implementation:** `confidence_tier(hands_played: int) -> str` in `stats.py`. UI helper `_archetype_badge_attrs(archetype, hands_played)` in `sessions.py` returns `(label, extra_style)` spread into every badge Span across all four badge-creation sites.

### I. Traffic Light Target System ✅ Implemented

Hero VPIP / PFR / 3-Bet stats are classified against configurable per-position zone bounds with a three-tier traffic light result.

**Zone logic:**
$$\text{traffic\_light}(v, g_{min}, g_{max}, y_{min}, y_{max}) = \begin{cases} \text{green} & \text{if } g_{min} \le v \le g_{max} \\ \text{yellow} & \text{if } y_{min} \le v \le y_{max} \text{ (and not green)} \\ \text{red} & \text{otherwise} \end{cases}$$

* The yellow zone must fully enclose the green zone: $y_{min} \le g_{min}$ and $y_{max} \ge g_{max}$ (supports asymmetric zones).
* Values are percentage floats (e.g. `18.0` = 18%).

**Position aliases**: `UTG+1 → utg`, `MP+1 → mp` via `canonical_position()` at lookup time. Settings UI and DB rows use the 6 canonical positions (`utg`, `mp`, `co`, `btn`, `sb`, `bb`).

**Implementation:** `traffic_light(value, green_min, green_max, yellow_min, yellow_max)` and `canonical_position(position)` in `src/pokerhero/analysis/targets.py`. Default bounds represent a balanced TAG profile (stored in `TARGET_DEFAULTS`). See `DataStructure.MD §7` for the full table of defaults and DB schema.

---

## 🧪 4. Expected Value (EV) Logic ✅ Implemented

### A. Exact EV (villain cards known)

When the Hero goes **All-in** and villain cards are known:
$$EV_{Action} = (Equity \times Pot_{to\_Win}) - Wager$$

This is equivalent to:
$$EV_{Action} = (Equity \times Pot_{before}) - ((1 - Equity) \times Wager)$$

Both forms yield the **net expected profit**: Hero wins the full pot (including their own wager) with probability $Equity$, and loses their wager with probability $(1 - Equity)$.

* **Equity**: Hero's win % computed via PokerKit Monte Carlo simulation against the villain's exact hole cards — only valid when hero shoved all-in and villain cards were later revealed.
* **Pot to Win**: Baseline is `pot_before + wager` (what Hero stands to gain). For **all all-in actions** (BET, RAISE, or CALL), `pot_to_win` additionally includes any subsequent non-hero CALL amounts committed on that street after the hero's action, so the pot is not understated in multiway spots where other villains call behind.
* **Wager**: `amount_to_call` for CALL and FOLD actions; `amount` for BET/RAISE actions.
* **Display**: Used for the **Lucky/Unlucky variance summary** only — not shown in the action table.
* **`ev_type = 'allin_exact'`** in `action_ev_cache`.

**Multiway all-in exact EV**: When multiple active villains have known hole cards, the pipeline uses `compute_equity_multiway()` (pipe-separated villain hands). Hero's equity is computed at the moment of the all-in, regardless of side pots formed on later streets.
* **`ev_type = 'allin_exact_multiway'`** in `action_ev_cache`.

### B. Range-based EV (decision review — always computed)

When the villain's cards are not known, equity is estimated against their **inferred range**. The range is built from the villain's observed session VPIP/PFR/3-Bet stats blended with population priors:

**Blend formula:**

$$\text{blended\_stat} = \frac{n \times \text{obs\_stat} + w \times \text{prior}}{n + w}$$

* $n$ = hands observed against this villain in the session.
* $w$ = `range_prior_weight` setting (default 30).
* $\text{obs\_stat}$ = observed VPIP, PFR, or 3-Bet % (0–100 range).
* $\text{prior}$ = population prior from settings (`range_vpip_prior`, `range_pfr_prior`, `range_3bet_prior`).

**Range construction** (`build_range` in `ranges.py`):

1. Hands are ranked by equity × playability score from `HAND_RANKING` (169 canonical hands).
2. The villain's pre-flop action determines which slice of the range to use:
   - `'2bet'` (open raise) → top PFR% of hands by rank.
   - `'call'` (flat call) → hands ranked from PFR% to VPIP% (flatting range).
   - `'3bet'` → top 3-Bet% of hands (strong re-raise range).
   - `'4bet+'` → top 4-Bet% of hands (premium range, defaults to `range_4bet_prior` = 3%).
3. **Street contraction** (`contract_range`): for each intermediate street already played, the range is filtered to remove hands that would likely have folded, using `score_combo_vs_board` (draw-aware scoring) and the continuation % settings.
   Draw detection (`_detect_straight_draw`) classifies straight draws as follows:
   - **OESD (8 outs)**: 4 consecutive rank indices present AND both ends completable (`low ≥ 1` and `low + 4 ≤ 13`). Example: 5-6-7-8 (needs 4 or 9).
   - **Gutshot (4 outs)**: either (a) a boundary 4-consecutive draw where only one end completes (A-K-Q-J needing T, or A-2-3-4 needing 5), or (b) 4 of 5 consecutive rank indices present with one internal gap, where at least one combo card contributes to the window. Example: 5-6-_-8-9 (needs 7).
   - Board-only 3-to-a-straight patterns (e.g., 7-8-9 with unrelated combo) are **not** flagged as draws.
   - Passive villain action (check/call) → keep top 65% (`range_continue_pct_passive`).
   - Aggressive villain action (bet/raise) → keep top 40% (`range_continue_pct_aggressive`).
4. If fewer than 5 combos survive after contraction, the hand is skipped (no EV written).

**Display**: Shows `Est. Equity: ~X%  Est. EV: ±Y` with a ℹ tooltip revealing the pre-flop range type, contracted range size, and sample count. For CALL actions with negative EV, a *"[Fold was better ↑]"* hint appears. For FOLD actions, a verdict is shown instead (see § D Fold EV below). This is the **only EV shown in the action table** — range equity is always used for decision review, regardless of whether villain cards were revealed later.
* **`ev_type = 'range'`** in `action_ev_cache`.
* **`ev_type = 'range_multiway_approx'`** when the hand is multiway (multiple active non-hero players) — flags that the range-based equity is a heads-up approximation against the primary villain only.

### C. EV Cache & Calculation Flow

EV is **not** computed on page load. It is computed explicitly via the **📊 Calculate EVs** button on the Session Report and stored in `action_ev_cache`. This DB-first approach means:

* Session report render is instant — it reads pre-computed values.
* EV is stable across page reloads (no re-computation).
* The session list shows `✅ Ready (YYYY-MM-DD)` once EVs have been calculated.

**Orchestrator**: `calculate_session_evs(db_path, session_id, hero_id, settings)` in `stats.py` — iterates over all hero CALL/BET/RAISE actions **and FOLD actions with `amount_to_call > 0`** in the session, identifies the primary villain via `identify_primary_villain`, and computes **two independent EV tracks** per action:

1. **Range track** (always): `ev_type = 'range'` / `'range_multiway_approx'` — used for the action table. Always computed, always based on villain's inferred range. Detects multiway via active player count.
2. **All-in exact track** (conditional): `ev_type = 'allin_exact'` / `'allin_exact_multiway'` — used for Lucky/Unlucky variance summary. Only written when `is_all_in = 1` **and** villain cards are known. For multiway all-ins, uses `compute_equity_multiway()` against all revealed hands.

Both tracks are written to `action_ev_cache` with the same `action_id` + `hero_id` but different `ev_type` (the PK is `(action_id, hero_id, ev_type)`). Results are bulk-written via `save_action_evs`.

### D. Fold EV (Was the Fold Correct?)

When the hero **folds facing a bet**, the orchestrator computes the **EV of calling** and stores it in `action_ev_cache` for that FOLD action. The wager is `amount_to_call` (same formula as a CALL):

$$EV_{Call} = (Equity \times Pot_{to\_Win}) - ((1 - Equity) \times amount\_to\_call)$$

**Display in action table:**
* `EV_Call > 0` → **⚠ Should have called (call EV: +X)** in red — calling was +EV, so the fold was a mistake.
* `EV_Call ≤ 0` → **✓ Good fold (call EV: −X)** in green — calling was −EV, so the fold was correct.

**Parser note:** FOLD actions now have `amount_to_call` set to the pending bet size at parse time (same formula as CALL: `street_bet − player_committed_this_street`). Open folds (no pending bet) retain `amount_to_call = 0` and are excluded from EV computation. MDF is **not** computed for FOLD actions (it is only meaningful for defending decisions).

### D′. Fold Equity for BET/RAISE Actions

For **BET** and **RAISE** actions, the EV formula incorporates **fold equity** — the probability that the villain folds, awarding hero the pot uncontested:

$$EV_{Bet} = P(fold) \times pot\_before + P(call) \times (equity \times pot\_to\_win - wager)$$

where $P(call) = 1 - P(fold)$.

**Fold probability estimation**: Uses `fold_equity_default_pct` setting (default 40%). This is a population-level default; future versions may use per-villain fold-to-bet statistics when available.

**Storage**: `fold_equity_pct` column in `action_ev_cache` (nullable). Set for BET/RAISE actions on **range-based** EV rows (`range`, `range_multiway_approx`); NULL for CALL/FOLD and always NULL for `allin_exact`/`allin_exact_multiway` rows (villain cards are known because they called, so fold probability is 0 by definition).

### E. Equity Calculation Detail

| Parameter | Value |
| :--- | :--- |
| **Engine** | PokerKit `calculate_equities` |
| **Method** | Monte Carlo simulation |
| **Default samples** | 1 000 (configurable via `range_sample_count` setting) |
| **Deck** | Standard 52-card (`Deck.STANDARD`) |
| **Hand evaluator** | `StandardHighHand` (best 5-card high hand) |

### F. EV Summary Thresholds

The Session Report EV Summary classifies each **all-in hand** as Lucky or Unlucky based on two thresholds, both configurable via **Settings → Analysis Settings**:

| Setting | DB Key | Default | Meaning |
|:--------|:-------|:-------:|:--------|
| Lucky equity threshold | `lucky_equity_threshold` | 40 (%) | Hero wins with equity < this % → 🍀 Lucky |
| Unlucky equity threshold | `unlucky_equity_threshold` | 60 (%) | Hero loses with equity > this % → 😞 Unlucky |

The query that feeds Lucky/Unlucky classification (`get_session_allin_evs`) selects the **latest allin_exact-EV action** per hand (highest `action_id` with `ev_type IN ('allin_exact', 'allin_exact_multiway')`), giving the most representative equity reading regardless of which street the all-in occurred. Hands without an all-in (or where villain cards were not revealed) do not appear in this summary.

---

## ⚠️ 5. Business Rules for SQL Integrity
1. **Atomicity**: No single `Actions` row should represent two players.
2. **Dead Money**: Blinds and Antes are treated as "Dead Money" immediately upon the next action.
3. **Sequence**: The `sequence` integer must be globally unique within a `hand_id` to allow perfect reconstruction of the game tree.