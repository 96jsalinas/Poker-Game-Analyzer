# User Experience (UX) & App Flow

This document defines the navigation structure and user interface logic for the PokerHero-Analyzer. The app follows a hierarchical "Drill-Down" approach: **Overall -> Session -> Hand -> Action.**

---

## 🗺️ 1. Main Navigation Menu
The entry point of the application (`/`). Currently a simple hub page.

* **[1] Upload Files** (`/upload`): The "Ingestion" hub. ✅ Implemented.
* **[2] Review Sessions** (`/sessions`): Historical log of all processed games. ✅ Implemented.
* **[3] Overall Stats** (`/dashboard`): The "Hero Dashboard." ✅ Implemented.
* **[4] Settings** (`/settings`): User and App configuration. ✅ Implemented.

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
Sessions  →  Sessions › 2026-02-16 250/500  →  Sessions › 2026-02-16 250/500 › Hand #2597...
```

### Level 1: Session History ✅
A table view showing all played sessions.
* **Columns**: Date, Stakes (e.g., 100/200), Hands Played, Net Profit/Loss (green/red).
* **Action**: Clicking a row navigates to the **Hand List** for that session.

### Level 2: Hand List (Within a Session) ✅
A detailed list of every hand dealt in that session.
* **Columns**: Hand ID, Hero Cards (Hole Cards), Final Pot, Net Result (green/red).
* **Action**: Clicking a row navigates to the **Hand Action View**.

### Level 3: Hand Action View ✅
A chronological breakdown of the specific hand.
* **Header**: Hand # and board cards (Flop | Turn | River).
* **Body**: Actions grouped by street (colour-coded headers), showing player username, position (e.g. `jsalinas96 (BTN)`), action type, amount, and pot size.
* **Math Column**: SPR shown on the first Flop action; Pot Odds % shown for every decision point Hero faces.

---

## 📊 5. Overall Stats (The Dashboard) 🔲 Planned

A high-level overview of the Hero's performance across all time.

### A. Key Performance Indicators (KPIs)
* **Total Profit/Loss**: Large focal number.
* **Win Rate**: Measured in `bb/100` (Big Blinds won per 100 hands).
* **Volume**: Total sessions and total hands played.
* **Filtering**: Allow's user to define time period for which stats apply (7 days, 1 month, 1 year, all-time, custom)

### B. Positional Stats Table
Breakdown of how the user plays in different seats (BTN, SB, BB, etc.).
| Position | VPIP% | PFR% | 3-Bet% | Net Profit |
| :--- | :--- | :--- | :--- | :--- |
| Button | 25% | 22% | 8% | +$150.00 |
| ... | ... | ... | ... | ... |

### C. Visualizations
* **Bankroll Graph**: A line chart showing cumulative profit over time/hands.
* **VPIP/PFR Gap**: A gauge chart showing the relationship between playing and raising.

### D. Highlights
* Shows biggest hands in user history, biggest blunders or wins.

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