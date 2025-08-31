# Setup Instructions for Industry Market Intelligence Dashboard

This guide walks you through the steps to install, configure, and run the project locally.

## 🔧 Prerequisites

Ensure you have the following installed:

- Python 3.9 or above
- pip
- (Optional) virtualenv or venv for isolated environments

## Step 1 - Create and Activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate  # For Linux/macOS

# On Windows:
# venv\Scripts\activate

## Step 2 - Install Required Dependencies
pip install -r requirements.txt

## Step 3 - Set Up Environment Variables
touch .env

OPENAI_API_KEY=your_openai_api_key
## Do not share your .env file. Add .env to your .gitignore.

## Step 4 - Run the Streamlit Dashboard
streamlit run app.py
