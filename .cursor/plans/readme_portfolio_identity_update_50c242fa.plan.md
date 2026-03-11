---
name: README Portfolio Identity Update
overview: Update READMEs across portfolio codebases to stay current, express your professional identity (cyberpunk bitcoiner glitch artist goth, programmer first) via tagline, About section, and infused voice, and apply CL4R1T4S patterns to optimize prompt usage and revision workflow.
todos: []
isProject: false
---

# README Portfolio Identity and CL4R1T4S Update

## Scope

**Primary READMEs** (root of each codebase):

- [portfolio-harness/README.md](D:\portfolio-harness\README.md) — hub; gets full About section
- [software/README.md](D:\software\README.md)
- [Arc_Forge/README.md](D:\Arc_Forge\README.md)
- [moltbook-watchtower/README.md](D:\moltbook-watchtower\README.md)
- [prusa_XL_soft/README.md](D:\prusa_XL_soft\README.md)
- [obsidian_cursor_integration/README.md](D:\obsidian_cursor_integration\README.md)
- [local-first/README.md](D:\local-first\README.md)

**Sub-project READMEs** (link to harness About, get tagline + voice):

- [WatchTower_main/WatchTower_main/README.md](D:\portfolio-harness\WatchTower_main\WatchTower_main\README.md)
- [berserk_custom_bit/README.md](D:\portfolio-harness\berserk_custom_bit\README.md)

---

## Phase 1: Persona and About Source of Truth

### 1.1 Create `docs/AUTHOR.md` in portfolio-harness

Single source of truth for professional identity. Other READMEs link here.

**Content outline:**

- **Tagline:** One line (e.g. *Programmer first. Cyberpunk. Bitcoin. Glitch. Goth.*)
- **Short bio:** 2–3 sentences — programmer who ships; local-first, sound money, self-custody; glitch aesthetic; dark/technical sensibility
- **Links:** Portfolio, Bitcoin-Chaos work, org-intent, MCP/local-proto
- **Voice cues:** Technical over flowery; anti-establishment where it fits; no corporate speak

**Placement:** [portfolio-harness/docs/AUTHOR.md](D:\portfolio-harness\docs\AUTHOR.md)

### 1.2 Add About section to portfolio-harness README

Insert after "Portfolio Highlights" or before "Portfolio projects":

```markdown
## About

[2–3 sentence excerpt from AUTHOR.md, or link]

See [docs/AUTHOR.md](docs/AUTHOR.md) for full bio.
```

---

## Phase 2: Tagline and Voice per README

### 2.1 Tagline placement

Add a one-line tagline to each primary README, typically as:

- **Option A:** Subtitle under the main title (e.g. `> Programmer first. Cyberpunk. Bitcoin. Glitch.`)
- **Option B:** Footer before License/Support (e.g. `*Built by a programmer who ships.`*)

**Per-repo guidance:**


| Repo                           | Placement            | Rationale                              |
| ------------------------------ | -------------------- | -------------------------------------- |
| portfolio-harness              | Subtitle under title | Hub; identity front and center         |
| software                       | Footer               | Technical platform; identity secondary |
| Arc_Forge                      | Subtitle             | Creative/TTRPG; identity fits          |
| moltbook-watchtower            | Footer               | Monitoring; subtle                     |
| prusa_XL_soft                  | Footer               | Hardware/maker; subtle                 |
| obsidian_cursor_integration    | Subtitle             | PKM/tools; identity fits               |
| local-first                    | Footer               | Reference doc; subtle                  |
| WatchTower, berserk_custom_bit | Footer               | Sub-projects; link to harness          |


### 2.2 Infused voice

Adjust tone where it fits (not everywhere):

- **Replace:** "Contributions welcome" → "PRs welcome. Code speaks."
- **Replace:** "Please refer to" → "See"
- **Add:** Short, punchy intros where currently generic
- **Keep:** Technical accuracy; no forced slang

**Repos where voice fits best:** portfolio-harness, Arc_Forge, berserk_custom_bit, moltbook-watchtower (epistemic hygiene already present).

---

## Phase 3: Content Updates (Keep READMEs Current)

Apply fixes from existing plans where still relevant:

- **readme_quick_wins** ([readme_quick_wins_6436f3e9.plan.md](D:\portfolio-harness\plans\readme_quick_wins_6436f3e9.plan.md)): WatchTower formatting, links, Python versions, troubleshooting links, path fixes
- **readme_scope_update** (home-cyber-risk): Multi-source breach docs, architecture, config — only if that project is in scope

