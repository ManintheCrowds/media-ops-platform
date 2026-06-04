# Naming brainstorm — public release (2026-06-04)

**Constraints:** No "Archivist" in public-facing artifacts; no government-meeting / municipality / civic framing; keep defensible ML + ops metrics in neutral language.

**Scoring (1–5):** recruiter clarity · technical accuracy · privacy · GitHub repo fit · OSS collision risk

## Product name (transcription pipeline)

| Candidate | R | T | P | GH | OSS | Total | Notes |
|-----------|---|---|---|----|-----|-------|-------|
| **CaptionPipeline** | 5 | 5 | 4 | 4 | 4 | **22** | **Selected for implementation** — literal, ATS-friendly |
| StreamCaption | 4 | 4 | 4 | 4 | 3 | 19 | Short; generic |
| VoxPublish | 3 | 3 | 5 | 4 | 3 | 18 | Brandable; verify trademarks |
| MediaCaption Engine | 4 | 5 | 4 | 3 | 4 | 20 | Long display name |
| TranscriptOps | 4 | 4 | 4 | 4 | 3 | 19 | Pairs with homelab ops |

## Repository name (combined repo: pipeline + homelab platform)

| Candidate | R | T | P | GH | OSS | Total | Notes |
|-----------|---|---|---|----|-----|-------|-------|
| **media-ops-platform** | 5 | 5 | 4 | 5 | 4 | **25** | **Selected (final)** — dual-brand umbrella |
| caption-platform | 5 | 5 | 4 | 5 | 4 | 23 | Superseded interim rename |
| stream-ops-platform | 4 | 4 | 4 | 4 | 3 | 19 | Ops-heavy |
| unified-homelab-platform | 3 | 4 | 5 | 3 | 3 | 18 | Hides ML story |
| software (keep) | 2 | 3 | 5 | 2 | 2 | 14 | Weak discoverability |

## Implementation defaults (override in GitHub UI if you prefer)

| Role | Value |
|------|--------|
| **Product name** | CaptionPipeline |
| **GitHub repo** | `ManintheCrowds/media-ops-platform` |
| **Product B** | Platform API |
| **License** | MIT (aligns with README badge and portfolio audit) |

## Neutral narrative replacements

| Remove | Use |
|--------|-----|
| Archivist | CaptionPipeline |
| Government meeting video | Long-form video libraries needing search and captions |
| Municipalities / cities / citizens | Production feeds / deployments / audiences |
| Nine cities | Nine production feeds |
| SCC (employer-tied) | Broadcast SCC-format captions (format only) |

## Out of scope for rename

- `plans/`, `.cursor/plans/`, `.cursor/state/` — excluded from public tree (TTRPG "Archivist" role docs, `D:\` paths).
- Python modules — no `archivist` identifiers in `*.py`.

## Operator sign-off

- [x] Approve **CaptionPipeline** + **Platform API** + **media-ops-platform** + **MIT** (implemented 2026-06-04)
- [ ] Or note overrides: product ______ · repo ______ · license ______

After sign-off: **GH-PF-04** (public) per [GITHUB_PUBLIC_AUDIT_2026-06.md](https://github.com/ManintheCrowds/MiscRepos/blob/main/docs/portfolio/GITHUB_PUBLIC_AUDIT_2026-06.md).
