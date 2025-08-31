# backend/classifier.py

from transformers import pipeline

class ContentClassifier:
    def __init__(self):
        """
        Initializes the Zero-Shot Classification pipeline.
        """
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            print("✅ Zero-shot classification model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load classification model: {e}")
            self.classifier = None

    def evaluate_relevance(self, text: str, prompt: str) -> float:
        """
        Evaluates how relevant a piece of text is to a given prompt.
        """
        if not self.classifier or not text or not prompt:
            return 0.0
        
        try:
            result = self.classifier(text[:1024], candidate_labels=[prompt])
            score = result['scores'][0]
            print(f"📄 Evaluated article with relevance score: {score:.2f}")
            return score
        except Exception as e:
            print(f"❌ Error during classification: {e}")
            return 0.0