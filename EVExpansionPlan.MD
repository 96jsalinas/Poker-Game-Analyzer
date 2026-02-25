# EV System Redesign & Range-Based EV Expansion

> **Status:** Partially implemented — Parts A and B complete, Part C steps 7a–8 complete, steps 9–10 and Part D pending.
> **Branch:** `feat/ev-expansion`
> **Scope:** Rewrite of the entire EV subsystem. No backward-compatibility
> constraints — the app has no production users.

## Implementation Status

### ✅ Part A — Foundation (complete)

1. ✅ `compute_ev` returns `(ev, equity)` tuple — `stats.py` updated, `_render_actions` caller updated.
2. ✅ `hand_players.three_bet` + `action_ev_cache` table — `schema.sql`, `hand_parser.py`, `db.py` (`get_action_ev`, `save_action_evs`, `clear_all_data`).
3. ✅ New Analysis Settings — eight range settings in `db.py` (`RANGE_SETTING_DEFAULTS`, `get_range_settings`) and `settings.py` UI.

### ✅ Part B — Range computation (complete)

4. ✅ `ranges.py` — `HAND_RANKING` (169 hands, equity/playability source, user-configurable via Advanced Settings textarea in settings page), `build_range`, `blend_vpip`, `blend_pfr`, `blend_3bet`.
5. ✅ `ranges.py` — `expand_combos` (dead card filtering).
5a. ✅ `ranges.py` — `score_combo_vs_board` (draw-aware: flush draw, OESD, gutshot, two-overcard bonuses; monotone board edge case) + `contract_range` (40% aggressive / 65% passive).
6. ✅ `compute_equity_vs_range` in `stats.py` — full pipeline: `build_range` → `expand_combos` → `contract_range` per intermediate street → MC equity sampling. Returns `(0.0, 0)` when < 5 combos survive.

### ✅ Part C — Integration (in progress)

7a. ✅ Background Callback setup — add `diskcache` dependency; initialise `DiskcacheManager` in `run.py`; wire a minimal smoke-test long callback. No EV logic yet.
7b. ✅ `calculate_session_evs` orchestrator + `identify_primary_villain` helper — computes + persists EV for an entire session across all streets.
8. ✅ Session List "Calculate EVs" button — wired to the background callback from 7a; progress spinner; `✅ EVs ready` status.
9. `_render_actions` loads from `action_ev_cache` — exact + range display, fold comparison for CALL. Replaces inline `compute_ev` call. Update `TestRenderActionsEVShowdown`.
10. Session Report Lucky/Unlucky reads from DB — refactor `_build_ev_summary` + `_build_flagged_hands_list` + remove `_build_equity_map`, `_count_session_showdown_hands`.

### ⏳ Part D — Documentation (pending)

11. `AnalysisLogic.MD` — update EV section with range formula, blend formula, new display rules.
12. `Architecture.MD` — add DB-first principle + `action_ev_cache` to data flow diagram.
13. `DataStructure.MD` — add `action_ev_cache` schema.
14. `UserGuide.MD` + `guide.py` — document "Calculate EVs" button, Est. EV display, fold comparison, range settings.

---

## Critical Corrections (v2)

Three issues in the original draft that would have produced misleading results:

### A. VPIP ≠ Range — The Aggression Gap

A villain who **raised** pre-flop holds their **PFR range** (top PFR% of
hands), not their VPIP range. A villain who **called** pre-flop holds their
**flatting range** (hands ranked from PFR% to VPIP% — strong enough to enter
the pot but not strong enough to raise). Blending VPIP and ignoring the action
type would drastically overestimate villain weakness when facing a raise, leading
to EV values that recommend far too many calls.

A further edge case: if villain **3-bet** (re-raised after a prior raise), their
range is much tighter than their overall PFR range (e.g., 6% vs 14%). Using the
full PFR range against a 3-bet produces EV values that recommend calls with
hands that are mathematically crushed.

