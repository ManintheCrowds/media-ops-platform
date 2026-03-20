---
name: OpenDataLoader integration gaps
overview: Close the harness gaps you listed by extending LangChainChatBot PDF ingest (provenance, optional JSON/citations, hybrid/OCR, sanitize), optionally upgrading Arc_Forge campaign_kb from pdfplumber to a configurable OpenDataLoader path, and documenting the OpenAtlas future hook—without reimplementing the upstream parser.
todos:
  - id: verify-langchain-loader
    content: "Spike: inspect langchain_opendataloader_pdf OpenDataLoaderPDFLoader __init__ and JSON output metadata shape"
    status: completed
  - id: phase-a-provenance-hybrid
    content: "Extend LangChainChatBot pdf_ingest: parser versions, sha in chunk metadata, optional sanitize + hybrid kwargs/env"
    status: completed
  - id: phase-a-citations
    content: Implement JSON/bbox path and metadata-preserving split or element Documents; update OPENDATALOADER_PDF.md
    status: completed
  - id: phase-a-tests
    content: Add minimal pytest for metadata and optional flags
    status: completed
  - id: phase-b-campaign-kb
    content: "Arc_Forge campaign_kb: config flag, refactor extract_pdf_sections, ODL backend + Document.metadata_json"
    status: completed
  - id: phase-c-openatlas-doc
    content: "OpenAtlas: short future-ingest note linking to harness SCP/provenance"
    status: completed
isProject: false
---

# OpenDataLoader PDF integration gaps — implementation plan

## Context (current state)

- **Harness note:** [portfolio-harness/docs/integrations/OPENDATALOADER_PDF.md](D:/portfolio-harness/docs/integrations/OPENDATALOADER_PDF.md)
- **LangChain bot:** [portfolio-harness/LangChainChatBot/pdf_ingest.py](D:/portfolio-harness/LangChainChatBot/pdf_ingest.py) uses `OpenDataLoaderPDFLoader` with `format=loader_format` (default `"markdown"`), SCP on `page_content`, SHA-256 in `pdf_files` for file paths only—no `opendataloader-pdf` / `langchain-opendataloader-pdf` version in metadata.
- **campaign_kb (Arc_Forge):** [Arc_Forge/campaign_kb/app/ingest/pdf_ingest.py](D:/Arc_Forge/campaign_kb/app/ingest/pdf_ingest.py) uses **pdfplumber** page-by-page; [Arc_Forge/campaign_kb/app/ingest/service.py](D:/Arc_Forge/campaign_kb/app/ingest/service.py) `ingest_pdfs` builds [Section](D:/Arc_Forge/campaign_kb/app/models.py) rows with `page_number` but no bbox. `Document.metadata_json` exists and is unused in this path.

