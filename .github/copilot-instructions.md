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
