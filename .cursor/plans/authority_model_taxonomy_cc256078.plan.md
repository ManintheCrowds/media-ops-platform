---
name: Authority Model Taxonomy
overview: Create an authority-model taxonomy document, extend CHAOS_BITCOIN_MAPPING with an authority-model row and FIPS reference, tie authority requirements to risk tiers, refine org-intent.bitcoin-inspired.json with a risk-tiered authority principle, and document FIPS as the reference for low-stakes coordination-heavy designs.
todos: []
isProject: false
---

# Authority Model Taxonomy and Risk-Tiered Authority Integration

## Context

The FIPS observation (BitDevs MPLS Seminar 36) distinguishes *human authority without cryptographic certainty* (mesh routing + Nostr identities) from our desire for *cryptographic authority over AI systems*. This plan captures that distinction in docs, extends the Chaos-Bitcoin mapping, ties authority to existing risk tiers, and refines org-intent.

---

## 1. Create Authority-Model Taxonomy

**New file:** [docs/AUTHORITY_MODEL_TAXONOMY.md](D:\portfolio-harness\docs\AUTHORITY_MODEL_TAXONOMY.md)

**Content structure:**

- **Definitions**
  - **Cryptographic authority:** Proof-based, verifiable; private key = proof of ownership; signed actions; capability tokens.
  - **Social/coordination authority:** Consensus, reputation, human gates; identity may be crypto (Nostr keypair) but routing/peering decisions are not proof-based.
- **Spectrum table** (FIPS vs Bitcoin vs Fedimint vs AI framework):


| System       | Identity            | Authority                     | Verification           |
| ------------ | ------------------- | ----------------------------- | ---------------------- |
| FIPS         | Nostr keypairs      | Social (peering, routing)     | Reputation, gossip     |
| Bitcoin      | Private key         | Cryptographic                 | On-chain proof         |
| Fedimint     | Pubkey + AuthModule | Cryptographic                 | Capability tokens, BFT |
| AI framework | Signed identity     | Cryptographic for high-stakes | hb-4, capability scope |


