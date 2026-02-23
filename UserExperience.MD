# User Experience (UX) & App Flow

This document defines the navigation structure and user interface logic for the PokerHero-Analyzer. The app follows a hierarchical "Drill-Down" approach: **Overall -> Session -> Hand -> Action.**

---

## 🗺️ 1. Main Navigation Menu
The entry point of the application (`/`). Currently a simple hub page.

* **[1] Upload Files** (`/upload`): The "Ingestion" hub. ✅ Implemented.
* **[2] Review Sessions** (`/sessions`): Historical log of all processed games. ✅ Implemented.
* **[3] Overall Stats** (`/dashboard`): The "Hero Dashboard." ✅ Implemented.
* **[4] Settings** (`/settings`): User and App configuration. ✅ Implemented.
* **[5] User Guide** (`/guide`): In-app guide covering all screens and stat definitions (VPIP, PFR, 3-Bet%, C-Bet%, AF, Win Rate, SPR, Pot Odds, MDF, EV including equity method). ✅ Implemented.

---

## ⚙️ 2. Settings ✅ Implemented
* **Hero Username**: Persisted in the `settings` DB table. Set in the dedicated `/settings` page; also available on the Upload page for convenience.
* **Data Management**: "Clear Database" deletes all hands/sessions/actions/players (settings preserved). "Export Data to CSV" downloads sessions + hands as `pokerhero_export.csv`.

---

## 📤 3. Upload Files ✅ Implemented
* **Upload Interface**: A drag-and-drop zone or file picker for `.txt` files.
* **Hero Username Input**: Entered once; auto-saved to the `settings` table and pre-populated on return visits.
* **Processing Feedback**:
    * Summary of upload: *"✅ 24 imported, 0 skipped"* or *"⚠️ 2 skipped (duplicates)"*.
* **Error Log**: If a file is corrupted or in an unsupported format, shows a red error message.

---

## 🔍 4. Review Sessions (The Drill-Down) ✅ Implemented

Navigation uses a **breadcrumb** pattern — only one level is visible at a time. Clicking a row advances the view; clicking a breadcrumb crumb navigates back.

```
Sessions  →  Sessions › 2026-02-16 250/500  →  Sessions › 2026-02-16 250/500 › All Hands  →  Sessions › 2026-02-16 250/500 › Hand #2597...
```

### Level 1: Session History ✅
A table view showing all played sessions.
* **Columns**: Date, Stakes (e.g., 100/200), Hands Played, Net Profit/Loss (green/red).
* **Sorting** ✅ Implemented — click any column header to sort ascending/descending (`sort_action="native"` on `dash_table.DataTable`).
* **Action**: Clicking any cell in a row navigates to the **Session Report** for that session.
* **Filters** ✅ Implemented — filter bar above the table: date range (from/to), stakes multiselect, P&L min/max, min hands, Favourites only. Updates table data without page reload via `_apply_session_filters` callback + `session-data-store`.
* **Favourite** ✅ Implemented — ★/☆ button in the top-right corner of the hand list view; clicking toggles `is_favorite` on the current session (gold star = favourite). Persisted to DB via `_toggle_session_fav` callback + `session-fav-id-store`.

### Level 2: Session Report ✅
A narrative overview of the selected session, assembled from three query DataFrames (`get_session_kpis`, `get_session_hero_actions`, `get_session_showdown_hands`).
* **Narrative paragraph** — template-driven sentence summarising VPIP%, PFR%, AF and win rate for the session. Built by `_build_session_narrative(kpis_df, actions_df, session_label)`.
* **KPI strip** — five at-a-glance cards (Hands, VPIP%, PFR%, AF, Win Rate bb/100). Built by `_build_session_kpi_strip(kpis_df, actions_df)`.
* **EV Summary** — equity-based luck indicator. For each showdown hand with known villain cards, computes `compute_equity(hero_cards, villain_cards, board, 2000)`. Lucky: won with eq < 0.4. Unlucky: lost with eq > 0.6. Verdict: `👍 Ran above equity` / `👎 Ran below equity` / `~ Ran near equity`. Built by `_build_ev_summary(showdown_df)`.
* **Notable Hands** — lists each hand classified as 🍀 Lucky or 😞 Unlucky with the equity percentage. Built by `_build_flagged_hands_list(showdown_df)`.
* **Browse all N hands button** (`session-report-browse-btn`) — navigates to the Hand List for this session via `_browse_session_hands` callback.
* State: `level="report"`, `session_id=X`.

