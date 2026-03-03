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
* **Analysis Settings**: Configurable equity sample count, lucky/unlucky equity thresholds, and minimum hands for archetype classification. Stored in the `settings` table.
* **Target Stats**: Position-specific VPIP / PFR / 3-Bet range targets with a traffic-light system (green / yellow / red zones). Configured on a dedicated sub-page at `/settings/targets` (linked from the main settings page). Stored in the `target_settings` table (not the key-value `settings` table).
* **Data Management**: "Clear Database" deletes all hands/sessions/actions/players (settings preserved). "Export Data to CSV" downloads sessions + hands as `pokerhero_export.csv`.

## 🌙 Dark Mode ✅ Implemented
* A **fixed 🌚 / 🌞 toggle button** sits in the top-right corner of every page (position: fixed, z-index 9999) and is always accessible regardless of scroll position.
* The preference is persisted in a `dcc.Store(storage_type="local")` keyed `theme-store`, so it survives page navigation and browser restarts.
* Toggling adds / removes the `dark` class on `document.body` via a clientside callback, enabling CSS-variable-based dark overrides defined in `assets/theme.css`.
* CSS custom properties (`--bg-1`, `--bg-2`, `--text-1..4`, `--border`, `--border-light`) are used throughout all page files as inline-style `var()` references with light-mode fallbacks, so light mode is pixel-identical to the original design.
* **P&L color vars**: `--pnl-positive` / `--pnl-negative` — light defaults: `green`/`red`; dark overrides: `#2ecc71` / `#e74c3c` (bright enough to read on a dark surface). Used in `_pnl_style()`, `_build_session_kpi_strip`, and the dashboard KPI / positional stats / highlight cards.
* **Hero action-row var**: `--bg-hero-row` — light: `#edf5ff`; dark: `#1e2a4a` (navy). Used in `_action_row_style()` in `sessions.py`.
* **Traffic-light vars**: `--tl-green`, `--tl-yellow`, `--tl-red` — light: standard Bootstrap pastels (`#d4edda`, `#fff3cd`, `#f8d7da`); dark: deep saturated tones (`#1a3a2a`, `#3a3010`, `#3a1a1a`). Used in `_TL_COLORS` dicts in both `sessions.py` and `dashboard.py`.
* **Plotly charts**: `_build_vpip_pfr_chart` and the bankroll graph both accept a `theme` parameter (fed from `theme-store`) and set `plot_bgcolor`/`paper_bgcolor` to `#1a1a2e` in dark mode.
* **Dash 4 design tokens**: All Dash 4 form components (Input, Dropdown, DatePicker, Slider) are themed via `--Dash-Fill-Inverse-Strong`, `--Dash-Stroke-Strong`, `--Dash-Text-Primary`, etc., overridden in `body.dark`.
* **`color-scheme: dark`**: Applied to `input, select, textarea` in dark mode so the browser renders native controls (number spinners, checkboxes, scrollbars) with its built-in dark palette.
* **Icon convention**: 🌚 = currently light mode (click to go dark); 🌞 = currently dark mode (click to go light).

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
* **Position Breakdown Table** ✅ Implemented — compact per-position VPIP% / PFR% / Net P&L table with traffic-light background colouring (same green/yellow/red palette as the dashboard). Positions with no hands are omitted. Built by `_build_session_position_table(kpis_df, conn)` in `sessions.py`.
* **EV Summary** — equity-based luck indicator. For each **all-in hand** where villain cards were revealed, uses the precomputed `allin_exact` EV from `action_ev_cache`. Lucky: hero won with equity < 0.4. Unlucky: hero lost with equity > 0.6. Verdict: `👍 Ran above equity` / `👎 Ran below equity` / `~ Ran near equity`. Data comes from `get_session_allin_evs`. Built by `_build_ev_summary(ev_df)`.
* **Notable Hands** — lists each all-in hand classified as 🍀 Lucky or 😞 Unlucky with the equity percentage at the all-in moment. Each entry is a clickable link that navigates to the hand action view (`/sessions?session_id=X&hand_id=Y`). Built by `_build_flagged_hands_list(ev_df, session_id=session_id)`.
* **Browse all N hands button** (`session-report-browse-btn`) — navigates to the Hand List for this session via `_browse_session_hands` callback.
* State: `level="report"`, `session_id=X`.

