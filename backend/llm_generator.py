import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

load_dotenv()

class NewsletterGenerator:
    def __init__(self):
        # Initializes the connection to the OpenAI API
        api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            print("⚠️ Warning: OpenAI API key not found.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def generate_newsletter_section_stream(self, articles_df, theme_keywords, query_text=None):
        """
        Generates a themed summary of articles using streaming.
        Yields chunks of the response.
        """
        if not self.client:
            yield self._generate_simple_summary(articles_df, theme_keywords)
            return
        
        if articles_df.empty:
            yield "No articles were found for this theme."
            return
        
        # Prepare a concise summary of the top articles for the prompt
        articles_text = ""
        for _, row in articles_df.head(5).iterrows():
            articles_text += f"- Title: {row['title']}\n"
            articles_text += f"  Summary: {str(row.get('snippet', row.get('full_content', '')))[:250]}...\n\n"
            evidence = row.get("rag_evidence", [])
            if evidence:
                articles_text += f"  Retrieved Evidence: {str(evidence[0])[:260]}...\n\n"
        
        system_prompt = (
            "You are a senior technology analyst writing an executive briefing. "
            "Prioritize signal over noise and be specific."
        )
        
        user_prompt = f"""
        Analyze the following articles related to the theme "{', '.join(theme_keywords)}".
        Original query: "{query_text or ', '.join(theme_keywords)}".

        Articles:
        {articles_text}
        
        Write a concise newsletter section with this exact structure:
        ## Weekly Intelligence Brief
        - 5 bullets, one sentence each, each starting with a strong action verb.
        - Include named entities (company/lab/project), what changed, and why it matters.
        - Mention at least one practical implication for builders, operators, or investors.
        - Avoid vague claims, filler, or generic "important development" wording.
        - Max 28 words per bullet.
        """
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=420,
                temperature=0.3,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except APIError as e:
            print(f"❌ OpenAI API error: {e}")
            yield f"LLM analysis failed due to an API error. Falling back to a basic summary:\n{self._generate_simple_summary(articles_df, theme_keywords)}"

    def _generate_simple_summary(self, articles_df, theme_keywords):
        """Fallback method to generate a basic summary if the LLM call fails or is disabled."""
        if articles_df.empty:
            return "No articles found for this theme."
        
        summary = f"This analysis covers {len(articles_df)} articles related to '{theme_keywords[0]}'.\n"
        summary += "Key developments appear in the following articles:\n"
        
        for _, article in articles_df.head(3).iterrows():
            summary += f"- {article['title']}\n"
        
        summary += f"\nThese articles suggest notable activity and key developments in this technology sector."
        
        return summary