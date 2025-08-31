import os
import httpx

class ContentClassifier:
    def __init__(self):
        self.api_token = os.getenv("HF_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        print("✅ Classifier configured to use Hugging Face Inference API.")

    def evaluate_relevance(self, text: str, prompt: str) -> float:
        if not self.api_token or not text or not prompt:
            return 0.0
        
        payload = {
            "inputs": text[:1024],
            "parameters": {"candidate_labels": [prompt]},
        }
        
        try:
            response = httpx.post(self.api_url, headers=self.headers, json=payload, timeout=20.0)
            response.raise_for_status()
            result = response.json()
            score = result['scores'][0]
            print(f"📄 Evaluated article with relevance score: {score:.2f}")
            return score
        except Exception as e:
            print(f"❌ Error during API classification: {e}")
            return 0.0