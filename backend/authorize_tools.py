import os
from arcadepy import Arcade
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
USER_ID = os.getenv("ARCADE_USER_ID")

# --- List of all tools your app will use ---
TOOLS_TO_AUTHORIZE = [
    "GoogleDocs.CreateDocumentFromText@4.0.0",
    "Gmail.SendEmail@3.0.0"  # Add the new Gmail tool here
]

# --- Authorization Flow ---
client = Arcade(api_key=ARCADE_API_KEY)

for tool_name in TOOLS_TO_AUTHORIZE:
    print(f"\n▶️  Attempting to authorize tool: {tool_name}...")
    
    # 1. Start the authorization process
    auth_response = client.tools.authorize(
        tool_name=tool_name,
        user_id=USER_ID,
    )

    # 2. If not already authorized, provide the link to click
    if auth_response.status != "completed":
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please authorize the tool.")
        print(f"Click this link to grant permission: {auth_response.url}")
        print("="*50 + "\n")

        # 3. Wait for you to complete the process in your browser
        auth_response = client.auth.wait_for_completion(auth_response)

    if auth_response.status == "completed":
        print(f"✅ Authorization successful for {tool_name}!")
    else:
        print(f"❌ Authorization failed for {tool_name} with status: {auth_response.status}")
        # Decide if you want to stop on failure or continue
        # raise Exception(f"Authorization failed for {tool_name}")

print("\nAll tools checked.")