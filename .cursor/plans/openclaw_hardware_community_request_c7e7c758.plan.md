---
name: OpenClaw Hardware Community Request
overview: Add the community request for OpenClaw hardware recommendations to the short-term to-do, with proper task structure and placement per tech-lead and product-scope conventions.
todos: []
isProject: false
---

# Add OpenClaw Hardware Community Request to Short-Term To-Do

## Context

**Community request (verbatim):**

> "Out of curiosity, if someone didn't have an extra computer laying around and wanted to get something that is more up to date with AI specific specs, what computer or hardware setup would you recommend for running openclaw specifically? I personally lean more towards Mac because I feel safer using that, but curious what you would recommend for someone that might not be super technical. Since Mac minis are selling out, it seems like that might be the best solution, but I could see you having an alternative take on that"

**Key requirements inferred:**

- Hardware recommendations for OpenClaw
- AI-specific specs (unified memory, Neural Engine, VRAM for local models)
- Mac preference (safety, non-technical users)
- Mac Mini alternatives (availability concern)
- Non-technical audience

---

## 1. Where the Task Goes

**Target file:** `[.cursor/state/pending_tasks.md](D:\portfolio-harness\.cursor\state\pending_tasks.md)`

**Section choice:** Add a new **PENDING_SHORT_TERM** section for community requests and quick wins. Rationale:

- `PENDING_OPTIONAL` is for integration/validation tasks (Continue.dev, Aider)
- `PENDING_OTHER` is for misc (continual-learning, Playwright, Korean switch)
- A dedicated short-term section makes community requests visible and prioritizable

**Alternative:** Add to `PENDING_OPTIONAL` if you prefer not to introduce a new section. The task would sit alongside I1, I2.

---

## 2. Task Entry Format

Per existing `pending_tasks.md` schema:


| ID  | Status  | Task                                                                                                                                                                  | Spec / Link                                                                                                |
| --- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| ST1 | pending | **OpenClaw hardware recommendations (community request):** Create doc with AI-specific specs, Mac vs alternatives, Mac Mini availability, non-technical user guidance | [OPENCLAW.md](../../local-proto/docs/OPENCLAW.md), [REQUIREMENTS.md](../../local-proto/REQUIREMENTS.md) §4 |


---

## 3. Artifact Placement (Tech-Lead)

**Where the deliverable lives:**

- **Option A:** Extend [local-proto/docs/OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md) with a "Hardware" section (keeps OpenClaw docs in one place)
- **Option B:** Create `local-proto/docs/OPENCLAW_HARDWARE.md` (separate doc, linked from OPENCLAW.md)

**Recommendation:** Option A — add a "Hardware" section to OPENCLAW.md. Existing doc already covers install, config, SOUL, local backends; hardware fits naturally. Cross-ref [REQUIREMENTS.md](D:\portfolio-harness\local-proto\REQUIREMENTS.md) §4 (current hardware constraints: Jetson, GTX 1060) for contrast.

---

## 4. Content Scope (Product-Scope)

**Requirements:**

1. AI-specific specs: unified memory (M-series), VRAM for local models, Neural Engine
2. Mac preference: safety, ease for non-technical users
3. Mac Mini: M2/M4, 16GB vs 48GB for local vs cloud
4. Mac Mini alternatives: refurb M1/M2, cloud VPS, Windows/Linux options
5. Consider non-mac solutions if there is a minimal setup solution tha makes sense if this requirement is voided. The person is openminded. 
6. Non-technical guidance: minimal setup, "plug and run" path

**Acceptance criteria:**

- Given a non-technical user who prefers Mac, they can choose a hardware path (Mac Mini vs alternative)
- Given Mac Minis selling out, alternatives are documented
- Doc references existing community resources (getopenclaw.ai, getclawkit.com) where appropriate

---

## 5. Implementation Steps (When Approved)

1. Add `PENDING_SHORT_TERM` section to [pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md) (or append to PENDING_OPTIONAL)
2. Insert task ST1 with ID, status, description, spec links
3. Update "Last synced" and "Next focus" if needed
4. (Later) Implement the doc per product-scope — either extend OPENCLAW.md or create OPENCLAW_HARDWARE.md

---

## 6. CL4R1T4S / Local-First Notes

- **Convention-first:** OPENCLAW.md and REQUIREMENTS.md already exist; extend rather than create new structure
- **Local-first:** Hardware choice affects local inference (Ollama, vLLM); doc should clarify cloud API vs local model trade-offs (cost, privacy)
- **Bounded revision:** Doc is a single artifact; 1–2 revision rounds sufficient before publish

---

## 7. Decision for User

**Before implementing:**

1. **Section:** Prefer `PENDING_SHORT_TERM` (new) or `PENDING_OPTIONAL` (existing)?
2. **Deliverable location:** Extend OPENCLAW.md (Option A) or create OPENCLAW_HARDWARE.md (Option B)?

