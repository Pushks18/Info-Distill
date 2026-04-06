import math
import os
import re
from collections import Counter, defaultdict
from typing import Any

from openai import OpenAI


class RAGPipeline:
    """
    Lightweight in-memory RAG pipeline.
    - Retrieval: semantic (OpenAI embeddings) when available, lexical fallback otherwise.
    - Augmentation: returns top supporting chunks for ranking and generation prompts.
    """

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def score_articles(self, query: str, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not query or not articles:
            return []

        indexed = self._index_articles(articles)
        if not indexed:
            return []

        query_embedding = self._embed_texts([query])[0] if self.client else None
        query_terms = self._extract_terms(query)

        scored_chunks = []
        for row in indexed:
            chunk_score = self._score_chunk(query, query_embedding, query_terms, row)
            scored_chunks.append((chunk_score, row))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[: min(len(scored_chunks), 40)]
        grouped: dict[int, list[tuple[float, dict[str, Any]]]] = defaultdict(list)
        for score, row in top_chunks:
            grouped[row["article_idx"]].append((score, row))

        article_scores = []
        for idx, article in enumerate(articles):
            items = grouped.get(idx, [])
            if not items:
                article_scores.append(
                    {
                        "score": 0.0,
                        "confidence": 0.0,
                        "reason": "No supporting evidence chunk retrieved.",
                        "matched_terms_count": 0,
                        "total_terms_count": len(query_terms),
                        "matched_terms": [],
                        "evidence_chunks": [],
                    }
                )
                continue

            best = items[0][0]
            mean_top = sum(s for s, _ in items[:3]) / max(1, len(items[:3]))
            score = max(0.0, min(0.7 * best + 0.3 * mean_top, 1.0))
            confidence = max(0.0, min(0.6 * best + 0.4 * min(len(items) / 3, 1.0), 1.0))

            top_row = items[0][1]
            matched = self._matched_terms(query_terms, top_row["chunk_terms"])
            reason = (
                f"Top evidence chunk aligns with query intent. "
                f"Matched terms: {', '.join(matched[:4]) if matched else 'none'}."
            )
            article_scores.append(
                {
                    "score": round(score, 2),
                    "confidence": round(confidence, 2),
                    "reason": reason,
                    "matched_terms_count": len(matched),
                    "total_terms_count": len(query_terms),
                    "matched_terms": matched[:10],
                    "evidence_chunks": [r["chunk"] for _, r in items[:3]],
                }
            )
        return article_scores

    def retrieve_from_text(self, query: str, text: str, top_k: int = 4) -> list[str]:
        chunks = self._chunk_text(text)
        if not chunks:
            return []

        query_embedding = self._embed_texts([query])[0] if self.client else None
        query_terms = self._extract_terms(query)

        rows = []
        chunk_embeddings = self._embed_texts(chunks) if self.client else [None] * len(chunks)
        for i, chunk in enumerate(chunks):
            rows.append(
                {
                    "chunk": chunk,
                    "chunk_terms": self._extract_terms(chunk),
                    "embedding": chunk_embeddings[i],
                }
            )

        ranked = sorted(
            rows,
            key=lambda row: self._score_chunk(query, query_embedding, query_terms, row),
            reverse=True,
        )
        return [row["chunk"] for row in ranked[:top_k]]

    def _index_articles(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        all_chunks = []
        chunk_map = []
        for article_idx, article in enumerate(articles):
            source_text = article.get("full_content") or article.get("snippet") or ""
            for chunk in self._chunk_text(source_text):
                rows.append(
                    {
                        "article_idx": article_idx,
                        "chunk": chunk,
                        "chunk_terms": self._extract_terms(chunk),
                        "embedding": None,
                    }
                )
                all_chunks.append(chunk)
                chunk_map.append(len(rows) - 1)

        if self.client and all_chunks:
            embeddings = self._embed_texts(all_chunks)
            for i, emb in enumerate(embeddings):
                rows[chunk_map[i]]["embedding"] = emb
        return rows

    def _embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        if not self.client:
            return [None] * len(texts)
        try:
            response = self.client.embeddings.create(model=self.embedding_model, input=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"❌ Embedding error. Falling back to lexical retrieval: {e}")
            self.client = None
            return [None] * len(texts)

    def _score_chunk(
        self,
        query: str,
        query_embedding: list[float] | None,
        query_terms: list[str],
        row: dict[str, Any],
    ) -> float:
        lexical = self._lexical_score(query_terms, row["chunk_terms"])
        if query_embedding is None or row["embedding"] is None:
            return lexical

        semantic = self._cosine_similarity(query_embedding, row["embedding"])
        return max(0.0, min(0.7 * semantic + 0.3 * lexical, 1.0))

    def _lexical_score(self, query_terms: list[str], chunk_terms: list[str]) -> float:
        if not query_terms or not chunk_terms:
            return 0.0
        q = Counter(query_terms)
        c = Counter(chunk_terms)
        overlap = sum(min(q[t], c[t]) for t in q)
        return min(overlap / max(len(query_terms), 1), 1.0)

    def _matched_terms(self, query_terms: list[str], chunk_terms: list[str]) -> list[str]:
        chunk_set = set(chunk_terms)
        return [t for t in dict.fromkeys(query_terms) if t in chunk_set]

    def _extract_terms(self, text: str) -> list[str]:
        stop = {
            "a", "an", "the", "and", "or", "but", "for", "with", "that", "this",
            "from", "into", "about", "your", "their", "have", "has", "had", "are",
            "was", "were", "will", "would", "can", "could", "should", "not", "you",
        }
        words = re.findall(r"[a-z0-9]{3,}", text.lower())
        return [w for w in words if w not in stop]

    def _chunk_text(self, text: str, chunk_chars: int = 1100, overlap_chars: int = 180) -> list[str]:
        if not text:
            return []
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            return []
        if len(clean) <= chunk_chars:
            return [clean]

        chunks = []
        start = 0
        while start < len(clean):
            end = min(start + chunk_chars, len(clean))
            chunks.append(clean[start:end])
            if end == len(clean):
                break
            start = max(0, end - overlap_chars)
        return chunks

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return max(0.0, min(dot / (n1 * n2), 1.0))
