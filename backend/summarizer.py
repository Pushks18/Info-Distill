import os
import httpx

class Summarizer:
    def __init__(self):
        self.api_token = os.getenv("HF_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        print("✅ Summarizer configured to use Hugging Face Inference API.")

    def summarize_in_points(self, text: str) -> str:
        if not self.api_token or not text:
            return "No content to summarize."

        prompt = f"Summarize the following text into 5 distinct bullet points:\n\n{text[:2048]}"
        
        payload = {
            "inputs": prompt,
            "parameters": {"min_length": 50, "max_length": 200},
        }

        try:
            response = httpx.post(self.api_url, headers=self.headers, json=payload, timeout=25.0)
            response.raise_for_status()
            result = response.json()
            return result[0]['summary_text']
        except Exception as e:
            print(f"❌ Error during API summarization: {e}")
            return "Failed to generate summary."