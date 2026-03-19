---
name: Public Repo Voice Review
overview: Review of public GitHub repos (harness, portfolio-harness, scp) for unprofessional or author-centric language. Identifies "my portfolio", "only I use", and similar first-person/internal phrasing that reads like internal notes rather than public documentation.
todos: []
isProject: false
---

# Public Repo Voice Review

## Scope

Repos reviewed: **harness**, **portfolio-harness**, **scp** (ManintheCrowds org). Focus on READMEs, docs, and other public-facing content.

**Writing voice (from portfolio-harness):** Terse, technical, personality-driven. "Programmer first. Cyberpunk. Bitcoin. Glitch. Goth." Avoid first-person author-centric language in docs meant for external adopters.

---

## Findings

### 1. Harness repo (highest impact — portable, external adopters)


| File                                                          | Line | Issue                                                      | Current text                                                                                                                  |
| ------------------------------------------------------------- | ---- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [harness/README.md](D:\harness\README.md)                     | 49   | "my portfolio" in primary prompt; reads like internal note | `"Would a developer with no knowledge of my portfolio use this in their own project?"`                                        |
| [harness/docs/DELINEATION.md](D:\harness\docs\DELINEATION.md) | 7    | Same author-centric prompt                                 | `"Would a developer with no knowledge of my portfolio or domain-specific projects be able to use this in their own project?"` |
| [harness/docs/DELINEATION.md](D:\harness\docs\DELINEATION.md) | 19   | "only I use" — first-person, internal                      | `Does this reference a specific MCP server only I use (observation, provenance, Daggr, etc.)?`                                |


**Why it reads unprofessional:** External visitors see "my portfolio" and "only I use" and infer the docs are written for the maintainer, not for them. The delineation concept is useful; the phrasing should be reader-centric.

### 2. Portfolio-harness repo


| File                                                                                                                                              | Line   | Issue                                         | Current text                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| [portfolio-harness/docs/PROMOTION_TO_HARNESS.md](D:\portfolio-harness\docs\PROMOTION_TO_HARNESS.md)                                               | 9      | Lists author projects by name; author-centric | `"Would a developer with no knowledge of my portfolio, Bitcoin-Chaos, PentAGI, or Daggr be able to use this in their own project?"` |
| [portfolio-harness/docs/plans/2026-03-17-harness-delineation-design.md](D:\portfolio-harness\docs\plans\2026-03-17-harness-delineation-design.md) | 41, 53 | Same patterns                                 | Primary prompt + "only I use" in secondary table                                                                                    |


**Note:** `docs/plans/` may be lower priority (design docs). `PROMOTION_TO_HARNESS.md` is more visible.

### 3. SCP repo

**No issues.** README and docs are neutral, professional, no first-person author references.

### 4. Exclusions (acceptable)

- **routstr SKILL.md** — `"how do I use AI with Bitcoin?"` — user-quote trigger, fine
- **product-scope SKILL.md** — `"what are we building?"` — user-quote trigger, fine
- **"vs your portfolio"** in README — second-person is appropriate; the problem is the quoted prompt, not "your"

---

## Recommended Rewrites

### Primary delineation prompt (harness + portfolio-harness)

**Current (author-centric):**

> "Would a developer with no knowledge of my portfolio use this in their own project?"

**Proposed (reader-centric, preserves intent):**

> "Would any developer be able to use this in their own project without context from other projects?"

Or, shorter:

> "Is this portable and self-contained?"

### DELINEATION.md secondary table (harness)

**Current:**

> Does this reference a specific MCP server only I use (observation, provenance, Daggr, etc.)?

**Proposed:**

> Does this reference a project-specific MCP server (observation, provenance, Daggr, etc.) that is not part of the harness baseline?

### README Delineation section (harness)

**Current:**

> When extending harness or adding components, use [docs/DELINEATION.md](docs/DELINEATION.md) to decide what belongs in harness vs your portfolio. Primary prompt: "Would a developer with no knowledge of my portfolio use this in their own project?" Yes → harness; No → portfolio.

**Proposed:**

> When extending harness or adding components, use [docs/DELINEATION.md](docs/DELINEATION.md) to decide what belongs in harness vs your project. Primary prompt: "Would any developer be able to use this without context from other projects?" Yes → harness; No → your project.

---

## Implementation Order

1. **harness** — README + DELINEATION.md (highest visibility for adopters)
2. **portfolio-harness** — PROMOTION_TO_HARNESS.md
3. **portfolio-harness** — docs/plans/2026-03-17-harness-delineation-design.md (optional; design doc)

---

## Summary


| Repo              | Files to update                                     | Priority |
| ----------------- | --------------------------------------------------- | -------- |
| harness           | README.md, docs/DELINEATION.md                      | High     |
| portfolio-harness | docs/PROMOTION_TO_HARNESS.md                        | Medium   |
| portfolio-harness | docs/plans/2026-03-17-harness-delineation-design.md | Low      |
| scp               | None                                                | —        |


