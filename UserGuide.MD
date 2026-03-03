# PokerHero-Analyzer — User Guide

This guide explains how to use the PokerHero-Analyzer, what each screen shows, and what every statistic means. No poker software experience required.

---

## 🚀 1. Getting Started

### Step 1 — Set your hero username
Navigate to **Settings** (`/settings`) and enter the PokerStars screen name you play under. This tells the app which player in each hand history is *you*. All stats and results are calculated from your perspective only.

### Step 2 — Upload your hand histories
PokerStars allows you to export your hand histories as `.txt` files. Once you have those files:

1. Go to **Upload Files** (`/upload`).
2. Drag and drop one or more `.txt` files onto the upload zone (or click to browse).
3. The app will confirm how many hands were imported: *"✅ 24 imported, 0 skipped"*.

> **Tip:** You can upload the same file more than once — the app automatically skips hands it has already seen (duplicate prevention by Hand ID).

### Step 3 — Explore your stats
Once hands are uploaded, head to **Overall Stats** (`/dashboard`) for a high-level overview, or **Review Sessions** (`/sessions`) to drill into individual games.

### Dark Mode
Click the **🌚** button in the top-right navigation bar to switch to dark mode. Click **🌞** to return to light mode. Your preference is saved in the browser and persists across page reloads.

---

## 📊 2. The Dashboard (`/dashboard`)

The dashboard aggregates your performance across all hands ever imported (or within a selected time window).

### Time-Period Filter
Use the radio buttons at the top (**7 days**, **1 month**, **1 year**, **All time**) to scope every number on the page to a specific window. Default is *All time*.

### KPI Cards
| Card | What it means |
| :--- | :--- |
| **Total Profit/Loss** | Your net result in chips/currency across all hands in the selected period. |
| **Win Rate (bb/100)** | How many big blinds you win per 100 hands played. The standard measure of poker profitability. Positive = winning player. |
| **Sessions** | Number of distinct sessions (files) imported in the period. |
| **Hands** | Total number of hands dealt to you in the period. |
| **VPIP%** | How often you voluntarily put chips in the pot pre-flop. |
| **PFR%** | How often you raised pre-flop. |

### VPIP / PFR Gap Chart
A horizontal stacked bar showing three segments:
- 🟢 **PFR%** — hands where you raised pre-flop.
- 🔵 **Call/Limp%** — hands where you entered the pot by calling (the "gap" between VPIP and PFR; a large gap suggests passive pre-flop play).
- ⬜ **Fold%** — hands where you folded pre-flop.

A healthy TAG (Tight Aggressive) profile has a small gap between VPIP and PFR.

### Positional Stats Table
Breaks down your play by seat. Each row is a position (BTN, CO, HJ, SB, BB, etc.).