**Fix:** `villain_preflop_action` takes four values: `'call'`, `'2bet'`,
`'3bet'`, `'4bet+'`. A separate prior and Bayesian blend is added for 3-bets
(`range_3bet_prior` / `blend_3bet`). 4-bet+ uses a fixed prior
(`range_4bet_prior`) with no Bayesian blend — sample sizes for 4-bets are
almost always too small to be informative. To make villain 3-bet% available for
the blend, `three_bet INTEGER NOT NULL DEFAULT 0` is added to `hand_players`
and set by the parser (same mechanism as `vpip` / `pfr`).

**Bet-level detection (per hand):** when building villain history for a specific
hand, count the number of RAISE actions in the pre-flop sequence before
villain's raise:
- 0 prior raises → `'2bet'` — uses blended PFR%
- 1 prior raise  → `'3bet'` — uses blended 3-bet%
- 2+ prior raises → `'4bet+'` — uses fixed `range_4bet_prior`
- CALL action    → `'call'`  — uses flatting range (VPIP% − PFR%)

### B. Post-Flop Range Contraction is Mandatory, Not Optional

A villain who entered the pot with 35% VPIP will not still hold 35% VPIP worth
of combos on the river after betting multiple streets. Applying the pre-flop
range to a river decision treats them as if they could have 72o in their range —
producing wildly inflated "positive EV" results that would actively teach users
to make losing calls.

**Fix:** `contract_range` is implemented as part of this feature and is applied
for every post-flop street. For each intermediate street between pre-flop and
the current action's street, the range is contracted based on the villain's
observed action (bet/raise → tighter range; check/call → broader range) and the
board at that point. Range EV is therefore available on all streets including
TURN and RIVER — but only when the contracted range is valid (i.e., enough
combos survive contraction to give a meaningful estimate).

### D. `treys.Evaluator` Destroys Draws — Range Contraction Must Use Equity-Aware Scoring

`contract_range` as designed sorts combos by `treys.Evaluator` score and keeps
the top N%. `treys.Evaluator` measures *made-hand strength at this exact moment*
and has zero concept of future equity. On a flop of A♡ 8♡ 2♣:

- K♡ Q♡ (nut flush draw) scores as **King-high** — near the bottom of the list
- 5♠ 2♢ (bottom pair) scores as **a pair** — near the top of the list

A naïve sort-and-slice would keep the bottom pair and discard the nut flush
draw. Repeated over the flop and turn contraction steps, every flush draw and
straight draw would be systematically deleted from the villain's range. By the
river, if the flush completes, the app would confidently report near-zero
probability of a villain flush and recommend calling massive bets that are in
reality crushingly -EV.

**Fix:** A `score_combo_vs_board(combo, board) -> int` helper wraps
`treys.Evaluator` and applies score bonuses for detected draws (lower score =
stronger in treys scale). The bonuses are module-level constants (not
configurable settings — they encode poker theory, not user preferences):

```
FLUSH_DRAW_BONUS  = 3000   # ranks a flush draw (incl. naked-ace on monotone) ~alongside two-pair
OESD_BONUS        = 2000   # ranks an OESD ~alongside a weak pair
GUTSHOT_BONUS     = 800    # ranks a gutshot slightly above pure air
OVERCARD_BONUS    = 400    # ranks two overcards above true air (AK on J72, etc.)
```

Detection logic (applied only when board has < 5 cards, i.e., flop/turn):
- **Flush draw**: `(combo has 2 cards of suit S AND board has 2 of suit S)` OR
  `(combo has 1 card of suit S AND board has 3 of suit S)` — covers both the
  standard 4-flush draw and the naked-ace on a monotone board (e.g. A♡Q♠ on
  K♡8♡2♡) → subtract `FLUSH_DRAW_BONUS`.
- **OESD**: combo + board ranks contain a window of 4 consecutive ranks
  achievable in 2 ways (both open ends) → subtract `OESD_BONUS`.
