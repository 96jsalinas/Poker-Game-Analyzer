# PokerHero Analyzer

> 🚀 **Ready for feedback** — the core pipeline, stats dashboard, session review, and EV analysis engine are fully functional. Looking for testers to provide feedback on accuracy and UX.

A local, open-source poker hand history analyzer built entirely in Python. Upload your PokerStars session files, and the app parses every hand, stores it in a local SQLite database, and surfaces your stats through an interactive web dashboard — no cloud accounts, no subscriptions, no data leaving your machine.

---

## ⚠️ Limitations & Disclaimers

- **PokerStars Only:** The parser is built exclusively for PokerStars `.txt` hand history files. Ingestion of files from other poker sites is not supported.
- **Cash games:** While the app can ingest tournament files, it has been predominantly developed and tested with cash game data. Tournament-specific features and calculations may be less reliable. Contributions to improve tournament support are welcome.
- **Data Integrity:** This is a local-only application. While there is no risk of data being leaked, it is strongly recommended to back up your original `.txt` hand history files. Future updates or unforeseen bugs could potentially corrupt the local database.

---

## Features

**Hand ingestion & parsing**
- Drag-and-drop PokerStars `.txt` hand history files; duplicate detection prevents double-counting
- Supports **USD**, **EUR**, and **Play Money** sessions; currency is auto-detected per file
- Supports **Cash** and **Tournament** game types; includes automatic **re-buy detection**

**Session drill-down review**
- **Session Report** — narrative summary, KPI strip (bb/100, VPIP, AF), and position-specific stat tables
- **EV Analysis** — calculate EV for entire sessions; highlights 🍀 Lucky and 😞 Unlucky all-in hands based on exact equity at the moment of the all-in vs actual result
- Navigate Sessions → Hands → Actions with a breadcrumb UI
- Filter hands by position, P&L, showdown, Favourites, and **EV quality** (bad call / good call / bad fold); **filters persist** when navigating back from the action view to the hand list

**Action view (Hand Detail)**
- Full street-by-street replay with every action, amount, running pot, and board cards
- **Poker math inline** — SPR at flop, Pot Odds%, and MDF% shown at every hero decision point
- **EV calculation** — **Range-based EV** (estimated vs inferred villain range, always shown in the action table for decision review) and **All-in Exact EV** (against revealed villain cards at the moment of the all-in, used for the Lucky/Unlucky variance summary only)
- **Fold Verdicts** — tells you if a fold was mathematically correct (✓ Good fold) or a mistake (⚠ Should have called)

**Opponent profiling**
- Every opponent is automatically classified as **TAG**, **LAG**, **Nit**, or **Fish** based on their VPIP and aggression ratio
- **Confidence Tiers** — badges reflect sample size (Preliminary, Standard, or Confirmed ✓)
- Profile cards for all opponents accessible via a toggle panel in the hand list

**Overall Stats dashboard**
- KPI cards: P&L, win rate (bb/100), VPIP, PFR, 3-Bet
- **Bankroll graph** (cumulative P&L over time) and **VPIP/PFR Gap chart**
- **Traffic Light Targets** — positional stats shaded green/yellow/red based on your custom target ranges
- Dashboard Highlights: biggest single-hand win/loss and best/worst session
- Period filter (7 days / 1 year / All time) and currency toggle

**App**
- **Dark Mode** — system-wide 🌚/🌞 toggle with persistent user preference
- In-app guide explaining every feature, stat formula, and opponent archetype
- Settings page: set hero username, configure EV thresholds, clear database, and **Export to CSV**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Database | SQLite (local file, zero-config) |
| Data manipulation | Pandas + NumPy |
| Poker engine | [PokerKit](https://github.com/uoftcprg/pokerkit) (open-source) |
| Frontend | [Dash](https://dash.plotly.com/) (Plotly) |
| Style | CSS Variables + Dark Mode support |
| Tooling | Ruff, mypy (strict), pytest |

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
3. Browse your sessions on **Review Sessions** — use the **📊 Calculate EVs** button on any session report to run the analysis engine.
4. Check **Overall Stats** for aggregate performance and positional targets.
5. Open the **Guide** page (❓) for an explanation of every stat formula and opponent archetype.


---

## Development

```bash
pytest                  # run all tests
ruff check --fix .      # lint
ruff format .           # format
mypy src/               # type check
```

The project follows strict TDD (red → green → refactor). See [`Contributing.MD`](Contributing.MD) for conventions and workflow.

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
| [diskcache](https://github.com/grantjenks/python-diskcache) | Apache 2.0 | Runtime |
| [pytest](https://pytest.org/) | MIT | Dev only |
| [mypy](https://mypy-lang.org/) | MIT | Dev only |
| [Ruff](https://github.com/astral-sh/ruff) | MIT | Dev only |
| [pre-commit](https://pre-commit.com/) | MIT | Dev only |
| [pandas-stubs](https://github.com/pandas-dev/pandas-stubs) | BSD 3-Clause | Dev only |
| [Hatchling](https://hatch.pypa.io/) | MIT | Build tool |

**MIT, BSD 3-Clause, and Apache 2.0 are all permissive licenses with no copyleft restrictions.** They do not require this project to adopt a particular license, share source code, or impose any obligations beyond attribution. BSD 3-Clause adds a non-endorsement clause (you may not use the copyright holders' names to promote derived products without permission), which has no effect on this project's own MIT licensing. Apache 2.0 additionally includes an explicit patent grant from contributors, also with no impact on this project's MIT license.
