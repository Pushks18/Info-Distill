import os
from openai import OpenAI

class Summarizer:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if self.client:
            print(f"✅ Summarizer configured to use OpenAI ({self.model}).")
        else:
            print("⚠️ Warning: OPENAI_API_KEY not found. Summary quality will degrade.")

    def summarize_in_points(self, text: str, rag_context: list[str] | None = None) -> str:
        if not text:
            return "No content to summarize."

        if not self.client:
            return "Summary unavailable: OPENAI_API_KEY is missing or invalid."

        try:
            context_block = "\n".join(rag_context or [])
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert research summarizer. "
                            "Produce concise, concrete bullet points."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Summarize this article in exactly 5 bullet points.\n"
                            "Constraints:\n"
                            "- Do not use markdown symbols like #, *, or **.\n"
                            "- Each bullet is one sentence.\n"
                            "- Max 22 words per bullet.\n"
                            "- Include specific entities, metrics, or outcomes when available.\n"
                            "- Avoid hype and generic phrasing.\n\n"
                            f"EVIDENCE CHUNKS (retrieved context):\n{context_block if context_block else 'N/A'}\n\n"
                            f"ARTICLE:\n{text[:5000]}"
                        ),
                    },
                ],
                temperature=0.2,
                max_tokens=280,
                timeout=25,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"❌ Error during OpenAI summarization: {e}")
            return "Failed to generate summary."