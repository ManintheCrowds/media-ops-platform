---
name: Operator profile private archive
overview: Establish a gitignored canonical store under local-proto for the full ChatGPT-derived operator profile (YAML), add a small OpenAtlas alignment_context item containing a summary plus pointers to the local path (your chosen pattern), and wire privacy guardrails so nothing sensitive lands in tracked repos.
todos:
  - id: ignore-paths
    content: Add local-proto/.gitignore rules for private/operator-profile/ (or private/**)
    status: completed
  - id: canonical-yaml
    content: Create gitignored andrew_schumacher.operator_profile.v1.yaml; merge sections; fix name/id consistency
    status: completed
  - id: openatlas-item
    content: Create one OpenAtlas alignment_context item via alignment-context-cli (summary + path pointer; tags; draft→active)
    status: completed
  - id: verify-no-leak
    content: Run git status from local-proto and portfolio-harness; confirm no private files staged
    status: in_progress
isProject: false
---