- **Gutshot**: combo + board ranks form a one-gapped 4-out draw → subtract
  `GUTSHOT_BONUS`.
- **Two overcards**: both combo cards outrank every board card → subtract
  `OVERCARD_BONUS`. Captures hands like A♡K♡ on J♠7♢2♣ that aggressive players
  c-bet at near-100% frequency.
- Bonuses are cumulative (e.g., a flush draw + OESD combo gets both).

`contract_range` calls `score_combo_vs_board` instead of `treys.Evaluator`
directly. On the river (when there are no intermediate draws remaining because
the board is already complete before the current action), the draw bonuses
naturally evaluate to zero — the board already has 5 cards in the final MC
board, but the contraction boards are always flop (3) or turn (4) cards, so
draw detection is always relevant at contraction time.

500+ hero actions × 1000 MC iterations each = several minutes of CPU time.
Standard synchronous Dash callbacks time out after 30–60 seconds, leaving the
spinner orphaned while the backend either crashes or completes unlinked to the
UI.

**Fix:** The "Calculate EVs" button will use **Dash Background Callbacks** via
the `diskcache` manager (built into Dash, no Redis/Celery required). This lets
Dash hand computation off to a background thread and poll for progress. A new
sub-task (Part C, Step 7a) covers the `DiskcacheManager` setup before the button
is wired. `diskcache` is added as a project dependency.

---

## Motivation

The current EV implementation has several limitations:

1. **Only fires for exact known cards** (showdown / all-in). The vast majority
   of post-flop hero decisions show no EV at all.
2. **EV is computed lazily on every Session Report load** — the same expensive
   equity calculation runs each time the user opens a session.
3. **Single number displayed** — no equity %, no fold comparison, no
   indication of whether the estimate is exact or range-based.
4. **Fragmented data model** — `hand_equity` is keyed per hand, but EV
   logically belongs to an action. The Lucky/Unlucky display in the Session
   Report uses a separate code path from the Hand Detail EV column.

---

## Project Principle (new, to be added to `Architecture.MD`)

> **Compute once, persist always.** Any result that requires significant
> computation (equity, EV, range evaluation) must be saved to the database
> immediately after it is computed. Subsequent views load from the database
> they never recompute. Storage is cheap; compute and user time are not.
> This principle applies to all current and future analysis features.

---

## What Gets Removed

| Component | Location | Replacement |
|---|---|---|
| `hand_equity` table | `schema.sql` | `action_ev_cache` table |
| `get_hand_equity` / `set_hand_equity` | `db.py` | `get_action_ev` / `save_action_evs` |
| `_count_session_showdown_hands` | `sessions.py` | not needed (computation is triggered explicitly, not lazy) |
| `_build_equity_map` | `sessions.py` | `load_session_ev_cache` (reads from DB) |
| `_build_ev_summary` | `sessions.py` | `_build_ev_summary` refactored to query `action_ev_cache` directly |
| `_build_flagged_hands_list` | `sessions.py` | same — refactored to query `action_ev_cache` |
| Equity progress-bar in Session Report | `sessions.py` | "Calculate EVs" button + spinner in Session List |
| `TestHandEquityCache` | `test_database.py` | replaced by `TestActionEvCache` |
| `TestBuildEquityMap`, `TestCountSessionShowdownHands` | `test_sessions.py` | removed |

---

## New Database Table: `action_ev_cache`

Replaces `hand_equity`. Keyed per action (not per hand), so every hero action
can carry its own EV and equity values.

