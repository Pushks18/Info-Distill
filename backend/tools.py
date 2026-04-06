import os
from arcadepy import Arcade
from dotenv import load_dotenv

load_dotenv()

# --- Initialize Arcade Client ---
ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
USER_ID = os.getenv("ARCADE_USER_ID")

if not all([ARCADE_API_KEY, USER_ID]):
    raise ValueError("ARCADE_API_KEY and ARCADE_USER_ID must be set in the .env file.")

client = Arcade(api_key=ARCADE_API_KEY)

# Helper function to authorize and run tools
def authorize_and_run_tool(tool_name, input, user_id):
    # Start the authorization process
    auth_response = client.tools.authorize(
        tool_name=tool_name,
        user_id=user_id,
    )

    # If the authorization is not completed, print the authorization URL and wait for the user to authorize the app.
    # Tools that do not require authorization will have the status "completed" already.
    if auth_response.status != "completed":
        print(f"Click this link to authorize {tool_name}:\n{auth_response.url}.\nThe process will continue once you have authorized the app.")
        client.auth.wait_for_completion(auth_response.id)

    # Run the tool
    return client.tools.execute(tool_name=tool_name, input=input, user_id=user_id)

# --- Tool Definitions ---

def create_document_from_articles(articles: list, keywords: str) -> str:
    """Formats a list of articles into a beautifully formatted document."""
    print("📄 Creating document content...")
    if not articles:
        return "No articles were found for the given keywords."

    doc_content = f"Tech Article Summary: {keywords.title()}\n\n"
    doc_content += "AI Powered Article Intelligence Report\n\n"
    doc_content += "----------------------------------------\n\n"

    for i, article in enumerate(articles, 1):
        doc_content += f"{i}. Article: {article.get('title', 'No Title')}\n"
        doc_content += f"   Source: {article.get('source', 'N/A')}\n"
        doc_content += f"   Link: {article.get('link', 'N/A')}\n"
        relevance_score = article.get('relevance_score', 'N/A')
        confidence = article.get('relevance_confidence', 'N/A')
        doc_content += f"   Relevance Score: {relevance_score}\n"
        doc_content += f"   Scoring Confidence: {confidence}\n"
        doc_content += f"   Summary: {article.get('snippet', 'No summary available.')}\n\n"
        doc_content += "----------------------------------------\n\n"
    
    print("✅ Document content created.")
    return doc_content

def add_content_to_gdoc(content: str, file_name: str = "AI Intelligence Report") -> str:
    """
    Creates a new Google Doc with the provided text content and returns its URL.
    """
    if not USER_ID:
        return "Error: ARCADE_USER_ID is not set in the .env file."
    print(f"TOOL CALLED: Creating Google Doc titled '{file_name}'...")
    try:
        result = authorize_and_run_tool(
            tool_name="GoogleDocs.CreateDocumentFromText",
            input={"title": file_name, "text_content": content},
            user_id=USER_ID,
        )

        # --- CORRECTED LOGIC ---
        if result.status == "success" and result.output:
            doc_url = result.output.value.get("documentUrl")
            if doc_url:
                print(f"✅ Google Doc created successfully: {doc_url}")
                return doc_url
        
        # If the above conditions aren't met, something went wrong.
        error_detail = result.output.value if hasattr(result, 'output') else 'No output detail.'
        print(f"❌ Arcade tool failed with status: {result.status}, detail: {error_detail}")
        return "Failed to create the Google Document."

    except Exception as e:
        print(f"ERROR: Arcade tool execution failed: {e}")
        return "Failed to create the Google Document due to an error."

def send_email_with_link(doc_link: str, subject: str, recipient: str):
    """Sends an email with a link to the generated document."""
    print(f"📧 Calling Arcade to send email to {recipient}...")
    email_body = f"Here is the AI-generated report you requested:\n\n{doc_link}"
    try:
        result = authorize_and_run_tool(
            tool_name="Gmail.SendEmail",
            input={"body": email_body, "subject": subject, "recipient": recipient},
            user_id=USER_ID,
        )
        if result.status == "success":
            print("✅ Email sent successfully!")
            return True
        else:
            error_detail = result.output if hasattr(result, 'output') else 'No output detail.'
            print(f"❌ Arcade tool failed with status: {result.status}, detail: {error_detail}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Arcade tool execution failed: {e}")
        return False