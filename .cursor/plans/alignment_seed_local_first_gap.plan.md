---
name: Alignment-Seed Local-First Gap
overview: Gap analysis and task decomposition for alignment-seed vs local-first AI_SECURITY requirements.
status: pending
priority: 2
phase: extend
todos: []
isProject: false
---

# Alignment-Seed Local-First Gap Analysis

Gap analysis against [local-first AI_SECURITY](D:\local-first\AI_SECURITY.md). Ref: [criticism_remediation_plans](D:\software\.cursor\plans\criticism_remediation_plans_f26043cd.plan.md).

---

## Gap Analysis

| Requirement | alignment-seed status | Gap | Task |
|-------------|------------------------|-----|------|
| Encryption at rest | data/ not encrypted | High | L1: Document in PRIVACY.md; L2: Implement DPAPI or password-derived encryption for data/*.json |
| No cloud / no sync | Compliant | None | — |
| Traceability | analyze_alignment outputs summary | Partial | L3: Add optional audit log for capture script invocations (timestamp, script name, no PII) |
| HITL | Capture scripts are human-run | Compliant | — |
| Micro-segmentation | data/ isolated | Compliant | — |
| Tool registry / JIT | N/A (no AI tools) | — | — |

---

## Task Decomposition

### L1: PRIVACY.md Update (Early)

- Document encryption plan in [alignment-seed/docs/PRIVACY.md](D:\alignment-seed\docs\PRIVACY.md)
- Cross-ref [local-first AI_SECURITY](D:\local-first\AI_SECURITY.md)
- Add "Encryption at rest: planned; not yet implemented" and key management options (DPAPI, password-derived)

### L2: Encryption Implementation (Later)

- Implement DPAPI or password-derived encryption for data/*.json
- Depends on key management decision
- Out of scope for initial remediation

### L3: Capture Audit Log (Optional)

- Add optional audit log for capture script invocations
- Fields: timestamp, script name; no PII
- Low priority

---

## Implementation Order

1. L1 (doc only) — early
2. L2 — when wire is proven; key management decided
3. L3 — optional; low priority
