from sentence_transformers import SentenceTransformer, util
from typing import List, Dict

class RelevanceScorer:
    def __init__(self, keyword_weights: Dict[str, float] = None):
        """
        Initializes the scorer by loading the SentenceTransformer model.

        Args:
            keyword_weights: A dictionary mapping keywords to specific weights.
        """
        # This model is lightweight and effective for semantic similarity tasks.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.keyword_weights = keyword_weights or {}

    def weighted_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculates a score based on the presence of weighted keywords."""
        score = 0.0
        text_lower = text.lower()
        for kw in keywords:
            # Default to a weight of 1.0 if not specified.
            weight = self.keyword_weights.get(kw.lower(), 1.0)
            if kw.lower() in text_lower:
                score += weight
        return score

    def semantic_score(self, theme_text: str, article_text: str) -> float:
        """
        Calculates a semantic similarity score using model embeddings.
        This captures contextual meaning beyond simple keyword matching.
        """
        # The model converts text into numerical vectors (embeddings).
        theme_embedding = self.model.encode(theme_text, convert_to_tensor=True)
        article_embedding = self.model.encode(article_text, convert_to_tensor=True)
        
        # Cosine similarity measures the angle between the two vectors.
        # A score of 1 means they are identical in meaning.
        cosine_score = util.cos_sim(theme_embedding, article_embedding)
        return float(cosine_score.item())

    def combined_score(self, article_text: str, theme_keywords: List[str]) -> float:
        """
        Creates a blended score from both keyword and semantic methods.
        This provides a more robust measure of relevance.
        """
        keyword_score = self.weighted_keyword_score(article_text, theme_keywords)
        
        # Create a single string from theme keywords for semantic comparison.
        theme_text = " ".join(theme_keywords)
        semantic_score_val = self.semantic_score(theme_text, article_text)
        
        # A weighted average gives more importance to direct keyword matches.
        return (0.6 * keyword_score) + (0.4 * semantic_score_val)