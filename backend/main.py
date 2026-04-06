from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from data_collection import TechArticleSearch
from summarizer import Summarizer
from llm_generator import NewsletterGenerator
from rag_pipeline import RAGPipeline
import tools
import asyncio
from datetime import datetime
import os

# --- App Setup ---
app = FastAPI()
searcher = TechArticleSearch()
summarizer = Summarizer()
generator = NewsletterGenerator()
rag_pipeline = RAGPipeline()

# Simple in-memory cache for search results
search_cache = {}

# Semaphore to limit concurrent searches
search_semaphore = asyncio.Semaphore(5)  # Allow up to 5 concurrent searches

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    prompt: str
    recipient_email: str = ""
    date_filter: str = "w"

class CreateDocRequest(BaseModel):
    selected_articles: list[dict]  # List of article objects
    recipient_email: str

# --- API Endpoint ---
@app.post("/api/process")
async def process_request_endpoint(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Orchestrates the entire workflow: search, classify, create a GDoc, and email the link.
    """
    try:
        cache_key = f"{request.prompt}_{request.date_filter}"
        if cache_key in search_cache:
            articles = search_cache[cache_key]
        else:
            # 1. Search for and scrape full article content
            async with search_semaphore:
                articles = await searcher.search(request.prompt, request.date_filter)
            search_cache[cache_key] = articles

        if not articles:
            return {"status": "success", "articles": [], "message": "No articles found."}

        # 2. Score each article's relevance through retrieval-augmented evidence chunks
        rag_scores = rag_pipeline.score_articles(request.prompt, articles)
        for i, article in enumerate(articles):
            relevance = rag_scores[i] if i < len(rag_scores) else {}
            article['relevance_score'] = relevance.get("score", 0.0)
            article['relevance_confidence'] = relevance.get("confidence", 0.0)
            article['relevance_reason'] = relevance.get("reason", "")
            article['matched_terms_count'] = relevance.get("matched_terms_count", 0)
            article['total_terms_count'] = relevance.get("total_terms_count", 0)
            article['matched_terms'] = relevance.get("matched_terms", [])
            article['rag_evidence'] = relevance.get("evidence_chunks", [])

        # 3. Sort articles by score (most relevant first)
        sorted_articles = sorted(articles, key=lambda x: x['relevance_score'], reverse=True)
        
        # 4. Create and send the report in the background
        def create_and_send_report():
            # Use all sorted articles for the report
            doc_content = tools.create_document_from_articles(sorted_articles, request.prompt)
            
            try:
                # Use the gdoc function, not the old one
                doc_url = tools.add_content_to_gdoc(doc_content, f"AI Report - {request.prompt}")
                if request.recipient_email:
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
            "message": f"Found {len(sorted_articles)} articles ranked by relevance."
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stream-newsletter")
async def stream_newsletter(prompt: str, date_filter: str = "w"):
    """
    Streams the generated newsletter for the given prompt.
    """
    async def generate():
        try:
            cache_key = f"{prompt}_{date_filter}"
            if cache_key in search_cache:
                articles = search_cache[cache_key]
            else:
                # 1. Search for articles
                async with search_semaphore:
                    articles = await searcher.search(prompt, date_filter)
                search_cache[cache_key] = articles

            if not articles:
                yield "data: No articles found for this prompt.\n\n"
                return

            # 2. Score relevance with RAG evidence
            rag_scores = rag_pipeline.score_articles(prompt, articles)
            for i, article in enumerate(articles):
                relevance = rag_scores[i] if i < len(rag_scores) else {}
                article['relevance_score'] = relevance.get("score", 0.0)
                article['relevance_confidence'] = relevance.get("confidence", 0.0)
                article['relevance_reason'] = relevance.get("reason", "")
                article['matched_terms_count'] = relevance.get("matched_terms_count", 0)
                article['total_terms_count'] = relevance.get("total_terms_count", 0)
                article['matched_terms'] = relevance.get("matched_terms", [])
                article['rag_evidence'] = relevance.get("evidence_chunks", [])

            # 3. Sort
            sorted_articles = sorted(articles, key=lambda x: x['relevance_score'], reverse=True)

            # 4. Prepare data for LLM (convert to df-like)
            import pandas as pd
            articles_df = pd.DataFrame(sorted_articles)

            # 5. Stream the newsletter
            theme_keywords = prompt.split()  # simple split
            for chunk in generator.generate_newsletter_section_stream(articles_df, theme_keywords, prompt):
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.01)  # small delay for streaming effect

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/create-doc")
async def create_doc_endpoint(request: CreateDocRequest, background_tasks: BackgroundTasks):
    """
    Creates a Google Doc with selected articles, including short and comprehensive summaries.
    """
    try:
        if not request.selected_articles:
            return {"status": "error", "message": "No articles selected."}

        # Generate summaries for each selected article
        doc_content = "AI Generated Article Intelligence Report\n\n"
        doc_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        doc_content += f"Recipient: {request.recipient_email}\n"
        doc_content += f"Articles selected: {len(request.selected_articles)}\n\n"
        doc_content += "----------------------------------------\n\n"

        for i, article in enumerate(request.selected_articles, 1):
            doc_content += f"{i}. Article: {article.get('title', 'No Title')}\n"
            doc_content += f"   Source: {article.get('source', 'N/A')}\n"
            doc_content += f"   Published: {article.get('date', 'N/A')}\n"
            doc_content += f"   Relevance Score: {article.get('relevance_score', 0):.2f} ({int(article.get('relevance_score', 0) * 100)}%)\n"
            doc_content += f"   Scoring Confidence: {article.get('relevance_confidence', 0):.2f}\n"
            doc_content += f"   Link: {article.get('link', 'N/A')}\n\n"

            # Generate short summary
            short_summary = await generate_short_summary(article.get('full_content', article.get('snippet', '')))
            doc_content += "   Executive Snapshot:\n"
            doc_content += f"{short_summary}\n\n"

            # Generate comprehensive summary
            comprehensive_summary = await generate_comprehensive_summary(article.get('full_content', article.get('snippet', '')))
            doc_content += "   Deep Dive:\n"
            doc_content += f"{comprehensive_summary}\n\n"

            doc_content += "----------------------------------------\n\n"

        # Create Google Doc
        file_name = f"AI Article Report - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        doc_url = tools.add_content_to_gdoc(doc_content, file_name)

        if doc_url:
            # Send email in background
            def send_email():
                try:
                    subject = "Your AI-Generated Article Intelligence Report"
                    body = f"Here is your comprehensive article intelligence report:\n\n{doc_url}"
                    tools.send_email_with_link(doc_url, subject, request.recipient_email)
                except Exception as e:
                    print(f"Error sending email: {e}")

            background_tasks.add_task(send_email)

            return {
                "status": "success",
                "doc_url": doc_url,
                "message": f"Document created successfully. Email sent to {request.recipient_email}."
            }
        else:
            return {"status": "error", "message": "Failed to create Google Doc."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/article-detail")
async def article_detail_endpoint(article: dict):
    """
    Returns detailed information about an article with a 5-point summary.
    """
    try:
        content = article.get('full_content', article.get('snippet', ''))
        if not content:
            return {"status": "error", "message": "No content available for this article."}
        
        # Generate 5-point summary
        five_points = await generate_five_point_summary(content)
        
        return {
            "status": "success",
            "title": article.get('title', 'No Title'),
            "source": article.get('source', 'N/A'),
            "link": article.get('link', '#'),
            "date": article.get('date', 'N/A'),
            "relevance_score": article.get('relevance_score', 0),
            "snippet": article.get('snippet', 'No summary available.'),
            "five_point_summary": five_points
        }
    except Exception as e:
        print(f"Error generating article detail: {e}")
        return {"status": "error", "message": str(e)}

async def generate_short_summary(content: str) -> str:
    """Generate a short summary using the summarizer with fallback to text extraction."""
    if not content:
        return "No content available for summary."
    
    try:
        rag_context = rag_pipeline.retrieve_from_text(
            "key findings outcomes metrics decisions", content, top_k=3
        )
        result = summarizer.summarize_in_points(content[:5000], rag_context=rag_context)
        if result and "failed" not in result.lower() and "unavailable" not in result.lower():
            return result
    except Exception as e:
        print(f"Error in primary summarizer: {e}")
    
    # Fallback: Extract first paragraph or key sentences
    try:
        sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 20]
        if sentences:
            summary = '. '.join(sentences[:3]) + '.'
            return summary if len(summary) > 20 else content[:300] + "..."
        return content[:300] + "..."
    except:
        return "Summary: " + content[:200] + "..."

async def generate_comprehensive_summary(content: str) -> str:
    """Generate a comprehensive summary using the LLM with fallback to text processing."""
    if not content:
        return "No content available for comprehensive summary."
    
    try:
        if not generator.client:
            raise RuntimeError("OpenAI client unavailable.")
        rag_context = rag_pipeline.retrieve_from_text(
            "comprehensive technical summary insights impacts evidence", content, top_k=4
        )

        system_prompt = (
            "You are a technical intelligence analyst. "
            "Write crisp, specific analysis in markdown."
        )
        user_prompt = (
            "Create a high-quality comprehensive summary of this article.\n\n"
            "Output format:\n"
            "1) One-paragraph synopsis (3-4 sentences)\n"
            "2) 'Key Insights:' with exactly 4 bullets\n"
            "3) 'Why It Matters:' with exactly 2 bullets\n\n"
            "Rules:\n"
            "- Do not use markdown symbols like #, *, or **.\n"
            "- Be concrete and specific.\n"
            "- Include named entities and measurable outcomes when present.\n"
            "- Avoid generic filler.\n\n"
            f"EVIDENCE CHUNKS:\n{chr(10).join(rag_context) if rag_context else 'N/A'}\n\n"
            f"ARTICLE:\n{content[:7000]}"
        )

        response = generator.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=650,
            temperature=0.2,
            timeout=20
        )
        summary = response.choices[0].message.content.strip()
        if summary and len(summary) > 20:
            return summary
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
    
    # Fallback: Extract key sentences from content
    try:
        sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 30]
        if len(sentences) > 3:
            return '. '.join(sentences[:5]) + '. This article covers important developments and insights in the topic.'
        return content[:400] + "..." if len(content) > 400 else content
    except:
        return content[:400] + "..." if len(content) > 400 else content

async def generate_five_point_summary(content: str) -> list:
    """Generate a 5-point summary as a list with fallback to text extraction."""
    if not content:
        return ["No content available."]
    
    try:
        if not generator.client:
            raise RuntimeError("OpenAI client unavailable.")
        rag_context = rag_pipeline.retrieve_from_text(
            "five key takeaways critical facts concrete points", content, top_k=4
        )

        system_prompt = "You are an expert analyst. Extract exactly 5 sharp, non-overlapping takeaways."
        user_prompt = (
            "Extract 5 key points from this article content.\n\n"
            f"EVIDENCE CHUNKS:\n{chr(10).join(rag_context) if rag_context else 'N/A'}\n\n"
            f"ARTICLE:\n{content[:4000]}"
        )
        
        response = generator.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.2,
            timeout=15
        )
        
        # Parse the response into 5 points
        text = response.choices[0].message.content.strip()
        points = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 5]
        if points and len(points) >= 3:
            return points[:5]
    except Exception as e:
        print(f"Error with OpenAI five-point summary: {e}")
    
    # Fallback: Extract sentences as key points
    try:
        sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 25]
        if len(sentences) >= 5:
            return sentences[:5]
        elif len(sentences) >= 3:
            # Pad with additional summary sentences
            return sentences + [
                "Article highlights emerging trends and industry developments.",
                "Further reading recommended for comprehensive understanding."
            ]
        else:
            return [
                content[:100] + "...",
                "This article discusses important aspects of the topic.",
                "Multiple perspectives and insights are covered.",
                "Key trends and developments are highlighted.",
                "Recommended for further research and analysis."
            ]
    except:
        return [
            content[:100] + "...",
            "Article contains valuable information on the topic.",
            "Multiple perspectives covered.",
            "Emerging trends discussed.",
            "Further research recommended."
        ]