```sql
CREATE TABLE IF NOT EXISTS action_ev_cache (
    action_id              INTEGER NOT NULL REFERENCES actions(id),
    hero_id                INTEGER NOT NULL REFERENCES players(id),
    equity                 REAL    NOT NULL,
    ev                     REAL    NOT NULL,
    ev_type                TEXT    NOT NULL CHECK(ev_type IN ('exact', 'range')),
    blended_vpip           REAL,    -- NULL when ev_type = 'exact'
    blended_pfr            REAL,    -- NULL when ev_type = 'exact'
    blended_3bet           REAL,    -- NULL when ev_type = 'exact' or action was not a 3bet
    villain_preflop_action TEXT,    -- 'call'|'2bet'|'3bet'|'4bet+', NULL when ev_type = 'exact'
    contracted_range_size  INTEGER, -- # combos after contraction, NULL when ev_type = 'exact'
    sample_count           INTEGER NOT NULL,
    computed_at            TEXT    NOT NULL, -- ISO 8601 timestamp
    PRIMARY KEY (action_id, hero_id)
);
```

- `ev_type = 'exact'` — villain's cards were known (showdown / all-in).
  Equity is precise.
- `ev_type = 'range'` — villain's cards were estimated. Range was built from
  pre-flop action type + blended VPIP/PFR, then contracted street-by-street.
  `contracted_range_size` records how many combos survived (used in the tooltip).
  If contraction collapses the range to fewer than 5 combos, EV is not computed
  (too few samples to be meaningful) and the action is skipped.
- **`clear_all_data` must include `DELETE FROM action_ev_cache`** (derived
  data, not configuration).
- **`seed` on `init_db` is not needed** — the table starts empty; rows are
  written when the user triggers calculation.

---

## New Settings (added to Analysis Settings in `settings.py`)

| Key | Default | Description |
|---|---|---|
| `range_vpip_prior` | `26.0` | Population-average VPIP used as the Bayesian prior (%). Represents the "average opponent" when little data is available. |
| `range_pfr_prior` | `14.0` | Population-average PFR used as the Bayesian prior (%). Used when villain made a standard 2-bet (open raise). |
| `range_3bet_prior` | `6.0` | Population-average 3-bet% prior (%). Used when villain's pre-flop action was a 3-bet. Significantly tighter than PFR. |
| `range_4bet_prior` | `3.0` | Fixed prior for 4-bet+ ranges (%). No Bayesian blend is applied — sample sizes for 4-bets are almost always too small. |
| `range_prior_weight` | `30` | Prior weight `k` in the Bayesian blend formula. Higher = more regression to the prior when sample is small. |
| `range_sample_count` | `1000` | Number of Monte Carlo iterations for range equity computation. Higher = more accurate but slower. Configurable range: 200–5000. |
| `range_continue_pct_passive` | `65.0` | Percentage of range combos (by hand strength) a villain retains after a passive action (check or call) on a post-flop street. Models hands weak enough to fold to aggression. |
| `range_continue_pct_aggressive` | `40.0` | Percentage of range combos (by hand strength) a villain retains after an aggressive action (bet or raise) on a post-flop street. A tighter range reflecting value-heavy play. Note: bluffs are not explicitly modelled; the tooltip discloses this limitation. |

**Bayesian blend formula (applies to VPIP, PFR, and 3-bet%):**

```
effective_vpip  = (n × observed_vpip  + k × prior_vpip)  / (n + k)
effective_pfr   = (n × observed_pfr   + k × prior_pfr)   / (n + k)
effective_3bet  = (n × observed_3bet  + k × prior_3bet)  / (n + k)
```
4-bet+ uses `prior_4bet` directly (no blend).

Where `n` = hands observed for this villain in the session, `k` =
`range_prior_weight`.

---

## New Module: `src/pokerhero/analysis/ranges.py`

Pure functions only. No database access.

