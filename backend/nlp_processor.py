import pandas as pd
import re

# This dictionary defines your "themes". We have updated it to focus on
# computer science topics like AI, Data Science, and Web Development.
THEME_DEFINITIONS = {
    "Artificial Intelligence & Machine Learning": [
        "Artificial Intelligence", "AI", "Machine Learning", "ML", "Deep Learning", "DL",
        "Neural Network", "LLM", "Large Language Model", "Generative AI", "Computer Vision",
        "Natural Language Processing", "NLP", "Reinforcement Learning"
    ],
    "Data Science & Big Data": [
        "Data Science", "Data Scientist", "Big Data", "Data Analysis", "Data Analytics",
        "Data Mining", "Data Visualization", "Hadoop", "Spark", "ETL"
    ],
    "Web Development": [
        "Web Development", "Frontend", "Backend", "Full-Stack", "JavaScript", "React",
        "Angular", "Vue", "Node.js", "API", "Web Assembly", "WASM"
    ],
    "Cloud Computing & DevOps": [
        "Cloud Computing", "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP",
        "DevOps", "CI/CD", "Docker", "Kubernetes", "Serverless", "Infrastructure as Code"
    ],
    "Cybersecurity": [
        "Cybersecurity", "Information Security", "InfoSec", "Malware", "Ransomware",
        "Phishing", "Vulnerability", "Data Breach", "Encryption", "Zero Trust"
    ],
    "Software Engineering Principles": [
        "Software Engineering", "Software Development", "Agile", "Scrum",
        "Object-Oriented Programming", "OOP", "Design Patterns", "Microservices", "Code Quality"
    ]
}

class MarketIntelligenceNLP:
    def __init__(self):
        """
        Initializes the NLP processor.
        (This is the setup method for the class, but it's empty for now).
        """
        pass

    def categorize_by_theme(self, articles_df: pd.DataFrame, all_keywords: list) -> (pd.DataFrame, dict):
        """
        Categorizes articles into predefined themes based on keywords.
        """
        if articles_df.empty:
            return pd.DataFrame(), {}

        # Prepare a single text column for efficient searching.
        articles_df['text_for_search'] = (
            articles_df['title'].fillna('') + " " + articles_df['summary'].fillna('')
        ).str.lower()

        # Helper function to check for keyword presence using word boundaries for accuracy.
        def contains_any_keyword(text, keywords):
            for kw in keywords:
                # \b ensures we match whole words only (e.g., "ai" doesn't match "train").
                pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                if re.search(pattern, text):
                    return True
            return False

        # --- Step 1: Filter for any relevant article ---
        # Keep only articles that contain at least one of our keywords of interest.
        relevant_articles_df = articles_df[
            articles_df['text_for_search'].apply(lambda x: contains_any_keyword(x, all_keywords))
        ].copy()

        if relevant_articles_df.empty:
            return pd.DataFrame(), {}

        # --- Step 2: Assign filtered articles to specific themes ---
        themes_with_articles = {}
        for theme_name, theme_keywords in THEME_DEFINITIONS.items():
            # Find articles that match the keywords for this specific theme.
            matching_articles = relevant_articles_df[
                relevant_articles_df['text_for_search'].apply(lambda x: contains_any_keyword(x, theme_keywords))
            ]

            if not matching_articles.empty:
                themes_with_articles[theme_name] = {
                    'keywords': theme_keywords,
                    'articles': matching_articles.copy()
                }

        return relevant_articles_df, themes_with_articles