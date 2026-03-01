# Audit Findings & Remediation Plan

**Date**: 2026-03-01
**Scope**: Full codebase audit — parser, analysis, database, frontend, ingestion, config, tests, documentation.
**Baseline**: 786 passing tests, all pre-commit hooks green (ruff, mypy).

---

## Findings Summary

| ID  | Severity | Area       | Title                                       |
|-----|----------|------------|---------------------------------------------|
| H1  | HIGH     | Config     | `debug=True` in production entry point      |
| H2  | HIGH     | Database   | Missing indexes on `actions` table          |
| H3  | HIGH     | Frontend   | N+1 query in session list rendering         |
| H4  | HIGH     | Ingestion  | UTF-8 BOM breaks hand detection             |
| M1  | MEDIUM   | Frontend   | Unsafe base64 data-URI split                |
| M2  | MEDIUM   | Frontend   | `_fmt_pnl` can produce scientific notation  |
| M3  | MEDIUM   | Ingestion  | Orphaned session on first-hand-parse failure|
| M4  | MEDIUM   | Ingestion  | CRLF line endings may affect parsing        |
| M5  | MEDIUM   | Ingestion  | IntegrityError misclassification            |
| M6  | MEDIUM   | Config     | Hardcoded relative cache path               |
| M7  | MEDIUM   | Frontend   | Settings callbacks lack server-side validation |
| M8  | MEDIUM   | Analysis   | Straight draw loop bounds are sloppy        |
| L1  | LOW      | Parser     | `[\d.]+` regex accepts malformed decimals   |
| L2  | LOW      | Database   | Dead code: hand_equity shims                |
| L3  | LOW      | Ingestion  | First block parsed twice                    |
| L4  | LOW      | Frontend   | Percentage display inconsistency            |
| L5  | LOW      | Analysis   | SQL `.format()` for IN clause               |
| L6  | LOW      | Frontend   | Overly broad `except Exception` in upload   |
| L7  | LOW      | Ingestion  | Empty file ingestion is silent              |

---

## Detailed Findings

### H1. `debug=True` in production entry point

- **File**: `run.py:23`
- **Impact**: Werkzeug debugger is enabled, exposing an interactive Python shell to anyone with network access. Also enables hot-reload and verbose tracebacks.

```python
app.run(debug=True)  # Should be env-controlled
```

**Fix**: Read a `POKERHERO_DEBUG` environment variable:

```python
app.run(debug=os.environ.get("POKERHERO_DEBUG", "").lower() == "true")
```

---

### H2. Missing indexes on `actions` table

- **File**: `schema.sql:50-64`
- **Impact**: Queries that filter/join on `hand_id`, `player_id`, or `(hand_id, sequence)` perform full table scans. Performance degrades significantly with 10 k+ hands.

**Fix**: Add indexes after the `CREATE TABLE`:

```sql
CREATE INDEX IF NOT EXISTS idx_actions_hand_id ON actions(hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_player_id ON actions(player_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand_sequence ON actions(hand_id, sequence);
```

---

### H3. N+1 query in session list rendering

- **File**: `sessions.py:1472-1475`
- **Impact**: `_ev_status_label(conn, session_id)` is called once per session row via `iterrows()`. With 100 sessions this means 100 separate DB queries on every page load.

```python
df["ev_status"] = [
    _ev_status_label(conn, int(row["id"])) for _, row in df.iterrows()
]
```

**Fix**: Replace the per-row call with a single batch query using `WHERE session_id IN (...)` and merge into the DataFrame.

---

### H4. UTF-8 BOM breaks hand detection

- **File**: `pipeline.py:59`
- **Impact**: Files saved with UTF-8 BOM (e.g. from Windows Notepad) have a `\ufeff` prefix. The splitter regex `(?=PokerStars Hand #)` won't match the first hand because it starts with `\ufeffPokerStars Hand #`.

```python
blocks = split_hands(path.read_text(encoding="utf-8"))
```

**Fix**: Use `encoding="utf-8-sig"` which auto-strips the BOM.

---

### M1. Unsafe base64 data-URI split

- **File**: `upload_handler.py:37`
- **Impact**: If `content_string` doesn't contain a comma (malformed upload), the tuple unpacking raises an unhandled `ValueError`.

```python
_header, b64_data = content_string.split(",", 1)
```

**Fix**: Add a guard before the split:

```python
if "," not in content_string:
    raise ValueError("Invalid data URI format")
```

---

### M2. `_fmt_pnl` can produce scientific notation

- **Files**: `dashboard.py:126`, `sessions.py:436`
- **Impact**: The `:,.6g` format spec produces `1e-06` for very small values and rounds large values unexpectedly. Poker P&L should never display in scientific notation.

```python
return f"{sign}{pnl:,.6g}"
```

**Fix**: Use `:,.2f` for standard currency display, or clamp `g` precision higher. The current behaviour is acceptable for typical micro/small/mid-stakes but could surprise users at extremes.

