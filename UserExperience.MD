# User Experience (UX) & App Flow

This document defines the navigation structure and user interface logic for the PokerHero-Analyzer. The app follows a hierarchical "Drill-Down" approach: **Overall -> Session -> Hand -> Action.**

---

## 🗺️ 1. Main Navigation Menu
The entry point of the application.

* **[1] Upload Files**: The "Ingestion" hub.
* **[2] Review Sessions**: Historical log of all processed games.
* **[3] Overall Stats**: The "Hero Dashboard."
* **[4] Settings**: User and App configuration.

---

## ⚙️ 2. Settings
* **Hero Username**: The primary identifier used to distinguish "Hero" from "Villains" in PokerStars logs.
* **Preferred Currency**: (Optional) Toggle between USD, EUR, or Play Money.
* **Data Management**: Option to "Clear Database" or "Export Data to CSV."

---

## 📤 3. Upload Files
* **Upload Interface**: A drag-and-drop zone or file picker for `.txt` files.
* **Processing Feedback**:
    * Progress bar showing parsing status.
    * Summary of upload: *"Successfully imported 1,200 hands from 3 sessions. 4 duplicates skipped."*
* **Error Log**: If a file is corrupted or in an unsupported format, show a "Warning" log.

---

## 🔍 4. Review Sessions (The Drill-Down)

### Level 1: Session History
A table view showing all played sessions.
* **Columns**: Date, Table Name, Stakes (e.g., $0.10/$0.25), Hands Played, Net Profit/Loss.
* **Action**: Clicking a row opens the **Hand List**.

### Level 2: Hand List (Within a Session)
A detailed list of every hand dealt in that session.
* **Columns**: Hand ID, Hero Cards (Hole Cards), Final Pot, Result (Net), Biggest Action (e.g., "All-in").
* **Visual Indicator**: Green text for winning hands, red for losing hands.
* **Action**: Clicking a row opens the **Hand Replayer/Viewer**.

### Level 3: Hand Action View
A chronological breakdown of the specific hand.
* **Header**: Shows the "Board" (Flop, Turn, River) as card icons.
* **Body**: A list of all actions (e.g., "Hero raised to $5.00", "Villain called").
* **Math Sidebar**: Displays **SPR** for the flop and **Pot Odds** for every decision point the Hero faced.

---

## 📊 5. Overall Stats (The Dashboard)
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

---

## 🔄 6. Logic & State Rules
1.  **Duplicate Prevention**: The system must check Hand IDs during upload to ensure the same session isn't counted twice.
2.  **Hero Consistency**: If a user changes their username in Settings, the Dashboard must re-calculate stats based on the new ID.
3.  **Real-time Math**: SPR and MDF are pre-calculated at parse time and stored in the `Actions` table (`spr` and `mdf` columns). They are retrieved directly from the database when viewing a specific hand.