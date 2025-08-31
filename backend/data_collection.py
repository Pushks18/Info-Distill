import os
import httpx
from dotenv import load_dotenv
import trafilatura # Import the library
import asyncio

load_dotenv()

class TechArticleSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found.")
        self.headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    async def search(self, query: str, date_filter: str = "w") -> list:
        """
        Searches Google News and then scrapes the full content of each article.
        """
        print(f"🔎 Searching for news about: '{query}'")
        api_url = "https://google.serper.dev/news"
        payload = {"q": query, "tbs": f"qdr:{date_filter}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=self.headers, json=payload)
                response.raise_for_status()
            
            initial_results = response.json().get("news", [])
            if not initial_results:
                return []

            # Scrape full content from each URL asynchronously
            async def scrape_content(article):
                async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                    try:
                        res = await client.get(article['link'])
                        article['full_content'] = trafilatura.extract(res.text)
                        return article
                    except Exception:
                        article['full_content'] = None
                        return article

            tasks = [scrape_content(article) for article in initial_results]
            full_articles = await asyncio.gather(*tasks)
            
            # Filter out articles where content extraction failed
            valid_articles = [art for art in full_articles if art['full_content']]
            print(f"✅ Scraped content from {len(valid_articles)} articles.")
            return valid_articles
            
        except Exception as e:
            print(f"❌ API search failed: {e}")
            return []