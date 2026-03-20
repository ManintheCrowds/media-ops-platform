---
name: DECIDE-SIM automation backlog
overview: Deferred work — skill, CLI wrapper, and MCP tools to support research and testing with DECIDE-SIM (and related eval hygiene) without running heavy jobs inside OpenAtlas or OpenHarness core.
todos:
  - id: skill-decide-sim-eval
    content: Add portfolio-harness .cursor/skills/decide-sim-eval/SKILL.md — when to run, provenance, SCP on excerpts, human gate for API keys; link gap analysis + TOOL_SAFEGUARDS
    status: pending
  - id: cli-wrapper
    content: Thin CLI wrapper — invoke DECIDE-SIM clone path, env check, optional --dry-run; no secrets in repo
    status: pending
  - id: mcp-readonly
    content: MCP read-only tools first — list_runs, get_summary_metrics from sanitized directory; no ungated shell
    status: pending
  - id: repo-choice
    content: Design pass — place MCP next to scp vs local-proto vs new package; document in decision-log
    status: pending
isProject: false
---

# DECIDE-SIM automation (deferred)

**Source:** [promptfoo_vs_DECIDE_SIM_gap_analysis.md](../docs/research/promptfoo_vs_DECIDE_SIM_gap_analysis.md), [DECIDE-SIM harness brainstorm](../../../portfolio-harness/docs/brainstorms/2026-03-20-decide-sim-stack-integration-brainstorm.md).

**Non-goals:** Running the sim inside OpenAtlas; vendoring full upstream repo into openharness.

**Acceptance (when implemented):** Human-gated API use; SCP on any log text sent to LLM; read-only MCP surface before any execution tools.