---

### M3. Orphaned session on first-hand-parse failure

- **File**: `pipeline.py:75-80`
- **Impact**: Session row is inserted and committed *before* the first hand is successfully saved to the DB (line 87-91). If `save_parsed_hand` fails on the first hand, the session exists with zero hands.

**Fix**: Defer the `conn.commit()` on line 80 until after the first hand is successfully inserted, or clean up the session if no hands are ingested.

---

### M4. CRLF line endings may affect parsing

- **File**: `splitter.py:19`
- **Impact**: The regex `(?=PokerStars Hand #)` assumes Unix line endings. Files with `\r\n` (common on Windows) split correctly, but `\r` characters may propagate into parsed values if the rest of the parser doesn't strip them. Low likelihood with genuine PokerStars output but possible with user-edited files.

**Fix**: Normalize line endings at the top of `split_hands()`:

```python
text = text.replace("\r\n", "\n").replace("\r", "\n")
```

---

### M5. IntegrityError misclassification

- **File**: `pipeline.py:106-109`
- **Impact**: Any `sqlite3.IntegrityError` — not just a duplicate `source_hand_id` — is counted as a "skipped duplicate." A foreign-key violation or CHECK-constraint failure would be silently mis-categorised.

**Fix**: Inspect the error message string (e.g. `"UNIQUE constraint failed: hands.source_hand_id"`) to distinguish true duplicates from other integrity failures.

---

### M6. Hardcoded relative cache path

- **File**: `run.py:20`
- **Impact**: `diskcache.Cache("./cache")` creates the cache directory relative to CWD. If the app is launched from a different directory, the cache lands in an unexpected location.

```python
cache = diskcache.Cache("./cache")
```

**Fix**: Derive from `DB_PATH.parent / "cache"` or use a fixed project-root-relative path.

---

### M7. Settings callbacks lack server-side validation

- **File**: `settings.py:487-568`
- **Impact**: Analysis settings (thresholds, percentages) are saved without range validation. A user who bypasses frontend input constraints (browser dev tools) can persist out-of-range values.

**Fix**: Add range checks before writing to DB, e.g.:

```python
if value is None or not (10 <= value <= 49):
    return "⚠️ Value out of range"
```

---

### M8. Straight draw loop bounds are sloppy

- **File**: `ranges.py:455, 469`
- **Impact**: `range(14)` on line 455 produces windows with indices up to 16, and `range(13)` on line 469 produces windows up to 16. Indices beyond 13 never appear in `all_ranks`, so the extra iterations are harmless no-ops — the code is *correct* — but tighter bounds would be cleaner and prevent future confusion.

**Fix**: OESD loop → `range(11)` (max window `{10,11,12,13}`). Gutshot loop → `range(10)` (max window `{10,11,12,13,14}` — 14 is needed for ace-low).

---

### L1. `[\d.]+` regex accepts malformed decimals

- **File**: `hand_parser.py` (lines 64, 73, 75, 77, 79, 81, 84, 86, 88)
- **Impact**: Patterns like `[\d.]+` would match `1.2.3` which would then fail at `Decimal()` conversion. Practically zero risk since PokerStars output is well-formed, but a stricter pattern like `\d+(?:\.\d+)?` would be more precise.

---

### L2. Dead code: hand_equity shims

- **File**: `db.py:355-376`
- **Impact**: Intentional no-op shims (`get_hand_equity`, `set_hand_equity`) for the deprecated `hand_equity` table. Safe to keep for backward compatibility but could be removed in a cleanup pass.

---

### L3. First block parsed twice

- **File**: `pipeline.py:68, 87`
- **Impact**: The first hand block is parsed once for session metadata (line 68) and again in the main loop (line 87). Minor performance waste — could cache the first parse result and skip re-parsing.

---

### L4. Percentage display inconsistency

- **Files**: `dashboard.py` uses `:.1f%` (e.g. `14.5%`), `sessions.py` uses `:.0f%` (e.g. `15%`)
- **Impact**: VPIP/PFR shown with 1 decimal place on the dashboard but 0 decimals in session reports. Cosmetic inconsistency.

---

### L5. SQL `.format()` for IN clause

- **File**: `stats.py:717`
- **Impact**: Uses `.format()` to build the `IN (?, ?, ...)` placeholder list. The actual values are passed as bind parameters (safe), but the pattern looks alarming at first glance. Could use a helper function for clarity.

---

### L6. Overly broad `except Exception` in upload callback

- **File**: `upload.py:161`
- **Impact**: Catches all `Exception` subclasses including ones that might benefit from propagation. The `noqa: BLE001` suppression is present. Low practical risk since the Dash callback must return a UI message regardless.

---

### L7. Empty file ingestion is silent

- **File**: `pipeline.py:60-62`
- **Impact**: An empty or BOM-only file returns a successful `IngestResult` with all zeros — indistinguishable from "nothing to do." Could log a warning or return a distinct status.

