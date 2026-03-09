---
name: Identity Context v2 Schema
overview: Extend the identity context schema to v2 with stakeholders, interdependency matrix, value hierarchy, contexts, and temporal anchors—enabling matrices of interdependency for alignment.
status: resolved
priority: 1
phase: wire
resolved_at: "2026-03-08"
todos: []
isProject: false
---

# Identity Context v2 Schema Extension

## Scope

Add a v2 schema and template that capture stakeholders, interdependency, value conflicts, contexts, and temporal anchors. Preserve v1 compatibility: existing `identity_context.json` files remain valid; v2 fields are additive.

---

## 1. Schema: `identity_context.v2.json`

**Location:** [D:\alignment-seed\schema\identity_context.v2.json](D:\alignment-seed\schema\identity_context.v2.json)

**Version:** `"2.0"` in document; schema validates `^1\.0$|^2\.0$`.

**New / extended properties:**


| Section                  | Fields                                                                                  | Purpose                                             |
| ------------------------ | --------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `stakeholders`           | `id`, `name`, `type`, `roles[]`, `obligations[]`, `value_refs[]`, `priority`, `context` | Who is affected; accountability; relationship types |
| `interdependency_matrix` | `depends_on_me[]`, `i_depend_on[]`, `accountable_to[]`                                  | Relational self; network view                       |
| `value_hierarchy`        | `conflicts[]` with `a`, `b`, `rule`                                                     | Resolution when values conflict                     |
| `contexts`               | `id`, `name`, `stakeholder_priority[]`, `value_emphasis[]`                              | Situated self; per-context priorities               |
| `temporal`               | `as_of`, `evolving_toward`                                                              | Narrative self; temporal anchors                    |


**Stakeholder `type` enum:** `primary_relationship`, `community`, `institution`, `future_self`, `other`.

**Backward compatibility:** All v2-specific fields optional. Documents with `version: "1.0"` validated by v1 schema; `version: "2.0"` by v2 schema. v2 schema includes all v1 required fields plus optional v2 blocks.

---

## 2. Template: `identity_context.example.json`

**Location:** [D:\alignment-seed\templates\identity_context.example.json](D:\alignment-seed\templates\identity_context.example.json)

- Set `version` to `"2.0"`.
- Add example `stakeholders` (e.g. family, community).
- Add example `interdependency_matrix`.
- Add example `value_hierarchy.conflicts` (e.g. cooperation vs no_harm).
- Add example `contexts` (e.g. work, family, creative).
- Add example `temporal` block.

---

## 3. Capture Script: `capture_identity_context.ps1`

**Location:** [D:\alignment-seed\scripts\capture_identity_context.ps1](D:\alignment-seed\scripts\capture_identity_context.ps1)

- Detect schema version from existing file or prompt user (v1 vs v2).
- If v2: add interactive prompts for stakeholders, interdependency_matrix, value_hierarchy, contexts, temporal.
- Preserve existing v1 capture flow when upgrading or when user chooses v1.
- Output `version: "2.0"` when v2 capture is used.

---

## 4. Analyze Script: `analyze_alignment.ps1`

**Location:** [D:\alignment-seed\scripts\analyze_alignment.ps1](D:\alignment-seed\scripts\analyze_alignment.ps1)

- When `identity_context.json` exists and `version` is `"2.0"`:
  - Add to summary: `Stakeholders: N`, `Contexts: N`, `Value conflicts (resolved): N`.
- Keep existing v1 summary behavior (communities count) for v1 files.

---

## 5. Documentation: `IDENTITY_CONTEXT.md`

**Location:** [D:\alignment-seed\docs\IDENTITY_CONTEXT.md](D:\alignment-seed\docs\IDENTITY_CONTEXT.md)

- Add "Schema versions" section: v1 vs v2, migration path.
- Add table for new v2 fields.
- Add "Contextualizing the Self" section (relational, narrative, situated).
- Add "Integration with ALIGNMENT_SURFACE" (how identity_context feeds org-intent, escalation).

---

## 6. AGENTS.md

**Location:** [D:\alignment-seed\docs\AGENTS.md](D:\alignment-seed\docs\AGENTS.md)

- Update "For identity_context" to mention v2 schema and template.
- Keep data boundary: do not read `data/`; use templates for structure.

---

## File Summary


| File                                      | Action                |
| ----------------------------------------- | --------------------- |
| `schema/identity_context.v2.json`         | Create (new schema)   |
| `templates/identity_context.example.json` | Update to v2 example  |
| `scripts/capture_identity_context.ps1`    | Extend for v2 capture |
| `scripts/analyze_alignment.ps1`           | Extend summary for v2 |
| `docs/IDENTITY_CONTEXT.md`                | Extend with v2 docs   |
| `docs/AGENTS.md`                          | Minor update          |


---

## Schema Snippet (v2 additions)

```json
{
  "stakeholders": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["id", "name", "type"],
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "type": { "enum": ["primary_relationship", "community", "institution", "future_self", "other"] },
        "roles": { "type": "array", "items": { "type": "string" } },
        "obligations": { "type": "array", "items": { "type": "string" } },
        "value_refs": { "type": "array", "items": { "type": "string" } },
        "priority": { "type": "integer", "minimum": 1 },
        "context": { "type": "string" }
      }
    }
  },
  "interdependency_matrix": {
    "type": "object",
    "properties": {
      "depends_on_me": { "type": "array", "items": { "type": "string" } },
      "i_depend_on": { "type": "array", "items": { "type": "string" } },
      "accountable_to": { "type": "array", "items": { "type": "string" } }
    }
  },
  "value_hierarchy": {
    "type": "object",
    "properties": {
      "conflicts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["a", "b", "rule"],
          "properties": {
            "a": { "type": "string" },
            "b": { "type": "string" },
            "rule": { "type": "string" }
          }
        }
      }
    }
  },
  "contexts": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["id", "name"],
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "stakeholder_priority": { "type": "array", "items": { "type": "string" } },
        "value_emphasis": { "type": "array", "items": { "type": "string" } }
      }
    }
  },
  "temporal": {
    "type": "object",
    "properties": {
      "as_of": { "type": "string", "format": "date-time" },
      "evolving_toward": { "type": "string" }
    }
  }
}
```

---

## Migration Path

- Existing `data/identity_context.json` (v1): unchanged; continues to validate against v1 schema.
- To upgrade: add v2 fields manually or re-run capture script with v2 option.
- No breaking changes to v1 files.

