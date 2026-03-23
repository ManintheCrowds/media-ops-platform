---
name: verify-openatlas-audit
overview: Verify which reported audit findings are now fixed in OpenAtlas and identify remaining gaps with concrete follow-up steps.
todos:
  - id: verify-survey
    content: Verify survey validation and limits are implemented in API + schema.
    status: completed
  - id: verify-alignment-gate
    content: Verify current alignment secret gate behavior and assess exposure risk.
    status: completed
  - id: verify-admin-role
    content: Verify admin role enforcement source and trust assumptions.
    status: completed
  - id: verify-brainmap
    content: Verify brain-map secret handling and bounded JSON read/parse safeguards.
    status: completed
  - id: report-status
    content: Produce completion status matrix with evidence and prioritized remaining actions.
    status: completed
isProject: false
---

# OpenAtlas Audit Verification Plan

## Goal

Confirm completion status of the reported critic/security/agent-native findings in `D:/portfolio-harness/OpenAtlas` using static code review only (no code changes).

## Verification Scope

- Check survey input validation and limits in API layer.
- Check alignment-context API gate behavior across envs.
- Check admin authorization strategy and trust boundary.
- Check brain-map secret handling and response safety controls.
- Check capabilities manifest and route parity expectations.

## Files Reviewed

- [D:/portfolio-harness/OpenAtlas/src/app/api/survey/route.ts](D:/portfolio-harness/OpenAtlas/src/app/api/survey/route.ts)
- [D:/portfolio-harness/OpenAtlas/src/lib/survey/schemas.ts](D:/portfolio-harness/OpenAtlas/src/lib/survey/schemas.ts)
- [D:/portfolio-harness/OpenAtlas/src/lib/alignment-context/api-auth.ts](D:/portfolio-harness/OpenAtlas/src/lib/alignment-context/api-auth.ts)
- [D:/portfolio-harness/OpenAtlas/src/lib/alignment-context/admin-auth.ts](D:/portfolio-harness/OpenAtlas/src/lib/alignment-context/admin-auth.ts)
- [D:/portfolio-harness/OpenAtlas/src/app/api/brain-map/graph/route.ts](D:/portfolio-harness/OpenAtlas/src/app/api/brain-map/graph/route.ts)
- [D:/portfolio-harness/OpenAtlas/src/app/api/capabilities/route.ts](D:/portfolio-harness/OpenAtlas/src/app/api/capabilities/route.ts)
- [D:/portfolio-harness/OpenAtlas/src/app/api/admin/alignment-context/route.ts](D:/portfolio-harness/OpenAtlas/src/app/api/admin/alignment-context/route.ts)
- [D:/portfolio-harness/OpenAtlas/src/app/api/admin/alignment-context/[id]/route.ts](D:/portfolio-harness/OpenAtlas/src/app/api/admin/alignment-context/[id]/route.ts)

## Completion Criteria

- Mark each reported issue as `completed`, `partially completed`, or `not completed` with evidence.
- Separate "report drift" (outdated findings) from still-open risks.
- Provide remediation order for remaining items only.

## Suggested Next Implementation Slice

1. Tighten alignment gate for non-production internet-exposed hosts with explicit env control.
2. Replace string equality with timing-safe compare for secrets.
3. Harden admin role source (claims/DB policy-backed) if metadata mutability risk exists.
4. Add size guard for brain-map file parse path and optional lightweight rate limiting for survey.

