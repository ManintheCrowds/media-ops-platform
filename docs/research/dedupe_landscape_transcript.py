"""Re-fetch YouTube transcript, dedupe caption-style repeats, re-run SCP; update repo_landscape_scp_run.json.

Requires: ``AI_TRENDS_DATA`` pointing at the ai_trends cache dir (see local-proto AI Trends docs).
Paths assume ``D:/software``, ``D:/local-proto``, ``D:/scp`` as in this workspace.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent / "local-proto" / "scripts"))
sys.path.insert(0, str(ROOT.parent / "scp" / "src"))

import ai_trends_mcp as m  # noqa: E402
from scp.scp_utils import run_pipeline  # noqa: E402

EXCERPTS = """
=== TRUSTGRAPH (README summary) ===
Context development platform; Workbench port 8888; Context Cores portable bundles; Cassandra Qdrant Pulsar; RAG DocumentRAG GraphRAG OntologyRAG; MCP integration.

=== CYBERGYM ===
Agent security eval; PoC server; large datasets; Apache-2.0.

=== GSD ===
Spec-driven discuss plan execute verify; .planning/ artifacts; MIT.

=== LEARN-CLAUDE-CODE ===
Harness teaching s01-s12; MIT.

=== MONEYPRINTERV2 ===
Social automation; AGPL-3.0; educational disclaimer.

=== MAESTRO ===
YAML E2E mobile web; Apache-2.0.
"""


def strip_tags(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", t).strip()


def dedupe_adjacent_word_chunks(words: list[str], min_k: int = 2, max_k: int = 150) -> list[str]:
    """Collapse immediate repeated runs: ... A A ... -> ... A ... (A is k words)."""
    i = 0
    out: list[str] = []
    n = len(words)
    while i < n:
        matched = False
        upper = min(max_k, (n - i) // 2)
        for k in range(upper, min_k - 1, -1):
            if i + 2 * k <= n and words[i : i + k] == words[i + k : i + 2 * k]:
                out.extend(words[i : i + k])
                i += 2 * k
                matched = True
                break
        if not matched:
            out.append(words[i])
            i += 1
    return out


def dedupe_consecutive_identical_words(words: list[str]) -> list[str]:
    out: list[str] = []
    for w in words:
        if out and out[-1] == w:
            continue
        out.append(w)
    return out


def dedupe_word_passes(words: list[str], max_rounds: int = 24) -> list[str]:
    """Alternate chunk collapse and identical-word collapse until stable."""
    w = words
    for _ in range(max_rounds):
        n0 = len(w)
        w = dedupe_consecutive_identical_words(w)
        w = dedupe_adjacent_word_chunks(w)
        if len(w) == n0:
            break
    return w


def dedupe_consecutive_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    prev: str | None = None
    kept: list[str] = []
    for p in parts:
        s = p.strip()
        if not s:
            continue
        if s == prev:
            continue
        kept.append(s)
        prev = s
    return " ".join(kept)


def dedupe_youtube_body(clean_flat: str) -> tuple[str, dict]:
    words = clean_flat.split()
    before = len(words)
    w2 = dedupe_word_passes(words)
    after_words = len(w2)
    text = " ".join(w2)
    text = dedupe_consecutive_sentences(text)
    meta = {
        "words_before": before,
        "words_after_dedupe": after_words,
        "chars_after": len(text),
    }
    return text, meta


def main() -> None:
    raw = json.loads(m.fetch_youtube_captions("sWc7mkhITIo", False))
    tr = raw.get("transcript") or ""
    clean = strip_tags(tr)
    deduped, dedupe_meta = dedupe_youtube_body(clean)
    deduped = deduped[:50000]

    combined = (
        EXCERPTS.strip()
        + "\n\n=== YOUTUBE sWc7mkhITIo (deduped excerpt, cap 50k chars) ===\n"
        + deduped
    )

    out = run_pipeline(combined, sink="llm_context", options={})
    rep = {
        "blocked": out.get("blocked"),
        "tier": out.get("report", {}).get("tier"),
        "risk_score": out.get("report", {}).get("risk_score"),
        "result_preview": (out.get("result") or "")[:2000],
    }

    payload = {
        "dedupe": dedupe_meta,
        "scp_meta": rep,
        "combined_len": len(combined),
    }
    out_path = Path(__file__).resolve().parent / "repo_landscape_scp_run.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), **payload["dedupe"], "scp": rep}, indent=2))


if __name__ == "__main__":
    main()