### Level 3: Hand List (Within a Session) ✅
A detailed list of every hand dealt in that session.
* **Columns**: Hand ID, Hero Cards (Hole Cards with suit symbols), Final Pot, Net Result.
* **Sorting** ✅ Implemented — click any column header to sort ascending/descending.
* **Action**: Clicking any cell in a row navigates to the **Hand Action View**.
* **Filters** ✅ Implemented — filter bar: P&L min/max, position multiselect, Saw Flop checkbox, Showdown checkbox, Favourites only, EV quality multiselect (bad_call/good_call/bad_fold, OR logic, uses `has_bad_call`/`has_good_call`/`has_bad_fold` columns from `get_hands`). Updates table without page reload via `_apply_hand_filters` callback + `hand-data-store`.
* **Breadcrumb**: `Sessions > Session Label (→ report) > All Hands`.

### Level 4: Hand Action View ✅
A chronological breakdown of the specific hand.
* **Header**: Hand # and board cards (Flop | Turn | River).
* **Favourite** ✅ Implemented — ★/☆ button in the top-right of the action view header; clicking toggles `is_favorite` on the current hand (gold star = favourite). Persisted to DB via `_toggle_hand_fav` callback + `hand-fav-id-store`.
* **Body**: Actions grouped by street (colour-coded headers with board cards inline — FLOP shows the three flop cards, TURN shows the turn card, RIVER shows the river card), showing player username, position (e.g. `jsalinas96 (BTN)`), action type, amount, and pot size.
* **Math Column**: SPR shown on the first Flop action; Pot Odds % and MDF % shown for every decision point Hero faces.
* **Showdown Section**: ✅ Implemented — when villain hole cards are known (showdown or all-in with cards exposed), a purple "Showdown" section appears after the last street, showing each villain's name, position, and styled hole cards.
* **Breadcrumb**: `Sessions > Session Label (→ report) > All Hands (→ hand list) > Hand #N`.

---

## 📊 5. Overall Stats (The Dashboard) ✅ Implemented

A high-level overview of the Hero's performance across all time.

### A. Key Performance Indicators (KPIs) ✅
* **Total Profit/Loss**: Large focal number.
* **Win Rate**: Measured in `bb/100` (Big Blinds won per 100 hands).
* **Volume**: Total sessions and total hands played.
* **VPIP / PFR / 3-Bet**: Shown as headline KPI cards (no target display on the cards themselves).

### B. Positional Stats Table ✅
Breakdown of how the user plays in different seats (BTN, SB, BB, etc.).
| Position | Hands | VPIP% | PFR% | 3-Bet% | C-Bet% | AF | Net P&L |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Button | 45 | 25% | 22% | 8% | 60% | 2.50 | +$150 |
| ... | ... | ... | ... | ... | ... | ... | ... |

* **Formula Tooltips**: ✅ Implemented — VPIP%, PFR%, 3-Bet%, C-Bet%, and AF column headers each show a hoverable `?` badge that displays the formula and definition. Built via `_stat_header(label, tooltip)` in `dashboard.py`; styles in `assets/tooltips.css`.
* **Traffic Light Colouring**: ✅ Implemented — VPIP%, PFR%, and 3-Bet% cells are shaded green / yellow / red based on the user's configured target ranges for each position. Uses `traffic_light()` from `pokerhero.analysis.targets` with per-position `TargetBounds` loaded via `read_target_settings(conn)`. Color mapping: green `#d4edda`, yellow `#fff3cd`, red `#f8d7da`.

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