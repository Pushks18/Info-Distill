import json
import os
import re
from collections import Counter
from openai import OpenAI

class ContentClassifier:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if self.client:
            print(f"✅ Classifier configured to use OpenAI ({self.model}).")
        else:
            print("⚠️ Warning: OPENAI_API_KEY not found. Falling back to keyword relevance.")

    def evaluate_relevance(self, text: str, prompt: str) -> float:
        result = self.evaluate_relevance_with_confidence(text, prompt)
        return result["score"]

    def evaluate_relevance_with_confidence(self, text: str, prompt: str) -> dict:
        if not text or not prompt:
            return {"score": 0.0, "confidence": 0.0, "reason": "Missing prompt or text."}

        prompt_tokens = self._extract_tokens(prompt)
        content_tokens = self._extract_tokens(text)
        prompt_terms = self._build_terms(prompt_tokens)
        content_term_counts = self._build_content_term_counts(content_tokens)

        if not prompt_terms:
            return {"score": 0.0, "confidence": 0.0, "reason": "No usable prompt terms."}

        matched_terms = [term for term in prompt_terms if content_term_counts.get(term, 0) > 0]
        matched_terms_count = len(matched_terms)
        total_terms_count = len(prompt_terms)
        coverage = matched_terms_count / total_terms_count

        matched_occurrences = sum(content_term_counts.get(term, 0) for term in matched_terms)
        total_content_terms = max(len(content_tokens), 1)
        density = matched_occurrences / total_content_terms
        normalized_density = min(density / 0.2, 1.0)

        confidence = round(max(0.0, min(0.75 * coverage + 0.25 * normalized_density, 1.0)), 2)
        top_matched_terms = sorted(matched_terms, key=lambda t: content_term_counts.get(t, 0), reverse=True)[:10]

        # Primary path: OpenAI relevance scoring with structured JSON output.
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a strict relevance evaluator. "
                                "Return valid JSON only."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                "Evaluate how relevant the ARTICLE is to the QUERY.\n\n"
                                f"QUERY: {prompt}\n\n"
                                f"ARTICLE:\n{text[:4000]}\n\n"
                                "Return JSON with this schema:\n"
                                "{"
                                "\"score\": number from 0.0 to 1.0, "
                                "\"confidence\": number from 0.0 to 1.0, "
                                "\"reason\": short string under 25 words"
                                "}"
                            ),
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=120,
                    timeout=20,
                )
                payload = json.loads(response.choices[0].message.content or "{}")
                score = float(payload.get("score", 0.0))
                score = max(0.0, min(score, 1.0))
                reason = str(payload.get("reason", "No reason provided."))
                print(
                    f"📄 Relevance={score:.2f} | Confidence={confidence:.2f} "
                    f"(coverage={coverage:.2f}, density={normalized_density:.2f})"
                )
                return {
                    "score": score,
                    "confidence": confidence,
                    "reason": reason,
                    "matched_terms_count": matched_terms_count,
                    "total_terms_count": total_terms_count,
                    "matched_terms": top_matched_terms,
                }
            except Exception as e:
                print(f"❌ Error during OpenAI classification: {e}")

        # Fallback relevance = keyword match coverage
        score = round(max(0.0, min(coverage, 1.0)), 2)
        print(
            f"📄 Fallback relevance={score:.2f} | Confidence={confidence:.2f} "
            f"({matched_terms_count}/{total_terms_count})"
        )
        return {
            "score": score,
            "confidence": confidence,
            "reason": "Keyword-overlap score used due to model error.",
            "matched_terms_count": matched_terms_count,
            "total_terms_count": total_terms_count,
            "matched_terms": top_matched_terms,
        }

    def _extract_tokens(self, text: str) -> list[str]:
        stopwords = {
            "a", "an", "the", "and", "or", "but", "if", "then", "than", "so", "to",
            "of", "in", "on", "for", "by", "with", "at", "from", "into", "about",
            "as", "is", "are", "was", "were", "be", "been", "being", "it", "its",
            "this", "that", "these", "those", "you", "your", "we", "our", "they",
            "their", "he", "she", "his", "her", "them", "will", "would", "can",
            "could", "should", "do", "does", "did", "have", "has", "had", "not"
        }
        normalized = re.sub(r"[-_/]", " ", text.lower())
        tokens = re.findall(r"[a-z0-9]{2,}", normalized)
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def _build_terms(self, tokens: list[str]) -> list[str]:
        unigrams = tokens
        bigrams = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
        deduped = list(dict.fromkeys(unigrams + bigrams))
        return deduped

    def _build_content_term_counts(self, tokens: list[str]) -> Counter:
        unigram_counts = Counter(tokens)
        bigram_counts = Counter(
            f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)
        )
        counts = Counter()
        counts.update(unigram_counts)
        counts.update(bigram_counts)
        return counts