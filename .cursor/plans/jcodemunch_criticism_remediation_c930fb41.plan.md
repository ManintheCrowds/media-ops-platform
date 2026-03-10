---
name: jCodeMunch Criticism Remediation
overview: "Address the six criticism areas from the Quick Wins post-implementation review: golden task fragility, audit adoption limitations, Windows grep robustness, CI workflow gaps, critic-loop compliance, and documentation drift."
todos: []
isProject: false
---

# jCodeMunch Criticism Remediation Plan

Address the six criticism areas identified in the Quick Wins post-implementation review.

---

## 1. Golden Task Set Fragility

### 1.1 Disambiguate `main`

**Problem:** `main` appears in many files; `search_symbols` returns the first match, which may be wrong.

**Solution:** Extend `_method_jcodemunch` to accept optional `expected_file` and filter results. When a task has `expected_file`, iterate over `search_symbols` results and pick the first whose `file` (or `path`) matches. jCodeMunch results typically include file path in each result.

**Change in** [jcodemunch_benchmark.py](D:\portfolio-harness.cursor\scripts\jcodemunch_benchmark.py):

- Add optional 5th element to task tuple: `expected_file` (or reuse existing `file_path` from tuple)
- In `_method_jcodemunch`, when `expected_file` is provided, filter `results` to those where `r.get("file", "").endswith(expected_file)` or similar before taking `results[0]`
- If no matching result, try next result; if none match, return incorrect

### 1.2 Add portfolio-harness tasks

**Problem:** 11 of 12 tasks are in local-proto; portfolio-harness is barely exercised.

**Solution:** Add 3–4 symbols from portfolio-harness. Candidates (verify they exist and are indexed):

- `_resolve_repo_id` from [jcodemunch_benchmark.py](D:\portfolio-harness.cursor\scripts\jcodemunch_benchmark.py) — previously failed; diagnose first (see 1.3)
- `run_observability` from [jcodemunch_observability.py](D:\portfolio-harness.cursor\scripts\jcodemunch_observability.py)
- `compute_checksum` already in ROOT
- `log_agent_event` or similar from `.cursor/scripts/`

### 1.3 Diagnose and fix `_resolve_repo_id`

**Problem:** Task was removed instead of diagnosing why jCodeMunch returned 0 results.

**Solution:**

- Check if portfolio-harness (ROOT) is indexed: `list_repos` returns both local-proto and portfolio-harness
- Observability indexes `LOCAL_PROTO` only; benchmark may need portfolio-harness indexed. Check [jcodemunch_observability.py](D:\portfolio-harness.cursor\scripts\jcodemunch_observability.py) — it indexes `LOCAL_PROTO`. The `.code-index` may have both if index_folder was run on portfolio-harness elsewhere
- Add diagnostic: log `list_repos` output and `search_symbols` for `_resolve_repo_id` when run with ROOT
- If portfolio-harness is not indexed in CI, add an index step for ROOT (or a subset) before benchmark
- Re-add `_resolve_repo_id` once indexing is confirmed

---

## 2. Audit Adoption Script Limitations

### 2.1 Date filtering

**Change in** [audit_adoption.py](D:\portfolio-harness.cursor\scripts\audit_adoption.py):

- Add `--since` and `--until` (ISO8601 or relative: `7d`, `24h`)
- Parse `timestamp` from each entry; filter to entries within range
- If `timestamp` missing, include in "unknown" count or skip (document behavior)

### 2.2 Session grouping (optional)

**Constraint:** Audit schema has no `session_id`; only `timestamp`, `tool`, `args_hash`, `outcome`, `risk_tier`.

**Solution:** Heuristic grouping — entries within N minutes (e.g. 30) of each other = same session. Add `--session-gap-minutes` (default: 30) and output `sessions` array with per-session jcodemunch/other counts. Lower priority; can defer.

### 2.3 Unknown tool handling

**Change:** Add `--strict` flag. When set, treat `tool` missing or `"unknown"` as error: increment `parse_errors` and optionally exit 1. Without `--strict`, keep current behavior but add `parse_errors` and `unknown_count` to output for visibility.

---

## 3. Windows Grep Implementation

### 3.1 Python-native fallback

**Change in** [jcodemunch_benchmark.py](D:\portfolio-harness.cursor\scripts\jcodemunch_benchmark.py) `_method_grep_read_file`:

- On Windows: try PowerShell first; on failure (or `FileNotFoundError`), fall back to Python-native: `pathlib.Path.rglob("*.py")` + `re.search(pattern, content)` to find first match
- On Unix: keep rg then grep; add Python fallback as last resort

### 3.2 Path parsing robustness