```python
HAND_RANKING: list[str]
# 169 canonical pre-flop hands in descending strength order
# e.g. ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AKo", ...]

def blend_vpip(
    observed: float | None,
    n_hands: int,
    prior: float = 26.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed VPIP with population prior."""

def blend_pfr(
    observed: float | None,
    n_hands: int,
    prior: float = 14.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed PFR with population prior."""

def blend_3bet(
    observed: float | None,
    n_hands: int,
    prior: float = 6.0,
    k: int = 30,
) -> float:
    """Bayesian blend of observed 3-bet% with population prior."""

def build_range(
    vpip_pct: float,
    pfr_pct: float,
    three_bet_pct: float,
    villain_preflop_action: str,  # 'call' | '2bet' | '3bet' | '4bet+'
    four_bet_prior: float = 3.0,
) -> list[str]:
    """Return villain's pre-flop range as a list of hand strings.

    'call'   → flatting range: hands ranked pfr_pct% to vpip_pct%
    '2bet'   → open-raise range: top pfr_pct% of HAND_RANKING
    '3bet'   → 3-bet range: top three_bet_pct% of HAND_RANKING
    '4bet+'  → 4-bet range: top four_bet_prior% of HAND_RANKING (fixed, no blend)
    """

def expand_combos(
    range_hands: list[str],
    dead_cards: set[str],
) -> list[str]:
    """Expand shorthand hands ('AA') to specific card combos ('AcAd'),
    filtering out combos that contain any dead card (hero cards + board cards).
    Returns a list of 'XxYy' strings (two-card combos)."""

def score_combo_vs_board(combo: str, board: str) -> int:
    """Equity-aware hand score for range contraction sorting.

    Wraps treys.Evaluator with draw-detection bonuses so flush draws and
    straight draws are not discarded during contraction (see Correction D).
    Lower return value = stronger / more likely to continue.

    Only meaningful when board has < 5 cards (flop/turn contractions).
    Bonuses are module-level constants: FLUSH_DRAW_BONUS, OESD_BONUS,
    GUTSHOT_BONUS, OVERCARD_BONUS. Detection rules:
      - Flush draw: (combo has 2 suited cards matching 2 board cards of that
        suit) OR (combo has 1 card of suit S AND board has 3 of suit S — naked
        ace/king on monotone board)
      - OESD: combo + board ranks contain a 4-consecutive-rank window, 2 open ends
      - Gutshot: combo + board ranks form a one-gapped 4-out draw
      - Two overcards: both combo cards outrank every board card
    Bonuses are cumulative (e.g., a flush draw + OESD combo gets both).
    """

def contract_range(
    combos: list[str],
    board: str,                      # board cards at this street (3 or 4 cards)
    villain_action: str,             # 'bet' | 'raise' | 'call' | 'check'
    continue_pct_passive: float = 65.0,
    continue_pct_aggressive: float = 40.0,
) -> list[str]:
    """Contract villain range based on board texture and their action on this street.

    Algorithm:
      1. Score each combo using score_combo_vs_board (equity-aware — draws are
         scored favourably so they are not discarded in favour of weak made hands).
      2. Sort combos by score (lower = stronger).
      3. Keep top continue_pct% by count:
           - passive action (check/call)    → continue_pct_passive
           - aggressive action (bet/raise)  → continue_pct_aggressive
      4. Return the surviving combos.

    Note: bluff combos (weak hands bet as a bluff) are not explicitly modelled —
    the contracted range skews toward value hands and draws. This is disclosed
    in the ℹ tooltip on the Est. EV cell.

    Returns [] if no combos survive (caller should skip EV for this action).
    """
```

**Contraction pipeline:** for a hero action at street S, the full sequence is:
1. `build_range(vpip, pfr, villain_preflop_action)` → abstract hands
2. `expand_combos(hands, dead_cards={hero_cards ∪ current_board_cards})` → specific combos
3. For each intermediate street in chronological order (flop if S=TURN; flop+turn if S=RIVER):
   - `contract_range(combos, board_at_street, villain_action_at_street, ...)` → contracted combos
4. MC loop samples from the final contracted combo list + completes the board.

If `contracted_range_size < 5` after all contractions, skip EV for this action.

---

## New Function: `compute_equity_vs_range` in `stats.py`

