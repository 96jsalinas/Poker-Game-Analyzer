# Copilot Instructions: PokerHero-Analyzer

## Documentation

All design decisions, conventions, and formulas are documented in the `.MD` files at the repository root. Read the relevant file before working on any area:

| File | covers |
|------|--------|
| `Architecture.MD` | Tech stack, data flow pipeline, current directory structure |
| `DataStructure.MD` | SQLite schema, Python dataclass models, and DB field mappings |
| `AnalysisLogic.MD` | Source-of-truth math formulas (EV, SPR, MDF, Pot Odds, VPIP, PFR, AF, etc.) and data processing rules |
| `TestingStrategy.MD` | TDD policy, testing pyramid, fixture file inventory, tooling |
| `Contributing.MD` | Toolchain commands, `src/` layout, type hint rules, naming conventions, docstring style, commit protocol |
| `UserExperience.MD` | UI navigation structure, drill-down flow, dashboard KPIs, state/logic rules |

## Workflow Rules

- After implementing each agreed change, stage all affected files and commit before moving on to the next change. Keep commits small and focused — one logical change per commit. If a task naturally produces multiple independent changes (e.g. fixtures and tests), split them into separate commits.
- **TDD commit order is mandatory**: always make two separate commits per feature/fix — first a `test(...)` commit containing only the new failing tests, then a `feat(...)` or `fix(...)` commit containing the implementation (plus any doc updates). Never combine failing tests and their implementation in the same commit. Look at the git log to confirm the pattern before committing.
- After any implementation change, check whether the relevant `.MD` files need updating to stay in sync (e.g. `Architecture.MD` when adding/completing a module, `DataStructure.MD` when changing models or DB schema, `TestingStrategy.MD` when adding fixtures). If so, include the `.MD` update in the same commit as the code change.
- If a requested code change contradicts any rule, convention, or formula defined in the `.MD` files, stop and flag the contradiction to the user before proceeding. Once confirmed, update the relevant `.MD` file first, then implement the code change.
- If a task is too large or complex to be implemented reliably in a single step, break it into smaller sub-tasks, present the breakdown to the user, and implement each sub-task individually with its own commit. Each sub-task must be fully implemented, tested, and committed before starting the next one. Good sub-task boundaries include: per test class, per module, or per logical feature (e.g. parsing one street type). Never implement more than one sub-task in a single agent call.

## Commands

```bash
ruff check --fix .   # lint
ruff format .        # format
mypy src/            # type check
pytest               # all tests
pytest tests/path/to/test_file.py::test_function_name  # single test
pre-commit install   # required once before first commit
```

## Ruff Scope Rule

`ruff check --fix` and `ruff format` run project-wide and will reformat files you didn't touch. Always:
- Stage and commit formatting changes **together** with the feature/fix in the same commit — never as a separate commit.
- If there are unrelated uncommitted changes in the working tree, scope the commands to only your changed files (e.g. `ruff format src/pokerhero/ingestion/ tests/test_ingestion.py`) to avoid picking up unrelated diffs.

## Lessons Learned

### Never force-add gitignored files
`TODO.MD` is listed in `.gitignore` and must stay local-only. **Never** use `git add -f` on any gitignored file. If a file is gitignored, that is intentional. The only recovery from an accidental force-add is `git reset HEAD~1` (soft reset) if the commit hasn't been pushed yet. If it has been pushed, a force-push is required and disruptive for collaborators.

### Fixture files must mirror the actual file format exactly
When adding a test fixture for a new hand history variant (e.g. EUR cash game), the fixture **must** use the real PokerStars format throughout — including `€` prefixes on every monetary value in the body, not just the header. A fixture that only tests the header regex but uses simplified amounts in the body will pass parser tests while masking ingestion failures for real files. Write fixtures that match a real copy-paste snippet as closely as possible.

### Decimal-aware display formatting for monetary values
`int()` or `:.0f` formatting truncates micro-stake values (e.g. `int(0.02) == 0`). Any display code that renders blind sizes, pot sizes, or P&L values must use decimal-aware helpers:
- `_fmt_blind(v)`: `f"{float(v):g}"` — strips trailing zeros, no scientific notation for normal stake ranges.
- `_fmt_pnl(pnl)`: `f"{sign}{pnl:,.6g}"` — signed, comma-separated, 6 significant figures.
- Plotly hovertemplate uses d3-format, not Python format — use `%{y:,.4g}` not `%{y:,.0f}`.
These helpers are duplicated across `dashboard.py` and `sessions.py` — cross-page imports between Dash page modules are unclean, duplication is intentional for trivial one-liners.

### `hole_cards IS NOT NULL` does not mean the hero reached showdown
PokerStars records the hero's hole cards in the hand history regardless of whether they folded. When querying for hands where the hero actually went to showdown, always filter on `hero_hp.went_to_showdown = 1` — never rely on `hole_cards IS NOT NULL` alone as a showdown proxy for the hero's row.

### SQL JOINs on hand_players produce one row per matching player, not per hand
A query that JOINs `hand_players` looking for opponents with known cards will return N rows for any hand with N such opponents (multiway showdowns). Always add a deduplication strategy — either a correlated subquery (`villain_hp.player_id = (SELECT MIN(...) ...)`) to pick one representative villain, or a `GROUP BY h.id` with explicit aggregation. Failing to do this causes the same hand to appear multiple times in result sets.

### TDD commits must be split: test commit first, then implementation commit
The project history follows a strict two-commit pattern per feature/fix: a `test(scope): ...` commit containing only the new failing tests, followed by a `feat(scope): ...` or `fix(scope): ...` commit containing the implementation and doc updates. Never bundle tests and their implementation in the same commit — the red-state snapshot in git is intentional and allows reviewers to verify the tests were truly failing before the fix.

### Split test files when they grow too large
When a test file exceeds ~20 classes or ~1,000 lines, split it along page/feature boundaries. The naming convention mirrors the source: `test_{page}.py` for `pages/{page}.py`, `test_analysis.py` for `analysis/`. Shared fixtures (e.g. the `db` fixture) should be duplicated into each new file that needs them — do not create a shared `conftest.py` unless the duplication becomes unmanageable. `TestingStrategy.MD` must be updated in the same commit as the split to reflect the new file inventory.