**Current:** `rsplit(":", 1)` — for `C:\path\file.py:123` gives `["C:\\path\\file.py", "123"]` which is correct. Edge case: path with colon in filename (rare). Document that paths with colons in the filename are unsupported; no code change needed for typical cases.

---

## 4. CI Workflow

### 4.1 Artifact upload

**Change in** [jcodemunch_ci.yml](D:\portfolio-harness.github\workflows\jcodemunch_ci.yml):

- Use `actions/upload-artifact@v4` with `if-no-files-found: warn` (or equivalent) so missing files don't fail the step
- Or split into two upload steps: one for `observability.json` (always exists if observability ran), one for benchmark report (only if benchmark wrote it)
- Simpler: use `continue-on-error: true` for upload, or `path: |` with conditional paths — GitHub doesn't support conditional paths directly. Use a pre-step that creates empty placeholder files if missing, so upload never fails.

### 4.2 Index caching

**Change:** Add cache step for `.code-index`:

```yaml
- uses: actions/cache@v4
  with:
    path: .code-index
    key: jcodemunch-index-${{ hashFiles('local-proto/**/*.py') }}
```

- Cache key based on `local-proto` content hash so cache invalidates when indexed code changes
- Restore before observability; observability will incremental-index (fast if cache hit)

### 4.3 Path triggers

**Current:** `.cursor/docs/JCODEMUNCH*.md` — GitHub glob `*` matches within a path segment. Verify: `JCODEMUNCH_OBSERVABILITY.md` should match. If not, use `.cursor/docs/`** or list explicitly:  `.cursor/docs/JCODEMUNCH_OBSERVABILITY.md`.

---

## 5. Critic-Loop-Gate Compliance

**Problem:** Quick Wins did not produce a formal critic report before finalizing.

**Solution (process):**

- Add to [critic-loop-gate.mdc](c:\Users\schum.cursor\rules\critic-loop-gate.mdc) or a CONTEXT note: when implementing multi-file changes (docs, workflow UI, code), the agent should produce a critic JSON before marking complete
- Optional: Add a `# CRITIC_REPORT` section to plan files or handoff templates as a reminder
- No code change to scripts; this is a process/documentation update

---

## 6. Documentation Drift

**Change in** [JCODEMUNCH_OBSERVABILITY.md](D:\portfolio-harness.cursor\docs\JCODEMUNCH_OBSERVABILITY.md):

- Remove or replace the "Benchmark results (2026-03-10)" table (lines 173–181) — it shows 5 tasks with grep failing; now we have 12 tasks and grep works on Windows
- Replace with: "Run the benchmark for current results" or a single-row summary: "12 golden tasks; run `jcodemunch_benchmark.py` for latest."
- Ensure task catalog list matches script exactly after 1.1–1.3 changes

---

## Execution Order

1. **Golden task** — Diagnose `_resolve_repo_id` (1.3), add file filtering (1.1), add portfolio-harness tasks (1.2)
2. **Audit adoption** — Date filter (2.1), unknown handling (2.3); defer session grouping (2.2)
3. **Windows grep** — Python fallback (3.1)
4. **CI** — Artifact fix (4.1), index cache (4.2), path triggers (4.3)
5. **Docs** — JCODEMUNCH_OBSERVABILITY.md (6)
6. **Process** — Critic-loop note (5)

---

## Files to Modify


| File                                                                                                           | Changes                                                                                                                   |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| [.cursor/scripts/jcodemunch_benchmark.py](D:\portfolio-harness.cursor\scripts\jcodemunch_benchmark.py)         | File filtering in _method_jcodemunch; Python grep fallback; add portfolio-harness tasks; re-add _resolve_repo_id if fixed |
| [.cursor/scripts/audit_adoption.py](D:\portfolio-harness.cursor\scripts\audit_adoption.py)                     | --since, --until; --strict; parse_errors, unknown_count in output                                                         |
| [.github/workflows/jcodemunch_ci.yml](D:\portfolio-harness.github\workflows\jcodemunch_ci.yml)                 | Cache .code-index; artifact upload robustness; path triggers                                                              |
| [.cursor/docs/JCODEMUNCH_OBSERVABILITY.md](D:\portfolio-harness.cursor\docs\JCODEMUNCH_OBSERVABILITY.md)       | Remove stale results table; align task catalog                                                                            |
| [.cursor/scripts/jcodemunch_observability.py](D:\portfolio-harness.cursor\scripts\jcodemunch_observability.py) | If needed: index ROOT (portfolio-harness) for benchmark — check whether observability already indexes both                |


---

## Out of Scope

- Session grouping in audit (heuristic; defer)
- Critic automation (manual process reminder only)