```python
def compute_equity_vs_range(
    hero_cards: str,
    board: str,                  # full board at the current action's street
    vpip_pct: float,
    pfr_pct: float,
    three_bet_pct: float,
    villain_preflop_action: str, # 'call' | '2bet' | '3bet' | '4bet+'
    villain_street_history: list[tuple[str, str]],
    # [(board_at_street, villain_action), ...] in chronological order
    # e.g. for RIVER action: [("AhKhTh", "BET"), ("AhKhTh2c", "CALL")]
    # e.g. for FLOP action: []
    four_bet_prior: float = 3.0,
    sample_count: int = 1000,
    continue_pct_passive: float = 65.0,
    continue_pct_aggressive: float = 40.0,
) -> tuple[float, int]:
    """Estimate hero equity against a range derived from villain's action history.

    Returns (equity, contracted_range_size).
    Returns (0.0, 0) if contraction collapses range below 5 combos.

    Pipeline:
      1. build_range(vpip, pfr, three_bet_pct, villain_preflop_action)
      2. expand_combos (dead-card filtered against hero cards + full board)
      3. contract_range per intermediate street in villain_street_history
      4. MC loop sampling contracted combos + board completion.
    """
```

---

## `compute_ev` signature change in `stats.py`

```python
# BEFORE
def compute_ev(...) -> float:

# AFTER
def compute_ev(...) -> tuple[float, float]:  # (ev, equity)
```

Callers updated: `_render_actions` in `sessions.py`.

---

## Session List: "Calculate EVs" Button (Level 1)

Each session row in the session table gets a new status column:

| State | Display |
|---|---|
| Not yet calculated | `[📊 Calculate EVs]` button |
| Calculating | `⚙️ Calculating…` spinner (Dash interval-based progress) |
| Calculated | `✅ EVs ready (YYYY-MM-DD)` |

**On click (runs as a Dash Background Callback — see sub-task 7a):**
1. Dash background callback fires for the selected session; a progress bar is
   shown in the UI while the background worker runs.
2. Calls `calculate_session_evs(db_path, session_id, settings)`:
   - Fetches all hero actions for the session (all streets).
   - For each action, identifies the **primary villain** via
     `identify_primary_villain(hand_id, action_id)`:
     - In a heads-up pot: the single other active player.
     - In a multi-way pot: the last aggressor before hero's action in this
       betting round; if no aggressor, the player with the most hands observed.
     - If no suitable villain can be identified: skip range EV for this action.
   - Per action:
     - If villain cards known → `compute_ev` (exact) → save `ev_type='exact'`
     - If villain cards unknown AND hero has cards:
       → determine `villain_preflop_action` ('raise' | 'call')
       → build `villain_street_history` from villain's intermediate street actions
         (queried from the `actions` table; board per street from `hands` columns)
       → call `compute_equity_vs_range` (applies contraction internally)
       → if `contracted_range_size < 5`: skip (EV meaningless) — action shows `—`
       → else: save `ev_type='range'` with `contracted_range_size`
   - Writes all results to `action_ev_cache` in a single transaction.
3. Background callback signals completion; UI refreshes the status column.

The `computed_at` timestamp in the cache drives the status display — if a row
exists for any action in the session, the session shows "✅ EVs ready".
Clicking "Calculate EVs" again overwrites existing rows (recalculates with
current settings).

---

## EV Display Changes in Hand Detail (`_render_actions`)

### Exact EV cell (villain cards known)
```
Equity: 67%   EV: +12.50
[Fold was better ↑]         ← shown only for CALL actions when ev < 0
```

### Range EV cell (villain cards unknown, EVs calculated)
```
Est. Equity: ~54%   Est. EV: +3.40
ℹ Range: 3-bet (6.2% blended, 8 obs.) → 31 combos after 2-street contraction
```
The `ℹ` is a Dash `title` tooltip with full detail: pre-flop range type (call/
2-bet/3-bet/4-bet+), blended stat value and obs. count (or "fixed prior" for
4-bet+), combos before and after contraction, continue-pct settings used,
sample count, and a note that bluffs are not explicitly modelled.