### Level 3: Hand List (Within a Session) ✅
A detailed list of every hand dealt in that session.
* **Columns**: Hand ID, Hero Cards (Hole Cards with suit symbols), Final Pot, Net Result.
* **Sorting** ✅ Implemented — click any column header to sort ascending/descending.
* **Action**: Clicking any cell in a row navigates to the **Hand Action View**.
* **Filters** ✅ Implemented — filter bar: P&L min/max, position multiselect, Saw Flop checkbox, Showdown checkbox, Favourites only. Updates table without page reload via `_apply_hand_filters` callback + `hand-data-store`.
* **Breadcrumb**: `Sessions > Session Label (→ report) > All Hands`.

### Level 4: Hand Action View ✅
A chronological breakdown of the specific hand.
* **Header**: Hand # and board cards (Flop | Turn | River).
* **Favourite** ✅ Implemented — ★/☆ button in the top-right of the action view header; clicking toggles `is_favorite` on the current hand (gold star = favourite). Persisted to DB via `_toggle_hand_fav` callback + `hand-fav-id-store`.
* **Body**: Actions grouped by street (colour-coded headers), showing player username, position (e.g. `jsalinas96 (BTN)`), action type, amount, and pot size.
* **Math Column**: SPR shown on the first Flop action; Pot Odds % and MDF % shown for every decision point Hero faces.
* **Showdown Section**: ✅ Implemented — when villain hole cards are known (showdown or all-in with cards exposed), a purple "Showdown" section appears after the last street, showing each villain's name, position, and styled hole cards.
* **Breadcrumb**: `Sessions > Session Label (→ report) > Hand #N`.

---

## 📊 5. Overall Stats (The Dashboard) ✅ Implemented

A high-level overview of the Hero's performance across all time.

### A. Key Performance Indicators (KPIs) ✅
* **Total Profit/Loss**: Large focal number.
* **Win Rate**: Measured in `bb/100` (Big Blinds won per 100 hands).
* **Volume**: Total sessions and total hands played.
* **VPIP / PFR**: Shown as headline KPI cards.

### B. Positional Stats Table ✅
Breakdown of how the user plays in different seats (BTN, SB, BB, etc.).
| Position | Hands | VPIP% | PFR% | 3-Bet% | C-Bet% | AF | Net P&L |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Button | 45 | 25% | 22% | 8% | 60% | 2.50 | +$150 |
| ... | ... | ... | ... | ... | ... | ... | ... |

* **Formula Tooltips**: ✅ Implemented — VPIP%, PFR%, 3-Bet%, C-Bet%, and AF column headers each show a hoverable `?` badge that displays the formula and definition. Built via `_stat_header(label, tooltip)` in `dashboard.py`; styles in `assets/tooltips.css`.

### C. Visualizations ✅
* **Bankroll Graph**: A line chart showing cumulative profit over hands played.
* **VPIP/PFR Gap**: ✅ Implemented — stacked horizontal bar (PFR% green | Call/Limp% steel blue | Fold% gray). Placed between the bankroll graph and positional stats table. Built by `_build_vpip_pfr_chart(vpip, pfr)` in `dashboard.py`.

### D. Highlights ✅ Implemented
* Biggest single-hand win and loss (with hole cards shown as subtitle).
* Best and worst session (with date and stakes shown as subtitle).
* Displayed as a row of four cards below the positional stats table, respecting the active period filter.

### E. Time-Period Filtering ✅ Implemented
* Radio selector: **7 days**, **1 month**, **1 year**, **All time** (default).
* All KPIs, the bankroll graph, and the positional stats table are filtered
  to the selected window. Implemented via an optional `since_date` parameter
  on all five dashboard query functions.

---

## 🔄 6. Logic & State Rules
1.  **Duplicate Prevention**: The system must check Hand IDs during upload to ensure the same session isn't counted twice.
2.  **Hero Consistency**: If a user changes their username in Settings, the Dashboard must re-calculate stats based on the new ID.
3.  **Real-time Math**: SPR and MDF are pre-calculated at parse time and stored in the `Actions` table (`spr` and `mdf` columns). They are retrieved directly from the database when viewing a specific hand.