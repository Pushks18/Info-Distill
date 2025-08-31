from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data_collection import TechArticleSearch
from classifier import ContentClassifier
from summarizer import Summarizer
import tools

# --- App Setup ---
app = FastAPI()
searcher = TechArticleSearch()
classifier = ContentClassifier()
summarizer = Summarizer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    prompt: str
    recipient_email: str
    date_filter: str = "w"

# --- API Endpoint ---
@app.post("/api/process")
async def process_request_endpoint(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Orchestrates the entire workflow: search, classify, create a GDoc, and email the link.
    """
    try:
        # 1. Search for and scrape full article content
        articles = await searcher.search(request.prompt, request.date_filter)
        if not articles:
            return {"status": "success", "articles": [], "message": "No articles found."}

        # 2. Score each article's relevance (but don't filter)
        for article in articles:
            article['relevance_score'] = classifier.evaluate_relevance(
                article['full_content'], request.prompt
            )

        # 3. Sort articles by score (most relevant first)
        sorted_articles = sorted(articles, key=lambda x: x['relevance_score'], reverse=True)
        
        # 4. Create and send the report in the background
        def create_and_send_report():
            # Use all sorted articles for the report
            doc_content = tools.create_document_from_articles(sorted_articles, request.prompt)
            
            try:
                # Use the gdoc function, not the old one
                doc_url = tools.add_content_to_gdoc(doc_content, f"AI Report - {request.prompt}")
                subject = f"Your AI-Generated Report on '{request.prompt.title()}'"
                # Use the new email function that sends a link
                tools.send_email_with_link(doc_url, subject, request.recipient_email)
            except Exception as e:
                print(f"Error in background task: {e}")

        background_tasks.add_task(create_and_send_report)

        # 5. Return ALL sorted articles to the frontend immediately
        return {
            "status": "success",
            "articles": sorted_articles,
            "message": f"Found {len(sorted_articles)} articles. A report is being generated and sent to {request.recipient_email}."
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}