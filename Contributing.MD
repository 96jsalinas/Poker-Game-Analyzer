# Contributing & Style Guide: PokerHero-Analyzer

To ensure the PokerHero-Analyzer remains maintainable, bug-free, and easy to scale, this repository strictly adheres to modern Python development standards. We prioritize readability, explicit type definitions, and automated code quality checks.

## 🛠️ 1. The Toolchain

We use a consolidated, modern toolchain. All developers must ensure their code passes these checks before submitting a Pull Request.

* **Formatting & Linting:** [Ruff](https://docs.astral.sh/ruff/)
    * *Why:* Ruff is a highly performant Rust-based tool that replaces Black, Flake8, isort, and pyupgrade. It enforces consistent PEP-8 styling automatically.
    * *Command:* Run `ruff check --fix .` and `ruff format .` before committing.
* **Static Type Checking:** [Mypy](https://mypy.readthedocs.io/)
    * *Why:* Poker math requires absolute certainty about data types (e.g., distinguishing a `Decimal` from a `float`).
    * *Command:* Run `mypy src/` to verify type safety.

## 📐 2. Repository Structure

We use the `src/` layout pattern to prevent import errors and ensure the package is tested exactly as it would be installed in production.

```text
pokerhero-analyzer/
├── src/
│   └── pokerhero/
│       ├── __init__.py
│       ├── parser/
│       ├── analysis/
│       ├── database/
│       └── frontend/     # (TBD) Dash
├── tests/
│   └── fixtures/
├── data/
├── pyproject.toml
└── README.md

```

## ✍️ 3. Type Hinting (Mandatory)

Every function signature and class variable must be explicitly typed. We do not rely on implicit dynamic typing for the core logic.

**❌ Bad:**

```python
def calculate_pot_odds(amount_to_call, pot_size):
    return amount_to_call / (pot_size + amount_to_call)

```

**✅ Good:**

```python
from decimal import Decimal

def calculate_pot_odds(amount_to_call: Decimal, pot_size: Decimal) -> float:
    return float(amount_to_call / (pot_size + amount_to_call))

```

### 3a. No `Any` — Use `TypedDict` for heterogeneous dicts

**`typing.Any` is banned.** It silences mypy without providing safety, defeating the purpose of static typing entirely.

When an internal function passes around a dict with a fixed set of keys of different types, define a `TypedDict` instead:

**❌ Bad:**
```python
from typing import Any

def _build_action(...) -> dict[str, Any]:
    return {"seq": 1, "amount": Decimal("100"), "is_all_in": False}
```

**✅ Good:**
```python
from typing import TypedDict
from decimal import Decimal

class _RawAction(TypedDict):
    seq: int
    amount: Decimal
    is_all_in: bool

def _build_action(...) -> _RawAction:
    return {"seq": 1, "amount": Decimal("100"), "is_all_in": False}
```

> **Convention:** Internal `TypedDict` classes used only within a single module are prefixed with `_` (e.g. `_RawAction`, `_SeatInfo`). Public `TypedDict` classes exported from a module use `PascalCase` without a prefix.

## 📝 4. Naming Conventions

We follow strict PEP-8 naming conventions:

* **Classes:** `PascalCase` (e.g., `HandParser`, `SessionAnalyzer`)
* **Functions & Variables:** `snake_case` (e.g., `calculate_ev`, `pot_size`)
* **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_SEATS`, `DEFAULT_CURRENCY`)
* **Private Methods:** Prefix with an underscore (e.g., `_parse_header_line()`)

## 📖 5. Docstrings

We use **Google-style** docstrings. Every public function must have a docstring explaining its mathematical logic if applicable.

**Example:**

```python
def calculate_mdf(pot_size: Decimal, bet_size: Decimal) -> float:
    """
    Calculates the Minimum Defense Frequency (MDF).

    MDF is the percentage of the time a player must call a bet to 
    prevent the bettor from profiting purely by bluffing.

    Args:
        pot_size (Decimal): The size of the pot before the bet.
        bet_size (Decimal): The size of the bet facing the hero.

    Returns:
        float: The minimum defense frequency as a decimal (0.0 to 1.0).
    """
    return float(pot_size / (pot_size + bet_size))
```

## 🚨 6. Git & Commit Protocol

* **Pre-commit Hooks:** You must install the repository's pre-commit hooks (`pre-commit install`). This will automatically run Ruff and Mypy on your code when you commit. If they fail, the commit is aborted.
* **Commit Messages:** Use the **Conventional Commits** format with imperative mood:
  ```
  <type>(<scope>): <short description>
  ```
  | Type | When to use |
  | :--- | :--- |
  | `feat` | New feature or function |
  | `fix` | Bug fix |
  | `test` | Adding or updating tests |
  | `docs` | Documentation changes only |
  | `chore` | Config, tooling, rules, non-code changes |
  | `refactor` | Code restructuring with no behaviour change |

  Examples: `feat(parser): add uncalled bet handling`, `fix(database): correct hero net_result calculation`, `test(database): add TestSessionInsert class`
* **Testing:** All new features or bug fixes must follow the **red-green-refactor** order: write and commit the failing test(s) first (`test` commit type), then implement the code to make them pass (`feat` or `fix` commit). Never write implementation code before the test exists and has been confirmed to fail.
* **Document discoveries immediately:** Any non-obvious finding made during implementation — format quirks, edge cases, data assumptions, design decisions, known limitations — must be recorded in the appropriate `.MD` file in the same commit as the code that handles it. The right file to use:

  | Discovery type | Document in |
  | :--- | :--- |
  | Input data format / encoding quirks | `Architecture.MD` |
  | Schema decisions or field type rationale | `DataStructure.MD` |
  | Formula definitions or math edge cases | `AnalysisLogic.MD` |
  | New fixtures or testing edge cases | `TestingStrategy.MD` |
  | Style, type, or tooling rules | `Contributing.MD` |