---

## Verified False Positives

These were raised during automated analysis but verified as **not bugs**:

| Claim | Verdict |
|-------|---------|
| `_build_highlights()` crashes on empty DataFrame | Empty check exists at line 364 before `idxmax()` |
| Tournament header `[\d+]+` is a regex bug | `+` inside `[]` is a literal plus; matches buy-in format `13200+1800` |
| FOLD `amount_to_call` contradicts model spec | Intentional design per AnalysisLogic.MD §D for fold EV |
| VPIP / 3-bet counting logic is wrong | Correctly implemented after Phase 2b fix |
| Missing PRIMARY KEY on `actions` table | `id INTEGER PRIMARY KEY AUTOINCREMENT` is the PK |
| Fold equity formula is mathematically wrong | Formula is correct: `P(fold) × pot + P(call) × showdown_EV` |
| XSS via villain usernames in Dash | `html.Span()` auto-escapes all string content |

---

## Documentation Consistency

The documentation audit found **96 % alignment** between code and `.MD` files:

- All formulas in `AnalysisLogic.MD` match their implementations ✅
- All schema columns in `DataStructure.MD` match `schema.sql` ✅
- Architecture and data flow in `Architecture.MD` match actual code structure ✅
- All 11 UX features in `UserExperience.MD` are implemented ✅

Minor gap: Showdown section styling (purple background) was not verified visually.

---

## Remediation Plan — ✅ COMPLETE

All 4 phases have been implemented and committed following strict TDD protocol
(red test commit → green implementation commit). Final test count: **816 passed**.

### Phase 1 — Security & Config Hardening ✅

**Scope**: H1, M1, M6, M7
**Commits**: `test(phase1)` + `fix(phase1)`

| Step | Finding | File(s) | Change |
|------|---------|---------|--------|
| 1a   | H1      | `run.py` | Replace `debug=True` with env-var check; import `os` |
| 1b   | M6      | `run.py` | Derive cache path from `DB_PATH.parent / "cache"` |
| 1c   | M1      | `upload_handler.py` | Guard `content_string.split(",", 1)` with a format check |
| 1d   | M7      | `settings.py` | Add server-side range validation to each save callback |

---

### Phase 2 — Database Performance ✅

**Scope**: H2, H3
**Commits**: `test(phase2)` + `fix(phase2)`

| Step | Finding | File(s) | Change |
|------|---------|---------|--------|
| 2a   | H2      | `schema.sql` | Add three `CREATE INDEX IF NOT EXISTS` statements for `actions` |
| 2b   | H3      | `sessions.py` | Replace `iterrows()` + per-row `_ev_status_label` with `_batch_ev_status_labels()` |

---

### Phase 3 — Ingestion Hardening ✅

**Scope**: H4, M3, M4, M5, L3, L7
**Commits**: `test(phase3)` + `fix(phase3)`

| Step | Finding | File(s) | Change |
|------|---------|---------|--------|
| 3a   | H4      | `pipeline.py` | Change `encoding="utf-8"` → `"utf-8-sig"` |
| 3b   | M4      | `splitter.py` | Normalize `\r\n` / `\r` → `\n` before regex split |
| 3c   | M3      | `pipeline.py` | Defer session commit until first hand is successfully inserted |
| 3d   | M5      | `pipeline.py` | Check `IntegrityError` message for `source_hand_id` before classifying as duplicate |
| 3e   | L3      | `pipeline.py` | Cache `first_parsed`; skip re-parsing block 0 in the loop |
| 3f   | L7      | `pipeline.py` | Log a warning and set a flag when `split_hands()` returns empty |

---

### Phase 4 — Code Quality & Cleanup ✅

**Scope**: M2, M8, L1, L2, L5, L6 (L4 deferred — intentional per-context precision)
**Commits**: `test(phase4)` + `fix(phase4)`

| Step | Finding | File(s) | Change |
|------|---------|---------|--------|
| 4a   | M2      | `dashboard.py`, `sessions.py` | `_fmt_pnl()` falls back to `:,.2f` when `:,.6g` produces scientific notation |
| 4b   | M8      | `ranges.py` | Tighten OESD loop to `range(11)`, gutshot loop to `range(10)` |
| 4c   | L1      | `hand_parser.py` | Replace `[\d.]+` with `\d+(?:\.\d+)?` in monetary regexes |
| 4d   | L2      | `db.py` | Remove `get_hand_equity` / `set_hand_equity` dead shims |
| 4e   | L5      | `stats.py` | Replace `.format()` with f-string for IN clause placeholders |
| 4f   | L6      | `upload.py` | Narrow `except Exception` to `except (OSError, ValueError, KeyError)` |

**Note**: L4 (percentage display inconsistency) was reviewed and determined to be intentional
— dashboard uses `:.1f%` for KPI precision, sessions uses `:.0f%` for compact table display.
