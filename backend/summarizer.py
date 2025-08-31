from transformers import pipeline

class Summarizer:
    def __init__(self):
        try:
            # Using a distilled BART model for a good balance of speed and quality
            self.summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6"
            )
            print("✅ Summarization model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load summarization model: {e}")
            self.summarizer = None

    def summarize_in_points(self, text: str) -> str:
        """
        Generates a 5-point summary for the given text.
        """
        if not self.summarizer or not text:
            return "No content to summarize."
        
        # We create a custom prompt to guide the model's output
        prompt = f"""
        Summarize the following text into 5 distinct bullet points. Each point should be a complete sentence.

        Text: "{text[:2048]}"

        Summary in 5 points:
        """
        
        try:
            # Generate a longer summary first
            summary_list = self.summarizer(
                prompt,
                min_length=50,
                max_length=200,
                do_sample=False
            )
            return summary_list[0]['summary_text']
        except Exception as e:
            print(f"❌ Error during summarization: {e}")
            return "Failed to generate summary."