**Cross-cutting:**

- Add/refresh "Quick start" where missing
- Ensure test commands are visible
- Fix broken or placeholder links (e.g. moltbook `git clone <repo-url>`)
- Add `docs/cl4r1t4s_analysis` reference in portfolio-harness README (see Phase 4)

---

## Phase 4: CL4R1T4S Integration

### 4.1 Add CL4R1T4S section to portfolio-harness README

Under "Documentation" or "AI Agent Documentation":

```markdown
### CL4R1T4S patterns

For agents working in this repo: [docs/cl4r1t4s_analysis/README.md](docs/cl4r1t4s_analysis/README.md). Use [PROMPT_TEMPLATES.md](docs/cl4r1t4s_analysis/PROMPT_TEMPLATES.md) for workflow design, placement, revision, MCP, and session start. Bounded retries (3), convention-first, verify before done.
```

### 4.2 Session-start prompt for README work

Add to [PROMPT_TEMPLATES.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\PROMPT_TEMPLATES.md) (or a new "README maintenance" template):

```
Update README(s) for [repo(s)]. Per docs/cl4r1t4s_analysis/dialectic_extracts.md: bounded revision (max 3), verify before done. Run document-review on draft before finalizing. Apply critic report per critic-loop-gate.
```

### 4.3 Subagent: README maintainer (optional)

Per [create-subagent skill](c:\Users\schum.cursor\skills-cursor\create-subagent\SKILL.md), create `.cursor/agents/readme-maintainer.md`:

- **Description:** Proactively reviews and updates READMEs for accuracy, links, and voice. Use when READMEs are stale, after major features, or when adding new projects.
- **System prompt:** Load docs/AUTHOR.md, docs/cl4r1t4s_analysis; apply dialectic (bounded revision, critic before done); preserve technical accuracy; infuse voice where appropriate.

---

## Phase 5: Revision Workflow (Dialectic-Protocol)

Per [dialectic-protocol](D:\portfolio-harness.cursor\skills\dialectic-protocol\SKILL.md):

1. **First pass:** Apply changes per phases 1–4
2. **Critic report:** Produce critic JSON (pass, score, issues, fixes) before marking done
3. **Revision:** If pass=false or score below threshold, revise once; stop after 2 rounds or if score delta < 1
4. **Done:** Include final critic report in summary

---

## Implementation Order

1. Create [docs/AUTHOR.md](D:\portfolio-harness\docs\AUTHOR.md) — source of truth
2. Update [portfolio-harness/README.md](D:\portfolio-harness\README.md) — About, tagline, CL4R1T4S, voice
3. Update primary READMEs (software, Arc_Forge, moltbook-watchtower, prusa_XL_soft, obsidian_cursor_integration, local-first) — tagline, voice, content fixes
4. Update sub-project READMEs (WatchTower, berserk_custom_bit) — tagline, links, quick wins
5. Add README template to [PROMPT_TEMPLATES.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\PROMPT_TEMPLATES.md)
6. (Optional) Create readme-maintainer subagent
7. Run document-review on updated READMEs
8. Produce critic report; revise if needed

---

## Files to Create/Modify


| Action            | Path                                                         |
| ----------------- | ------------------------------------------------------------ |
| Create            | portfolio-harness/docs/AUTHOR.md                             |
| Modify            | portfolio-harness/README.md                                  |
| Modify            | software/README.md                                           |
| Modify            | Arc_Forge/README.md                                          |
| Modify            | moltbook-watchtower/README.md                                |
| Modify            | prusa_XL_soft/README.md                                      |
| Modify            | obsidian_cursor_integration/README.md                        |
| Modify            | local-first/README.md                                        |
| Modify            | portfolio-harness/WatchTower_main/WatchTower_main/README.md  |
| Modify            | portfolio-harness/berserk_custom_bit/README.md               |
| Modify            | portfolio-harness/docs/cl4r1t4s_analysis/PROMPT_TEMPLATES.md |
| Create (optional) | portfolio-harness/.cursor/agents/readme-maintainer.md        |


---

## Success Criteria

- AUTHOR.md exists and reads professionally
- All primary READMEs have tagline and link to AUTHOR where appropriate
- portfolio-harness has About section and CL4R1T4S reference
- Voice is infused where it fits; technical content unchanged
- Quick wins (formatting, links, paths) applied
- PROMPT_TEMPLATES includes README maintenance prompt
- Critic report produced; pass=true or user accepts