### No EV cell (EVs not yet calculated)
```
—
```
Same as today. The user sees `—` until they click "Calculate EVs" in the
session list.

### Fold comparison
Only shown for **CALL actions**:
- EV(fold) = 0 by definition (you stop risking chips).
- EV(check) for BET actions is unknown without a full game tree — no
  check comparison is shown for BET/RAISE.

---

## Session Report: Lucky/Unlucky (Level 2)

The `_build_ev_summary` and `_build_flagged_hands_list` functions are
refactored to read from `action_ev_cache` rather than computing lazily.

Query: `action_ev_cache JOIN actions WHERE session_id = ? AND ev_type = 'exact'
AND (is_all_in = 1 OR street = 'RIVER')`. This gives one equity value per
hand for the Lucky/Unlucky classification.

If no cache rows exist for the session, the EV Summary section shows:
*"EV analysis not yet calculated. Use the 📊 Calculate EVs button on the
session list."*

---

## Sub-Tasks (implementation order, each is one test commit + one impl commit)

### Part A — Foundation (no UI change visible yet) ✅ COMPLETE

1. ✅ **`compute_ev` returns `(ev, equity)` tuple** — `stats.py` + update
   `_render_actions` caller + update `test_analysis.py`.
2. ✅ **`hand_players.three_bet` + `action_ev_cache` table** — add
   `three_bet INTEGER NOT NULL DEFAULT 0` to `hand_players` in `schema.sql`;
   update `hand_parser.py` to populate it (track raise count in pre-flop
   sequence, set `p.three_bet = p.username in three_bet_set`). Also add
   `action_ev_cache` DDL + `db.py` helpers (`get_action_ev`, `save_action_evs`,
   clear in `clear_all_data`). `test_database.py` + `test_parser.py`.
3. ✅ **New Analysis Settings** — all eight range settings in `settings.py` +
   `_read_analysis_settings` + `test_settings.py`.

### Part B — Range computation (pure functions, no UI) ✅ COMPLETE

4. ✅ **`ranges.py` — `HAND_RANKING` + `build_range` + `blend_vpip` + `blend_pfr` + `blend_3bet`** —
   tests cover: 2-bet uses top PFR%; 3-bet uses top 3-bet%; 4-bet uses fixed
   prior; call returns flatting slice; Bayesian blend for all three blended
   stats; `blend_3bet` falls back to prior when n=0. `test_analysis.py`.
   `HAND_RANKING` uses equity/playability source (169 hands); user-configurable
   via Advanced Settings textarea in `settings.py` (stored as JSON in `settings`
   table; validated to exactly 169 unique hands before saving).
5. ✅ **`ranges.py` — `expand_combos`** — dead card filtering tests.
5a. ✅ **`ranges.py` — `score_combo_vs_board` + `contract_range`** — tests cover:
    (a) flush draw (K♡Q♡ on A♡8♡2♣) scores lower than bottom pair (5♠2♢);
    (b) naked-ace on monotone board (A♡Q♠ on K♡8♡2♡) scores lower than a
    missed offsuit hand; (c) OESD scores lower than pure air on connected board;
    (d) gutshot scores lower than pure air; (e) two overcards (A♡K♡ on J♠7♢2♣)
    score lower than trash (Q9o); (f) bonuses are cumulative (flush draw + OESD);
    (g) passive action retains more combos than aggressive at same continue_pct;
    (h) returns `[]` when continue_pct forces 0 combos. `test_analysis.py`.
6. ✅ **`compute_equity_vs_range` in `stats.py`** — full contraction pipeline.
   Integration tests: (a) FLOP 2-bet action → equity in plausible range;
   (b) FLOP 3-bet action → significantly lower equity (tighter range) than
   2-bet; (c) RIVER action with 2-street history → contracted range;
   (d) range collapse (< 5 combos) returns `(0.0, 0)`.
   Also tests that `villain_preflop_action = '4bet+'` uses fixed prior.

