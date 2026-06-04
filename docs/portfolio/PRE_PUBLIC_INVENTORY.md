# Pre-public inventory — media-ops-platform (2026-06-04)

Path | Public-safe? | Action | Notes
-----|--------------|--------|------
`app/`, `services/`, `tests/`, `alembic/`, `config/` | yes | keep | Core platform code
`docs/portfolio/` | yes | keep | After rebrand scrub
`docs/API.md`, `docs/DEVELOPMENT.md` | yes | keep | Public API/dev entrypoints
`docs/research/`, `docs/brainstorms/` | partial | redact or de-index | Contains `D:\` / harness paths; not linked from README
`docs/AI_DOCUMENTATION_INDEX.md` | partial | redact harness links | Remove `portfolio-harness` absolute paths
`.github/workflows/` | yes | keep | tests, gitleaks, trufflehog, codeql
`.env.example` | yes | keep | No real secrets
`plans/` | no | **gitignore + untrack** | TTRPG plans, `D:\` paths, MiscRepos refs
`.cursor/plans/` | no | **gitignore + untrack** | Operator/agent plans
`.cursor/state/` | no | **gitignore + untrack** | pending_tasks, MiscRepos paths
`O8L1T34TUS_SCP_COGNITO_HAZARD/` | no | **gitignore** | Internal experiment name
`OBLITERATUS-src/` | no | **gitignore** | Non-portfolio artifact
`stealth/` | no | **gitignore** | Non-portfolio
`home-cyber-risk/config/identifiers.yml` | no | **gitignore** | Sensitive identifiers pattern
`cursor-quality-metrics/` | no | already partial | Local metrics; keep gitignored via cursor-metrics pattern
`portfolio/case-studies/` | yes | keep | Renamed `caption-pipeline.html`; neutral copy
`job-automation-service/.github/` | yes | keep | Nested CI only

## CI inventory (default branch)

| Workflow | Purpose |
|----------|---------|
| `tests.yml` | lint, unit, integration tests |
| `security-gitleaks.yml` | secrets |
| `security-trufflehog.yml` | secrets |
| `codeql.yml` | static analysis |

## Rename note

GitHub repo target: `ManintheCrowds/media-ops-platform` (was `software`). Operator renames in GitHub Settings while private; redirects preserve old URLs.
