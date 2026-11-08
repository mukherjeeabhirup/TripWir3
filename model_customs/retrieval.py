"""Small auditable local paper corpus; retrieval occurs only on tool invocation."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "papers.json"
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset("a an and are as at be by for from in is it of on or that the to with".split())


def _tokens(text: str) -> list[str]:
    return [token for token in _TOKEN.findall(text.lower()) if token not in _STOP]


@lru_cache(maxsize=1)
def _load_corpus() -> tuple[list[dict[str, Any]], str]:
    raw = CORPUS_PATH.read_bytes()
    docs = json.loads(raw)
    if not isinstance(docs, list) or not all(isinstance(d, dict) and {"id", "title", "url", "summary", "keywords"} <= d.keys() for d in docs):
        raise ValueError("Invalid local paper corpus")
    return docs, hashlib.sha256(raw).hexdigest()


def search_papers(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Return deterministic BM25-ranked original paraphrases, not full papers.

    This function does not call an embedding provider or choose when retrieval
    is needed. The Nemotron orchestrator must explicitly invoke this tool.
    Scores are lexical relevance, never evidence of model compromise.
    """
    if not isinstance(query, str) or len(query) > 2000:
        raise ValueError("Retrieval query must be a string of at most 2000 characters")
    if not isinstance(limit, int) or not 1 <= limit <= 5:
        raise ValueError("Retrieval limit must be between 1 and 5")
    terms = set(_tokens(query))
    if not terms:
        return []
    docs, digest = _load_corpus()
    tokenized = [_tokens(" ".join([doc["title"], " ".join(doc["keywords"]), doc["summary"]])) for doc in docs]
    counts = [Counter(tokens) for tokens in tokenized]
    avg_length = sum(map(len, tokenized)) / len(docs)
    ranked = []
    # Standard BM25 k1=1.5, b=.75; fixed for a tiny transparent local corpus.
    for doc, tokens, frequency in zip(docs, tokenized, counts):
        score = 0.0
        for term in sorted(terms):
            tf = frequency.get(term, 0)
            if not tf:
                continue
            document_frequency = sum(term in c for c in counts)
            idf = math.log(1 + (len(docs) - document_frequency + .5) / (document_frequency + .5))
            score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * len(tokens) / avg_length))
        if score > 0:
            ranked.append({**doc, "score": round(score, 6), "corpus_sha256": digest,
                           "content_type": "original_curated_paraphrase",
                           "retrieval_method": "local_bm25_k1_1.5_b_0.75"})
    return sorted(ranked, key=lambda d: (-d["score"], d["id"]))[:limit]


def chunks_from_results(results):
    """One curated-summary chunk per paper; scores rank documents, not confidence."""
    return [{'source_id':row['id'],'chunk_id':row['id']+':summary:'+hashlib.sha256(row['summary'].encode()).hexdigest()[:16],
             'text':row['summary'],'score':row['score'],'score_scope':'paper_title_keywords_summary',
             'url':row['url'],'corpus_sha256':row['corpus_sha256'],'content_type':'original_curated_paraphrase'} for row in results]