### Part C — Integration ⏳ PENDING

7a. **Background Callback setup** — add `diskcache` dependency; initialise
    `DiskcacheManager` in `run.py`; wire a minimal smoke-test long callback to
    confirm the manager works. No EV logic yet. `test_sessions.py`.
7b. **`calculate_session_evs` orchestrator + `identify_primary_villain`
    helper** — computes + persists EV for an entire session across all streets.
    Collects villain intermediate street actions from the `actions` table and
    board snapshots from the `hands` table. Tests seed FLOP, TURN, and RIVER
    actions with and without villain cards to confirm correct ev_type, correct
    contraction depth, and skip behaviour when range collapses.
8. **Session List "Calculate EVs" button** — wired to the background callback
   from 7a; progress spinner; `✅ EVs ready` status. `test_sessions.py`.
9. **`_render_actions` loads from `action_ev_cache`** — exact + range display,
   fold comparison for CALL. Replaces inline `compute_ev` call.
   Update `TestRenderActionsEVShowdown`.
10. **Session Report Lucky/Unlucky reads from DB** — refactor
    `_build_ev_summary` + `_build_flagged_hands_list` + remove
    `_build_equity_map`, `_count_session_showdown_hands`.

### Part D — Documentation ⏳ PENDING

11. **`AnalysisLogic.MD`** — update EV section with range formula, blend
    formula, new display rules.
12. **`Architecture.MD`** — add DB-first principle + `action_ev_cache` to
    data flow diagram.
13. **`DataStructure.MD`** — add `action_ev_cache` schema.
14. **`UserGuide.MD` + `guide.py`** — document "Calculate EVs" button, Est.
    EV display, fold comparison, range settings.

---

## Files Touched

| File | Change type |
|---|---|
| `schema.sql` | Add `three_bet` to `hand_players`; replace `hand_equity` with `action_ev_cache` (adds `blended_3bet`, `villain_preflop_action` with 4 values, `contracted_range_size`) |
| `hand_parser.py` | Populate `three_bet` flag (track raise count in pre-flop sequence) |
| `db.py` | Replace `get/set_hand_equity` with `get_action_ev`/`save_action_evs` |
| `stats.py` | `compute_ev` returns tuple; add `compute_equity_vs_range` (full pipeline + 3/4-bet); add `identify_primary_villain` |
| `analysis/ranges.py` | **New file** — `HAND_RANKING`, `build_range` (4 action types), `blend_vpip`, `blend_pfr`, `blend_3bet`, `expand_combos`, `score_combo_vs_board` (draw-aware), `contract_range` |
| `sessions.py` | Major refactor — EV calculation, display, Session Report, background callback button |
| `settings.py` | Eight new analysis settings (adds `range_3bet_prior`, `range_4bet_prior`) |
| `run.py` | Add `DiskcacheManager` initialisation |
| `pyproject.toml` | Add `diskcache` dependency |
| `Architecture.MD` | DB-first principle |
| `AnalysisLogic.MD` | EV section update — contraction algorithm, aggression gap, 3-bet/4-bet ranges, blend formulas |
| `DataStructure.MD` | New table docs; updated `hand_players` schema |
| `UserGuide.MD` + `guide.py` | User-facing docs |
| `test_database.py` | Replace `TestHandEquityCache` with `TestActionEvCache`; `hand_players.three_bet` schema test |
| `test_parser.py` | `three_bet` flag set correctly for 2-bet, 3-bet, 4-bet+ hands |
| `test_sessions.py` | Remove `TestBuildEquityMap`, `TestCountSessionShowdownHands`; update EV tests; background callback smoke test |
| `test_analysis.py` | New range + blend (VPIP/PFR/3-bet/4-bet) + contraction tests |
| `test_settings.py` | New settings tests (all eight range settings) |