- **When each applies:** Low-stakes coordination (social OK) vs high-stakes (spend, PII, irreversible) requiring crypto proof.
- **FIPS as reference:** Link to [github.com/jmcorgan/fips](https://github.com/jmcorgan/fips); cite BitDevs notes [2026-03-10-bitdevs-mpls-seminar-36.md](D:\portfolio-harness\docs\bitcoin_observations\2026-03-10-bitdevs-mpls-seminar-36.md). FIPS = low-stakes, coordination-heavy; acceptable authority model when failure modes are bounded.
- **Cross-references:** [CHAOS_BITCOIN_MAPPING.md](D:\portfolio-harness\docs\CHAOS_BITCOIN_MAPPING.md), [org-intent.bitcoin-inspired.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.bitcoin-inspired.json), [FRONTIER_OPERATIONS_MANIFESTO.md](D:\portfolio-harness\docs\FRONTIER_OPERATIONS_MANIFESTO.md).

---

## 2. Extend CHAOS_BITCOIN_MAPPING

**File:** [docs/CHAOS_BITCOIN_MAPPING.md](D:\portfolio-harness\docs\CHAOS_BITCOIN_MAPPING.md)

**Changes:**

- Add a new row after the existing table (or as a dedicated "Authority model" section) that maps the authority-model contrast:


| Chaos Failure            | Bitcoin Solution    | FIPS Analogue                                                      | Agent Mitigation                                                                   |
| ------------------------ | ------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Authority conversational | Private key = proof | Nostr identity + social routing; coordination without crypto proof | Cryptographic owner binding for spend/PII; human gates for low-stakes coordination |


- Add a "See also" link to `AUTHORITY_MODEL_TAXONOMY.md` and to the FIPS section in the BitDevs seminar notes.

---

## 3. Tie Authority to Risk Tiers

**File:** [docs/AUTHORITY_MODEL_TAXONOMY.md](D:\portfolio-harness\docs\AUTHORITY_MODEL_TAXONOMY.md) (section within the new doc)

**Risk-tier mapping** (align with [.cursorrules](D:\portfolio-harness.cursorrules) Risk-Tiered Operations):


| Risk Tier    | Authority Model              | Rationale                                                             |
| ------------ | ---------------------------- | --------------------------------------------------------------------- |
| **Low**      | Social/coordination OK       | Reversible; no spend, no PII; e.g. routing, coordination, docs        |
| **Medium**   | Human gate + signed identity | Git tag + backup; two reviewers; identity verified                    |
| **High**     | Cryptographic proof required | Full backup; lead approval; capability tokens, signed actions         |
| **Critical** | Full proof chain             | Multiple backups; team consensus; Fedimint BFT, on-chain verification |


- Add a short "Authority by risk tier" section that references this table and the existing `.cursorrules` risk-tier definitions (Low: Git commit; Medium: tag + backup; High: full backup + lead; Critical: multiple backups + consensus).

---

## 4. Refine org-intent.bitcoin-inspired.json

**File:** [org-intent-spec/examples/org-intent.bitcoin-inspired.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.bitcoin-inspired.json)

**Changes:**

- Add a new value (or principle) to `values` array:
  - `"Prefer cryptographic authority for high-stakes actions (spend, PII, irreversible); social/coordination authority acceptable for low-stakes coordination when failure modes are bounded"`
- Add a new `delegation_rule`:

```json
  {
    "principle": "authority_by_risk",
    "decision_boundary": "For spend, PII, or irreversible actions: require cryptographic proof. For low-stakes coordination: social authority (human gates) acceptable per AUTHORITY_MODEL_TAXONOMY.",
    "action": "proceed"
  }
  

```

- Update `meta.modified` to current date.
- Optionally add a `references` or `see_also` field if the org-intent schema supports it; otherwise document the link in `meta.note` or a comment.

---

## 5. Document FIPS as Low-Stakes Reference

**Locations:**

- **AUTHORITY_MODEL_TAXONOMY.md:** Dedicated subsection "FIPS as Reference for Low-Stakes Design" — when to use FIPS-style authority (coordination, mesh routing, reversible decisions), when not (spend, PII, irreversible).
- **BitDevs seminar notes:** The FIPS section in [2026-03-10-bitdevs-mpls-seminar-36.md](D:\portfolio-harness\docs\bitcoin_observations\2026-03-10-bitdevs-mpls-seminar-36.md) already exists. Add a line under "Status" or "Relevance":
  - `- **Authority reference:** See AUTHORITY_MODEL_TAXONOMY.md; FIPS = reference for low-stakes, coordination-heavy designs.`

---

## 6. Update Cross-References

- **CHAOS_BITCOIN_MAPPING.md:** Add `AUTHORITY_MODEL_TAXONOMY.md` to "See also."
- **BITCOIN_AGENT_CAPABILITIES.md:** Add a brief mention of authority-model taxonomy in the "org-intent and hard_boundaries" section or a new "Authority model" subsection, with link to `AUTHORITY_MODEL_TAXONOMY.md`.
- **AGENT_ENTRY_INDEX.md** (if it exists and lists Bitcoin docs): Add `AUTHORITY_MODEL_TAXONOMY.md` to the index.

---

## File Summary


| Action | File                                                              |
| ------ | ----------------------------------------------------------------- |
| Create | `docs/AUTHORITY_MODEL_TAXONOMY.md`                                |
| Edit   | `docs/CHAOS_BITCOIN_MAPPING.md`                                   |
| Edit   | `org-intent-spec/examples/org-intent.bitcoin-inspired.json`       |
| Edit   | `docs/bitcoin_observations/2026-03-10-bitdevs-mpls-seminar-36.md` |
| Edit   | `docs/BITCOIN_AGENT_CAPABILITIES.md`                              |


---

## Verification

- `AUTHORITY_MODEL_TAXONOMY.md` defines both authority types and maps FIPS, Bitcoin, Fedimint, AI framework.
- Risk-tier table is consistent with `.cursorrules` Risk-Tiered Operations.
- CHAOS_BITCOIN_MAPPING has the new authority row and cross-link.
- org-intent JSON is valid and includes the new value and delegation_rule.
- All cross-references resolve.

