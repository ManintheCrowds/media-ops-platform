# Security Audit Roadmap — software

## Repository
- **Path:** D:/software
- **Primary stack:** Python services, infra configs, CI
- **Data tier (initial):** confidential
- **Notes:** Tests workflow includes Bandit/Safety; no Dependabot/CodeQL/secrets scanning.

## Phased roadmap (0–5)
### Phase0_TriageAndScope
- **Goal:** Validate CRITICAL findings in docs vs code.
- **Effort:** 0.5–1.5 days
- **Blast radius:** low

### Phase1_MetadataAndPolicy_Soft
- **Goal:** Ensure `project-metadata.yml` coverage for root and service subdirs.
- **Effort:** 1–2 days
- **Blast radius:** low-medium

### Phase2_SecretsAndDependabot
- **Goal:** Add secrets scanning and Dependabot for Python services.
- **Effort:** 1–3 days
- **Blast radius:** medium

### Phase3_CodeQL
- **Goal:** Enable CodeQL and tune for Python.
- **Effort:** 1–2 days
- **Blast radius:** medium-high

### Phase4_RemediationSprint
- **Goal:** Remove real secrets, move configs to env, reduce findings.
- **Effort:** 3–10 days
- **Blast radius:** medium-high

### Phase5_GovernanceHardening
- **Goal:** Make scans blocking for main branch merges.
- **Effort:** 1–2 days
- **Blast radius:** medium
