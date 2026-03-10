---
name: Expand jCodeMunch Analysis
overview: Replace the binary pass/fail observability test with a richer analysis that includes quality metrics, timing, edge-case coverage, baseline comparison, and structured output for diagnostics and regression detection.
todos: []
isProject: false
---

# Expand jCodeMunch Observability Analysis

Replace the myopic pass/fail model with multi-dimensional analysis: quality metrics, timing, edge cases, baselines, and actionable diagnostics.

---

## 1. Analysis Dimensions (Beyond Pass/Fail)


| Dimension           | Current     | Expanded                                             |
| ------------------- | ----------- | ---------------------------------------------------- |
| **Status**          | pass / fail | OK / WARN / FAIL with rationale                      |
| **Timing**          | none        | Per-tool latency (ms)                                |
| **Quality**         | none        | Relevance score, verify hash, result completeness    |
| **Edge cases**      | none        | Empty query, typo, non-indexed path                  |
| **Baseline**        | none        | Compare symbol count, disk size to prior or expected |
| **Output size**     | none        | Approx token/chars per tool (for context budgeting)  |
| **Recommendations** | none        | Actionable notes (e.g. "re-index recommended")       |


---

## 2. Per-Tool Analysis Additions

### index_folder

- **Timing:** duration_seconds
- **Quality:** `changed + new + deleted` vs 0 (incremental health)
- **WARN:** `no_symbols_count` > 0 or `discovery_skip_counts` high
- **Note:** "Index fresh" vs "No changes" interpretation

### list_repos

- **Timing:** from `_meta.timing_ms` if present
- **Quality:** repo count >= 1, symbol_counts non-empty
- **Baseline:** Compare total symbol count to previous run (if persisted)

### search_symbols

- **Timing:** from `_meta.timing_ms`
- **Quality:** top match score, result_count; "audit" should match `_audit`_*
- **WARN:** result_count 0 for known-good query
- **Edge case:** Run with typo ("audit_summary" vs "audit_summry") — expect fewer/different results

### get_symbol

- **Timing:** from `_meta.timing_ms`
- **Quality:** verify hash pass/fail; source non-empty
- **FAIL:** verify reports drift

### get_file_outline

- **Quality:** symbol_count > 0 for known file; kind distribution
- **Edge case:** Non-indexed path — expect empty symbols, status WARN

### get_file_content

- **Quality:** content length matches requested range
- **Output size:** chars returned (proxy for tokens)

### search_text

- **Quality:** match_count; "audit_wrapper" in local-proto may be 0 (small index)
- **WARN:** 0 matches when query appears in indexed file (possible cache issue)

### get_repo_outline

- **Quality:** languages, total_symbols populated
- **Note:** Some jcodemunch versions return `total_symbols: null` — document

### Disk stats

- **Baseline:** Compare total_mb, file_count to prior run
- **WARN:** Sudden growth or shrinkage without re-index

---

## 3. Edge Case Tests (New)


| Test             | Query/Input                                  | Expected                             | Status Logic     |
| ---------------- | -------------------------------------------- | ------------------------------------ | ---------------- |
| Empty query      | search_symbols(query="")                     | Few or no results                    | WARN if error    |
| Typo query       | search_symbols(query="audit_summry")         | Fewer/different than "audit_summary" | OK (fuzzy works) |
| Non-indexed path | get_file_outline(file_path="nonexistent.py") | Empty symbols                        | WARN             |
| Verify drift     | get_symbol(verify=True)                      | Hash match                           | FAIL if mismatch |


---

## 4. Output Format

### Structured report (JSON)

```json
{
  "timestamp": "ISO8601",
  "overall": { "status": "OK|WARN|FAIL", "score": 0.0-1.0, "summary": "..." },
  "tools": {
    "index_folder": {
      "status": "OK",
      "timing_ms": 40,
      "quality": { "incremental": true, "changed": 0 },
      "notes": []
    },
    "search_symbols": {
      "status": "OK",
      "timing_ms": 12,
      "quality": { "result_count": 5, "top_score": 32, "relevance": "high" },
      "notes": []
    }
  },
  "edge_cases": { "empty_query": "WARN", "non_indexed_path": "WARN" },
  "baseline": { "symbol_count": 20273, "disk_mb": 29.04, "delta_from_prior": null },
  "recommendations": []
}
```

### Human-readable summary

- Overall: OK / WARN / FAIL with one-line reason
- Per-tool: status, timing, quality highlight
- Recommendations: "Re-run index_folder after adding files", "search_text returned 0 — verify index includes target file"

---

## 5. Baseline Persistence (Optional)

- **File:** `.cursor/state/jcodemunch_baseline.json` or `.code-index/.last_run.json`
- **Content:** Last run's symbol_count, disk_mb, timestamp
- **Use:** Delta in next run; WARN if symbol_count drops without invalidate_cache

---

## 6. Implementation Approach

**File:** [.cursor/scripts/jcodemunch_observability.py](D:\portfolio-harness.cursor\scripts\jcodemunch_observability.py)

1. Introduce `Analyzer` or result builder that collects per-tool: status, timing, quality, notes
2. Add timing via `time.perf_counter()` around each tool call
3. Add edge-case block: empty query, non-indexed path
4. Add baseline load/save (optional, behind flag)
5. Compute overall status: FAIL if any FAIL; WARN if any WARN; else OK
6. Emit JSON report to stdout or `--output report.json`
7. Keep human-readable sections; add "ANALYSIS" section with status, score, recommendations

**Exit code:** 0 = OK, 1 = WARN (optional: 2 = FAIL) — or keep 0/1 with WARN as 0 for non-blocking

---

## 7. Doc Updates

- [JCODEMUNCH_OBSERVABILITY.md](D:\portfolio-harness.cursor\docs\JCODEMUNCH_OBSERVABILITY.md): Document new analysis dimensions, output format, baseline file, interpretation guide

---

## 8. Scope Boundaries

- **In scope:** Richer analysis in existing script; JSON output; edge cases; optional baseline
- **Out of scope:** pytest integration; CI integration; token estimation (can add as char count proxy later)

