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

### Highlights
Four cards showing notable hands/sessions:
- 🏆 **Biggest Hand Win** — your largest single-hand profit (click to jump to that hand).
- 💀 **Biggest Hand Loss** — your largest single-hand loss (click to jump to that hand).
- 📈 **Best Session** — the session with the highest net P&L (click to open that session).
- 📉 **Worst Session** — the session with the lowest net P&L (click to open that session).

---

## 🔍 3. Review Sessions (`/sessions`)

A three-level drill-down: **Session List → Hand List → Hand Detail**.

### Level 1: Session List
All your imported sessions in a table. Each row shows the date, stakes (e.g. 500/1000), hands played, and your net result for that session (green = profit, red = loss).

**Filters** (above the table):
| Filter | What it does |
| :--- | :--- |
| From / To | Show only sessions that started in this date range (format: YYYY-MM-DD). |
| Stakes | Multi-select to show only specific stake levels. |
| P&L Min / Max | Show only sessions where your net result fell within this range. |
| Min Hands | Show only sessions with at least this many hands. |

Click any row to drill into the hand list for that session.

### Level 2: Hand List
All hands from the selected session. Each row shows the Hand ID, your hole cards, the final pot size, and your net result for that hand.

**Filters** (above the table):
| Filter | What it does |
| :--- | :--- |
| P&L Min / Max | Show only hands within this profit/loss range. |
| Position | Filter to hands where you were in a specific seat. |
| Saw Flop | Show only hands where you saw the flop. |
| Showdown | Show only hands that went to showdown. |

Use the breadcrumb trail at the top to navigate back to the session list.

### Level 3: Hand Detail
A full chronological replay of a single hand, grouped by street (Pre-Flop, Flop, Turn, River).

Each action row shows:
- **Player** and their position (e.g. `jsalinas96 (BTN)`).
- **Action** — Fold, Call, Raise, Check, or Bet.
- **Amount** — the total bet size for this action.
- **Pot** — the running pot size after this action.
- **Math** (Hero decision points only):
  - **Pot Odds%** — the equity you need to break even calling this bet.
  - **MDF%** — the % of your range you must continue with to prevent the villain profiting purely from bluffs.
  - **SPR** — shown once at the start of the Flop; how many pot-sized bets deep the stacks are.
  - **EV** — shown on all-in spots and showdowns when villain cards are known.

---

## 📐 4. Statistic Definitions

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
$$EV = (Equity \times Pot_{to\_win}) - ((1 - Equity) \times Amount_{to\_lose})$$

Shown on all-in spots and showdowns (when the villain's cards are visible). A positive EV means the action was mathematically profitable in the long run. Displayed in green (positive) or red (negative). Shown as `—` when villain cards are unknown.

---

## ⚙️ 5. Settings (`/settings`)

| Setting | What it does |
| :--- | :--- |
| **Hero Username** | The PokerStars screen name used to identify you in hand histories. All stats recalculate when changed. |
| **Clear Database** | Deletes all imported hands, sessions, and actions. Settings (hero username) are preserved. |
| **Export Data to CSV** | Downloads a CSV file containing your sessions and hands for use in external tools. |
