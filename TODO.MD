# TODO

## ✅ Completed

### Logging
Structured logging added via `logging.getLogger(__name__)` in `pipeline.py`, `upload_handler.py`, and `db.py`. `setup_logging()` (defined in `config.py`) activates a console handler at startup.

### Session Financials Bug (was: sessions.net_result is always 0.0)
`sessions.hero_buy_in` and `sessions.hero_cash_out` were always `NULL`. Fixed in `ingest_file()`: hero `starting_stack` from the first hand is `hero_buy_in`; `starting_stack + net_result` from the last hand is `hero_cash_out`. `update_session_financials()` DB function updates the row after all hands are processed.

### Re-buy Detection
`hero_buy_in` now accumulates the initial buy-in **plus all re-buys**. A re-buy is detected when hero's `starting_stack` at hand N exceeds `starting_stack + net_result` from hand N-1. The delta is added to `hero_buy_in`.

### Multi-Page UI
Full Dash multi-page app with:
- `/` — Navigation hub
- `/upload` — File ingestion with hero username persisted to `settings` table
- `/sessions` — Full 3-level drill-down: Session list → Hand list → Hand action view with breadcrumb navigation, player usernames/positions, SPR and pot odds

### Hand View — Card Display & Hero Highlighting
- Hero hole cards shown as styled card chips (rank + suit symbol ♠♥♦♣) in both the hand list and the action view header
- Board cards (flop | turn | river) displayed as card chips with street separators
- Hero action rows highlighted with a light-blue background and left accent border for instant visual identification
- Pure HTML/CSS implementation — no external icon libraries, fully open-source

### Dashboard Page (`/dashboard`)
- KPI cards: total P&L, win rate bb/100, sessions count, hands count, VPIP%, PFR%
- Bankroll graph: cumulative profit over time (Plotly line chart)
- Positional stats table: VPIP/PFR/AF/Net per position

---
### Settings Page (`/settings`)
- Hero username input (reads/saves from settings table; Upload page retains it for convenience)
- Clear Database button (deletes all hands/sessions/actions/players; settings preserved)
- Export to CSV button (downloads sessions + hands as `pokerhero_export.csv`)

---
## 🔲 Deferred Analysis Features
- **3-Bet%** — requires action sequence traversal (detect raise-over-raise preflop)
- **C-Bet%** — requires last-aggressor tracking per street
- **EV** — requires PokerKit equity calculation at showdown/all-in spots