| Column | Definition |
| :--- | :--- |
| **Hands** | Number of hands dealt to you in this seat. |
| **VPIP%** | See [VPIP](#vpip-voluntarily-put-in-pot) below. Hover the `?` for the formula. |
| **PFR%** | See [PFR](#pfr-pre-flop-raise) below. Hover the `?` for the formula. |
| **3-Bet%** | See [3-Bet%](#3-bet) below. Hover the `?`. |
| **C-Bet%** | See [C-Bet%](#c-bet-continuation-bet) below. Hover the `?`. |
| **AF** | See [Aggression Factor](#af-aggression-factor) below. Hover the `?`. |
| **Net P&L** | Your total profit/loss in this seat. |

> **Hover tooltips:** Each stat column header has a `?` badge. Hover it to see the exact formula.

> **Traffic light colouring:** VPIP%, PFR%, and 3-Bet% cells are shaded 🟢 green, 🟡 yellow, or 🔴 red depending on how your stat compares to your configured target range for that position. Configure ranges in **Settings → Target Stats** (`/settings/targets`). Cells are green when you're in the optimal zone, yellow when slightly outside, and red when well outside.

### Highlights
Four cards showing notable hands/sessions:
- 🏆 **Biggest Hand Win** — your largest single-hand profit (click to jump to that hand).
- 💀 **Biggest Hand Loss** — your largest single-hand loss (click to jump to that hand).
- 📈 **Best Session** — the session with the highest net P&L (click to open that session).
- 📉 **Worst Session** — the session with the lowest net P&L (click to open that session).

---

## 🔍 3. Review Sessions (`/sessions`)

A four-level drill-down: **Session List → Session Report → Hand List → Hand Detail**.

### Level 1: Session List
All your imported sessions in a table. Each row shows the date, stakes (e.g. 500/1000), hands played, and your net result for that session (green = profit, red = loss).

**Filters** (above the table):
| Filter | What it does |
| :--- | :--- |
| From / To | Show only sessions that started in this date range (format: YYYY-MM-DD). |
| Stakes | Multi-select to show only specific stake levels. |
| P&L Min / Max | Show only sessions where your net result fell within this range. |
| Min Hands | Show only sessions with at least this many hands. |
| ★ Favourites only | Show only sessions you have starred. |

Click the **★ / ☆** button on any session row to mark it as a favourite — starred sessions are saved to the database.

Click any row to open the **Session Report** for that session.

### Level 2: Session Report
A narrative overview of your performance in the selected session, before you dive into individual hands.

**KPI Strip** — five at-a-glance cards:
| Card | What it shows |
| :--- | :--- |
| **Hands** | Total hands played in this session. |
| **VPIP** | Your Voluntarily Put In Pot % for this session. |
| **PFR** | Your Pre-Flop Raise % for this session. |
| **AF** | Your Aggression Factor post-flop for this session. |
| **Win Rate** | Your result in bb/100 for this session. |

**Position Breakdown Table** — a compact per-position table showing your VPIP% and PFR% for each seat you played in this session. Cells are shaded with the same traffic-light colours as the dashboard (green / yellow / red) based on your target ranges. Positions with zero hands in the session are omitted.

**Narrative paragraph** — a short written summary describing your VPIP, PFR, AF and overall win/loss rate for the session.

**EV Summary** — shows how your results compared to your equity in **all-in situations** where villain cards were revealed. First, click **📊 Calculate EVs** to compute EV for the session (this runs once and is saved — subsequent views are instant):
- 👍 **Ran above equity** — you won more than your equity predicted (ran good).
- 👎 **Ran below equity** — you won less than your equity predicted (ran bad).
- **~** **Ran near equity** — results were consistent with your equity.

> A hand is classified as *Lucky* when you won with < 40% equity at the all-in moment, and *Unlucky* when you lost with > 60% equity. Only all-in hands where villain cards were revealed are included. Thresholds are configurable in **Settings → Analysis Settings**.

**Notable Hands** — a list of any individual all-in hands flagged as Lucky (🍀) or Unlucky (😞), showing the hand ID and your equity at the all-in moment.

**📊 Calculate EVs** — click this button to compute and save EV for every hero action in the session. The session list will show `✅ Ready (date)` once done. Calculation only needs to run once per session; results persist in the database.

### Level 3: Hand List
All hands from the selected session. Each row shows the Hand ID, your hole cards, the final pot size, and your net result for that hand.

**Filters** (above the table):
| Filter | What it does |
| :--- | :--- |
| P&L Min / Max | Show only hands within this profit/loss range. |
| Position | Filter to hands where you were in a specific seat. |
| Saw Flop | Show only hands where you saw the flop. |
| Showdown | Show only hands that went to showdown. |
| ★ Favourites only | Show only hands you have starred. |
| EV quality | Filter by action quality: **⚠ Bad call (−EV)** shows hands where you called but the range EV was negative; **✓ Good call (+EV)** shows hands where your call had positive range EV; **⚠ Bad fold (should call)** shows hands where your fold had positive calling EV. Multiple values use OR logic. Only applies to hands with calculated EV data. |

Use the breadcrumb trail at the top to navigate back to the session report or the session list.

### Level 4: Hand Detail
A full chronological replay of a single hand, grouped by street (Pre-Flop, Flop, Turn, River).

Click the **☆ Favourite hand** button at the top of the hand to star it (**★**). Starred hands are saved to the database and can be filtered from the hand list.

Each action row shows:
- **Player** and their position (e.g. `jsalinas96 (BTN)`).
- **Action** — Fold, Call, Raise, Check, or Bet.
- **Amount** — the total bet size for this action.
- **Pot** — the running pot size after this action.
- **Math** (Hero decision points only):
  - **Pot Odds%** — the equity you need to break even calling this bet.
  - **MDF%** — the % of your range you must continue with to prevent the villain profiting purely from bluffs.
  - **SPR** — shown once at the start of the Flop; how many pot-sized bets deep the stacks are.
  - **EV** — shown on hero CALL/BET/RAISE/FOLD actions after EVs have been calculated (use **📊 Calculate EVs** on the session report):
    - **Est. EV** (`Est. Equity: ~X%  Est. EV: ±Y`): equity estimated from the villain's inferred range — always shown for every hero action. Hover the ℹ icon to see the pre-flop range type and contracted range size. For CALL actions with negative EV, a *"[Fold was better ↑]"* hint appears.
    - **Fold verdict** (FOLD actions facing a bet): `✓ Good fold (call EV: −X)` in green, or `⚠ Should have called (call EV: +X)` in red — shows whether calling would have been +EV.

---

## 👥 4. Opponent Profiles

PokerHero-Analyzer automatically profiles the other players at your table using their pre-flop statistics gathered during the session. Profiles appear in three places:

- **Opponent Profiles panel** — in the Hand List view, click the **👥 Opponent Profiles** button to expand a panel of profile cards for every player in the session.
- **Villain summary line** — in the Hand Detail view, a line below the board shows all villains in the hand with their archetype badge (e.g. `Villains: Alice **TAG** Bob **Fish**`).
- **First-action badge** — the very first time a villain acts in a hand, their archetype badge appears inline next to their name in the action log. Subsequent actions from the same player are clean.
- **Showdown** — each villain's name at showdown also carries their badge.

> **Minimum sample:** A player must appear in at least **15 hands** in the session before a classification is shown. Below that threshold no badge appears — the sample is too small to be reliable.

### The Four Archetypes

The classification uses two dimensions: **VPIP** (how wide their range is) and the **Aggression Ratio** (PFR ÷ VPIP, how often they raise vs call when they do enter).

| Archetype | VPIP | Aggression | What it means |
| :---: | :---: | :---: | :--- |
| 🔵 **TAG** | < 25% | ≥ 0.5 | Tight-Aggressive — plays a narrow, strong range and usually raises rather than calls. The most common winning player profile. |
| 🟠 **LAG** | ≥ 25% | ≥ 0.5 | Loose-Aggressive — plays many hands and attacks frequently. Can be very strong or very exploitable depending on their post-flop skill. |
| ⚫ **Nit** | < 25% | < 0.5 | Tight-Passive — enters very few pots and mostly calls when they do. Their range is strong but their play is predictable. |
| 🟢 **Fish** | ≥ 25% | < 0.5 | Loose-Passive — calls too wide and rarely raises. The most profitable opponent to find at your table. |

### How to Adjust Against Each Type

**vs TAG 🔵**
- Respect their aggression — a TAG raising into you usually has it. Avoid bluffing into their strong ranges.
- 3-bet or fold against their opens; cold-calling in position can work with hands that play well post-flop.
- They can fold to well-timed aggression on scare cards, so semi-bluffs and well-constructed bluffs have merit.
- Thin value-bet less; they will fold dominated hands rather than pay off.

**vs LAG 🟠**
- Call down lighter — their wide range contains many bluffs and semi-bluffs.
- Position is critical; try to play pots in position against a LAG wherever possible.
- Don't try to out-bluff them — they are less likely to fold once they commit to a pot.
- Let them barrel into your strong hands rather than raising, which may stop the action.

**vs Nit ⚫**
- Steal their blinds aggressively — they fold too often pre-flop.
- When a Nit finally shows aggression, give them credit; their range is extremely value-heavy.
- Don't pay off big bets from a Nit; they almost always have a strong hand when they raise.
- Bluffing is profitable in unopened pots but fold quickly when they fight back.

**vs Fish 🟢**
- Value bet relentlessly and bet larger than you might against thinking players — Fish call too wide.
- Never slow-play your strong hands; extract maximum value every street.
- Avoid bluffing — Fish call down with weak pairs and draws and cannot be pushed off hands.
- When a Fish raises (which is rare), give them credit; they tend to only raise with strong holdings.

---

## 📐 5. Statistic Definitions

### VPIP (Voluntarily Put In Pot)
$$VPIP = \frac{\text{Hands where you called or raised pre-flop}}{\text{Total Hands}}$$

Measures how "loose" your pre-flop game is. A VPIP of 20–28% is typical for a tight-aggressive cash game player. Higher = looser, lower = tighter. Posting blinds does **not** count as voluntary.

---

### PFR (Pre-Flop Raise)
$$PFR = \frac{\text{Hands where you raised pre-flop}}{\text{Total Hands}}$$

Measures how aggressive you are before the flop. Should always be ≤ VPIP. The gap between VPIP and PFR is how often you *call* instead of raise pre-flop — a large gap can indicate passive tendencies.

---

### 3-Bet%
$$3Bet\% = \frac{\text{Times you re-raised a pre-flop raiser}}{\text{Opportunities to 3-bet}}$$

An *opportunity* occurs any time someone opens with a raise before your action. A higher 3-Bet% means you defend/attack more aggressively against openers. Typical range: 5–12% for a solid TAG.

---

### C-Bet% (Continuation Bet)
$$CBet\% = \frac{\text{Times you bet the flop as the pre-flop aggressor}}{\text{Times you were pre-flop aggressor and saw the flop}}$$

When you raised pre-flop and saw the flop, how often do you follow up with a bet? Low C-Bet% (< 40%) may signal passivity post-flop; very high (> 85%) may be exploitable.

---

### AF (Aggression Factor)
$$AF = \frac{\text{Post-flop Bets} + \text{Post-flop Raises}}{\text{Post-flop Calls}}$$

Measures how aggressively you play post-flop relative to passively calling. An AF above 2.0 is generally considered aggressive. Below 1.0 is passive. Folds and checks are excluded.

---

### Win Rate (bb/100)
$$WinRate = \frac{\text{Total net chips won}}{\text{Total hands}} \times 100$$

The gold-standard measure of poker profitability. Expressed in big blinds per 100 hands played. A positive number means you are a winning player at that stake. 5+ bb/100 is considered strong for live cash games.

---

### SPR (Stack-to-Pot Ratio)
$$SPR = \frac{\text{Effective stack at flop}}{\text{Pot at start of flop}}$$

Calculated once at the beginning of the flop. The *effective stack* is the smaller of Hero's stack and the relevant villain's stack. SPR tells you how committed you are to the pot:

| SPR | Interpretation |
| :--- | :--- |
| < 4 | Very low — easy to commit with top pair or better. |
| 4 – 13 | Medium — implied odds matter; strong draws become more valuable. |
| > 13 | Deep — premium hands required to stack off; post-flop skill matters most. |

---

### Pot Odds
$$\text{Pot Odds} = \frac{\text{Amount to Call}}{\text{Total Pot (after call)}}$$

The minimum equity (% chance of winning) you need to make a break-even call. If pot odds are 25% and your hand equity is 30%, calling has positive expected value.

---

### MDF (Minimum Defense Frequency)
$$MDF = \frac{\text{Pot before bet}}{\text{Pot before bet} + \text{Bet size}}$$

The minimum % of your range you must continue with (call or raise) to prevent the villain from profiting with pure bluffs. If you fold more than `1 − MDF`, your opponent can bluff profitably regardless of their cards.

---

### EV (Expected Value)
$$EV = (Equity \times Pot_{to\_win}) - ((1 - Equity) \times Wager)$$

Shown on hero CALL/BET/RAISE actions once EVs have been calculated for the session. Positive EV (green) = the action was profitable long-term. Negative EV (red) = the action lost expected value. `—` when no EV has been calculated for this action.

Two display modes:
- **Est. EV** — the only EV shown in the action table. Equity is estimated by building a range from the villain's session VPIP/PFR/3-Bet stats (blended with population priors) and contracting it street by street based on their actions. This reflects what you could have reasonably known at the time of the decision. Hover the ℹ icon for details.

For CALL actions with **negative estimated EV**, a *"[Fold was better ↑]"* hint is shown.

> **All-In EV**: For hands where you went all-in and the villain's cards were revealed, the EV Summary section uses *exact* equity (computed against villain's actual cards at the all-in moment) for Lucky/Unlucky classification. This is separate from the action table display.

For **FOLD actions facing a bet**, the EV column shows a verdict: **✓ Good fold (call EV: −X)** (green) when calling would have been −EV, or **⚠ Should have called (call EV: +X)** (red) when calling would have been +EV.

> **How equity is calculated:** Using PokerKit's `calculate_equities` via Monte Carlo simulation. The number of samples is configurable via **Range sample count** in Analysis Settings (default: 1 000).

---

## ⚙️ 6. Settings (`/settings`)

### Hero Username
The PokerStars screen name used to identify you in hand histories. All stats recalculate when changed.

### 📊 Analysis Settings
Fine-tune how the Session Report computes and displays equity-based statistics.

| Setting | Default | What it does |
| :--- | :---: | :--- |
| **Lucky equity threshold (%)** | 40 | Hero wins a hand with equity *below* this % → flagged as 🍀 Lucky. |
| **Unlucky equity threshold (%)** | 60 | Hero loses a hand with equity *above* this % → flagged as 😞 Unlucky. |
| **Min hands for archetype badge** | 15 | Minimum hands observed against an opponent before a TAG/LAG/Nit/Fish badge is displayed. |
| **Range sample count** | 1 000 | Monte Carlo samples per EV computation. Higher = more accurate but slower. |
| **VPIP prior (%)** | 26 | Population VPIP used when few hands are observed against a villain. |
| **PFR prior (%)** | 14 | Population PFR used when few hands are observed against a villain. |
| **3-Bet prior (%)** | 6 | Population 3-Bet % used when few hands are observed. |
| **4-Bet prior (%)** | 3 | Top % of hands used as the 4-bet+ range. |
| **Prior weight (hands)** | 30 | How strongly the population prior anchors the estimate. Equivalent to observing this many hands at the prior values. |
| **Continue % passive** | 65 | % of the villain's range assumed to continue after a passive action (check/call) on a street. |
| **Continue % aggressive** | 40 | % of the villain's range assumed to continue after an aggressive action (bet/raise) on a street. |

### 🎯 Target Stats (`/settings/targets`)
Configure per-position optimal ranges for VPIP, PFR, and 3-Bet. Accessible via the **Target Stats** link on the main Settings page.

Each stat × position combination has four numeric inputs defining two zones:

| Field | What it means |
| :--- | :--- |
| **Green Min / Green Max** | The optimal zone. Stats within this range are highlighted green. |
| **Yellow Min / Yellow Max** | The marginal zone (must enclose the green zone). Stats outside green but within yellow are highlighted yellow. Stats outside yellow entirely are highlighted red. |

Positions configured: **UTG, MP, CO, BTN, SB, BB**. (UTG+1 maps to UTG, MP+1 maps to MP.)

Default values represent a balanced TAG profile. Novice users can ignore this page — sensible defaults ensure all cells still show a colour from day one.

### Data Management
| Action | What it does |
| :--- | :--- |
| **Clear Database** | Deletes all imported hands, sessions, and actions. Settings are preserved. |
| **Export Data to CSV** | Downloads a CSV file containing your sessions and hands for use in external tools. |
