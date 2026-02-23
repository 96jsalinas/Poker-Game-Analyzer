# PokerHero Analyzer

> ⚠️ **Work in progress** — the core pipeline and UI are functional, but several features are still being built. Expect rough edges.

A local, open-source poker hand history analyzer built entirely in Python. Upload your PokerStars session files, and the app parses every hand, stores it in a local SQLite database, and surfaces your stats through an interactive web dashboard — no cloud accounts, no subscriptions, no data leaving your machine.

---

## Features

### ✅ Implemented
- **Hand history ingestion** — drag-and-drop PokerStars `.txt` files; duplicate detection prevents double-counting
- **Full drill-down review** — navigate Sessions → Hands → Actions with a breadcrumb UI; see every action, pot size, and board card
- **Real-time poker math** — SPR at flop, Pot Odds, and MDF pre-calculated at parse time and shown inline in the action view
- **EV calculation** — for all-in spots where villain cards are known (showdown hands), equity is estimated via PokerKit Monte Carlo and displayed in the action view
- **Hero highlighting** — hero's rows are visually distinct in the action table
- **Overall Stats dashboard** — KPI cards (P&L, win rate in bb/100, VPIP, PFR), bankroll graph, and a full positional stats breakdown (VPIP%, PFR%, 3-Bet%, C-Bet%, AF, Net P&L)
- **Time-period filtering** — dashboard updates for 7 days / 1 month / 1 year / All time
- **Settings page** — set hero username, clear the database, export all data to CSV
- **Card rendering** — hole cards and board cards rendered with suit symbols and colour-coding

### 🔲 Planned / In Progress
- Filter controls on session and hand table views (by date, stakes, P&L, position, etc.)
- MDF display in the action view
- Dashboard Highlights section (biggest wins/losses)
- VPIP/PFR gap chart
- EV result caching (currently computed synchronously per page load)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Database | SQLite (local file, zero-config) |
| Data manipulation | Pandas + NumPy |
| Poker engine | [PokerKit](https://github.com/uoftcprg/pokerkit) (open-source) |
| Frontend | [Dash](https://dash.plotly.com/) (Plotly) |
| Linting / formatting | Ruff |
| Type checking | mypy (strict) |
| Testing | pytest |

All dependencies are open-source.

---

## Getting Started

**Requirements:** Python 3.13+

```bash
# 1. Clone the repo
git clone https://github.com/96jsalinas/poker-game-analyzer.git
cd poker-game-analyzer

# 2. Install the package and dev dependencies
pip install -e ".[dev]"

# 3. Install pre-commit hooks (required before committing)
pre-commit install

# 4. Run the app
python run.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

---

## Usage

1. Go to **Settings** and enter your PokerStars username as the hero.
2. Go to **Upload Files** and drop your `.txt` hand history files.
3. Browse your sessions on **Review Sessions** — click a session, then a hand, to see the full action-by-action breakdown with poker math.
4. Check **Overall Stats** for aggregate performance across all your hands. Use the period selector to narrow by time window.

> **Note:** Only **PokerStars** `.txt` hand history exports are currently supported.

---

## Development

```bash
pytest                  # run all tests
ruff check --fix .      # lint
ruff format .           # format
mypy src/               # type check
```

The project follows strict TDD (red → green → refactor). See [`Contributing.MD`](Contributing.MD) for conventions, commit format, and workflow rules.

---

## Project Structure

```
src/pokerhero/
├── parser/       # Regex-based PokerStars hand history parser
├── database/     # SQLite schema + raw-SQL query layer
├── ingestion/    # File splitter + ingest pipeline
├── analysis/     # Query functions (queries.py) + stat calculations (stats.py)
└── frontend/     # Dash multi-page app (upload, sessions, dashboard, settings)
tests/            # pytest tests
data/histories/   # Your hand history files (git-ignored, local only)
```

Full architecture, data model, analysis formulas, and UX spec are documented in the `.MD` files at the repo root.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for the full text.

### What MIT means

MIT is a permissive open-source license. You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software — for any purpose, including commercially — provided the original copyright notice and license text are included in all substantial copies or distributions of the software.

MIT does **not** require derivative works to be open-source (it is not a copyleft license like GPL).

### Dependency licenses

All runtime and development dependencies use permissive open-source licenses that are fully compatible with MIT:

| Package | License | Scope |
|---|---|---|
| [PokerKit](https://github.com/uoftcprg/pokerkit) | MIT | Runtime |
| [Dash (Plotly)](https://dash.plotly.com/) | MIT | Runtime |
| [Pandas](https://pandas.pydata.org/) | BSD 3-Clause | Runtime |
| [NumPy](https://numpy.org/) | BSD 3-Clause | Runtime |
| [pytest](https://pytest.org/) | MIT | Dev only |
| [mypy](https://mypy-lang.org/) | MIT | Dev only |
| [Ruff](https://github.com/astral-sh/ruff) | MIT | Dev only |
| [pre-commit](https://pre-commit.com/) | MIT | Dev only |
| [pandas-stubs](https://github.com/pandas-dev/pandas-stubs) | BSD 3-Clause | Dev only |
| [Hatchling](https://hatch.pypa.io/) | MIT | Build tool |

**MIT and BSD 3-Clause are both permissive licenses with no copyleft restrictions.** They do not require this project to adopt a particular license, share source code, or impose any obligations beyond attribution. BSD 3-Clause adds a non-endorsement clause (you may not use the copyright holders' names to promote derived products without permission), which has no effect on this project's own MIT licensing.