Upstream APIs (for reference): `opendataloader_pdf.convert(...)` supports `sanitize`, `hybrid`, `hybrid_url`, `hybrid_mode`, etc. ([hybrid-mode docs](https://github.com/opendataloader-project/opendataloader-pdf/blob/main/content/docs/hybrid-mode.mdx)). The **LangChain loader** docs show `file_path`, `format`, `quiet`; **first implementation step** must confirm which kwargs `OpenDataLoaderPDFLoader` forwards to `convert()` (read installed `langchain_opendataloader_pdf` or its PyPI source). If the loader does not expose hybrid/sanitize, implement a small wrapper that calls `opendataloader_pdf.convert()` to a temp dir and maps output files into `Document`s, only for the advanced code path.

---

## Phase A — LangChainChatBot ([pdf_ingest.py](D:/portfolio-harness/LangChainChatBot/pdf_ingest.py))

**A1. Provenance (low risk)**  

- After successful load, set chunk/document metadata: `parser="opendataloader-pdf"`, `parser_version` from `importlib.metadata.version("opendataloader-pdf")` and `langchain_opendataloader_pdf` version (or single combined field).  
- Keep existing file `sha256` behavior; add the same hash into **chunk metadata** for retrieval/debug parity with the integration note.

**A2. Expose loader options (medium)**  

- Extend `ingest_pdf_paths(...)` with optional parameters aligned to upstream: at minimum `loader_format` (already), plus `sanitize: bool = False`, and hybrid-related args (`hybrid: str | None`, `hybrid_url`, `hybrid_mode`, `hybrid_fallback`, `hybrid_timeout`) **or** read from env (e.g. `OPENDATALOADER_HYBRID_URL`) so ops can run `opendataloader-pdf-hybrid --port 5002` separately without embedding a process manager in Python.  
- Document in [OPENDATALOADER_PDF.md](D:/portfolio-harness/docs/integrations/OPENDATALOADER_PDF.md): hybrid server must be running; JVM batching guidance unchanged.

**A3. Citations / JSON + bbox (medium, behavior-dependent)**  

- Spike: run loader with `format="json"` (or `"markdown,json"`) and inspect `Document.metadata` / `page_content` shape.  
- If metadata already carries `page number` / `bounding box` per document, pass them through after SCP and **before** `RecursiveCharacterTextSplitter`, or use a splitting strategy that preserves metadata (merge chunk metadata with bbox when splitting merges multiple elements—may require custom splitter or element-per-chunk for JSON mode).  
- If the loader returns one blob, parse JSON lines/objects and build LangChain `Document`s manually with metadata fields `page`, `bbox`, `element_type`.  
- Goal: optional code path `citation_mode=True` or `loader_format` including `json` that stores bbox/page on chunks for future UI—not necessarily perfect merge with character splitter on first iteration.

**A4. Sanitize vs SCP**  

- `sanitize=True` addresses **PII**; SCP addresses **injection**. Document the distinction in the integration note; wire `sanitize` as an optional flag (default `False` to avoid surprising redaction). Order: upstream sanitize → SCP on resulting text (confirm order with upstream semantics if both enabled).

**A5. Tests**  

- Add minimal tests (mock loader or small fixture PDF if CI allows JDK) for: metadata contains parser version; optional sanitize flag forwarded. Prefer pytest in `LangChainChatBot/tests/` if that pattern exists, else a small `test_pdf_ingest_metadata.py`.

**A6. Requirements**  

- [requirements.txt](D:/portfolio-harness/LangChainChatBot/requirements.txt): keep optional deps commented; note `[hybrid]` extra for `opendataloader-pdf` where relevant.

---

## Phase B — campaign_kb ([Arc_Forge/campaign_kb](D:/Arc_Forge/campaign_kb))

**B1. Strategy**  

- Keep **pdfplumber** as default (no new JVM dependency for existing deployments).  
- Add config-driven backend: e.g. `PDF_BACKEND=pdfplumber|opendataloader` in [app/config.py](D:/Arc_Forge/campaign_kb/app/config.py) plus optional hybrid URL / sanitize flags.

**B2. Implementation**  

- Refactor [pdf_ingest.py](D:/Arc_Forge/campaign_kb/app/ingest/pdf_ingest.py) into two extractors behind one interface `extract_pdf_sections(path) -> Iterable[dict]` with the same keys (`page_number`, `section_title`, `raw_text`, `normalized_text`) for `ingest_pdfs`.  
- OpenDataLoader path: use `opendataloader_pdf.convert()` to a temp directory with `format="markdown"` or structured output, map sections to the same payload shape; set `Document.metadata_json` with parser name/version and hybrid settings.  
- **Bbox:** [Section](D:/Arc_Forge/campaign_kb/app/models.py) has no per-section JSON column. **MVP:** store citation hints in `Document.metadata_json` (e.g. list of `{page, bbox}` keyed by section index) or add optional `metadata_json` on `Section` via Alembic migration if you need queryable per-section bbox—choose one in implementation to avoid duplicate truth.

**B3. Ops / Docker**  

- If OpenDataLoader is optional, document JDK + optional hybrid service in campaign_kb README; CI may stay on pdfplumber only.

---

## Phase C — OpenAtlas (docs only)

- Add a short subsection to an existing architecture doc (e.g. [OpenAtlas/docs/BRAIN_MAP_SCHEMA.md](D:/portfolio-harness/OpenAtlas/docs/BRAIN_MAP_SCHEMA.md) or a new `docs/ingest/UNTRUSTED_TEXT.md`) stating: future PDF → graph ingest should use the same **SCP + provenance** pattern as [OPENDATALOADER_PDF.md](D:/portfolio-harness/docs/integrations/OPENDATALOADER_PDF.md); no product code until scope exists.

---

## Dependency / risk notes


| Risk                                                       | Mitigation                                                               |
| ---------------------------------------------------------- | ------------------------------------------------------------------------ |
| LangChain loader missing hybrid kwargs                     | Fallback to direct `opendataloader_pdf.convert()` for advanced mode      |
| JSON + `RecursiveCharacterTextSplitter` splits across bbox | Start with element-level documents for JSON or custom splitter           |
| campaign_kb DB migration                                   | Defer bbox-on-Section until needed; use `Document.metadata_json` for MVP |
| Cross-repo work                                            | Phase A in **portfolio-harness**; Phase B in **Arc_Forge**               |


---

## Suggested order of execution

1. Verify `OpenDataLoaderPDFLoader` signature (spike).
2. Phase A1–A2 + docs.
3. Phase A3 (citations) as a follow-up once spike clarifies loader output.
4. Phase B when campaign_kb quality matters more than JVM weight.
5. Phase C doc pointer.

