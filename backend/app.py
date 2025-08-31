import streamlit as st
import pandas as pd
import re
import html
import os
from datetime import datetime, timedelta

from data_collection import MarketIntelligenceCollector
from nlp_processor import MarketIntelligenceNLP
from llm_generator import NewsletterGenerator 
from tools import add_content_to_document, send_email

# --- App Configuration ---
st.set_page_config(page_title="AI Tech Intelligence System", layout="wide")


# --- Function Definitions ---
def generate_search_query(keywords: list) -> str:
    """
    Creates a sophisticated search query from a list of keywords.
    Date logic is now handled by the API call directly.
    """
    if not keywords:
        return ""
    
    exact_phrases = [f'"{kw}"' for kw in keywords if len(kw.split()) > 1]
    single_words = [kw for kw in keywords if len(kw.split()) == 1]
    query_parts = exact_phrases + single_words
    keyword_query = f"({' OR '.join(query_parts)})"
    
    # Refined query for more relevance
    full_query = f"{keyword_query} AND ('university research funding' OR 'federal research grants' OR 'R&D policy') (site:.gov OR site:.edu OR site:.org)"
    return full_query

def normalize_bullet(line):
    return re.sub(r"^\s*[\d]+[\.\)]\s*", "", line).strip()


# --- Initialization ---
@st.cache_resource
def init_components():
    collector = MarketIntelligenceCollector()
    nlp_processor = MarketIntelligenceNLP()
    generator = NewsletterGenerator()
    return collector, nlp_processor, generator

@st.cache_data
def load_keywords():
    try:
        return pd.read_csv("keywords.csv")
    except FileNotFoundError:
        st.error("`keywords.csv` not found. Please create it.")
        return pd.DataFrame({'theme': [], 'keyword': []})

collector, nlp_processor, generator = init_components()
keywords_df = load_keywords()

if 'report_summaries' not in st.session_state:
    st.session_state.report_summaries = []
if 'last_report_url' not in st.session_state:
    st.session_state.last_report_url = None


# --- UI: Header and Custom CSS ---
st.markdown("""
    <style>html, body, [class*="css"] {font-family: 'Segoe UI', sans-serif;}</style>
""", unsafe_allow_html=True)
st.markdown("""
    <div style="background-color:#0E1117;padding:1.5rem 1rem;border-radius:8px;margin-bottom:1rem;">
        <h2 style="color:white;margin-bottom:0.2rem;">⚡ Federal R&D Intelligence System</h2>
        <p style="color:white;">Your AI-powered assistant for tracking latest technological trends.</p>
    </div>
""", unsafe_allow_html=True)


# --- UI: Sidebar Controls ---
st.sidebar.markdown("## 🧠 Intelligence Dashboard")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Search Controls")

all_themes = [""] + keywords_df['theme'].unique().tolist()
selected_theme = st.sidebar.selectbox("Select a Search Theme (Preset)", options=all_themes)

default_keywords = keywords_df[keywords_df['theme'] == selected_theme]['keyword'].tolist() if selected_theme else []
selected_keywords = st.sidebar.multiselect("Customize Keywords", options=keywords_df['keyword'].tolist(), default=default_keywords)

date_filter_options = {"Past Week": "w", "Past Month": "m", "Past Day": "d", "Any Time": None}
selected_date_filter_label = st.sidebar.selectbox("Select Date Range", options=list(date_filter_options.keys()))
selected_date_filter = date_filter_options[selected_date_filter_label]

if st.sidebar.button("Search", type="primary"):
    if selected_keywords:
        with st.spinner("Searching the web for the latest intelligence..."):
            search_query = generate_search_query(selected_keywords)
            # Pass the date filter directly to the collector
            st.session_state.articles_df = collector.search_web_and_extract(
                search_query, 
                search_type="news",
                date_filter=selected_date_filter
            )
            st.session_state.report_summaries = []
            st.session_state.last_report_url = None
    else:
        st.warning("Please select a theme or keywords to start a search.")
        st.session_state.articles_df = pd.DataFrame()


# --- UI: Sidebar Report Builder ---
st.sidebar.markdown("---")
st.sidebar.subheader("📝 Report Builder")
selected_count = len(st.session_state.report_summaries)
st.sidebar.write(f"**{selected_count}** theme summaries selected.")

if st.sidebar.button("Clear Selections"):
    st.session_state.report_summaries = []
    st.rerun()

generate_button = st.sidebar.button("Generate Single Report", disabled=(selected_count == 0))


# --- Main Page Display ---
if 'articles_df' in st.session_state and not st.session_state.articles_df.empty:
    st.markdown("---")
    report_title = st.text_input("**Enter a title for your final report:**", "Summary of articles")

    full_df = st.session_state.articles_df
    themed_articles, themes = nlp_processor.categorize_by_theme(full_df, selected_keywords)

    if not themed_articles.empty:
        for theme_name, theme_details in themes.items():
            articles_in_theme = theme_details['articles']
            if articles_in_theme.empty:
                continue

            with st.expander(f"**{theme_name}** ({len(articles_in_theme)} articles)", expanded=True):
                with st.spinner(f"Generating intelligence briefing for {theme_name}..."):
                    intelligence_briefing = generator.generate_newsletter_section(articles_in_theme, theme_details['keywords'])
                
                st.markdown(f"<p style='background-color:#F0F2F6; color:#31333F; padding:1rem; border-radius:8px;'>{intelligence_briefing}</p>", unsafe_allow_html=True)
                
                if st.button(f"➕ Add '{theme_name}' Summary to Report", key=f"add_{theme_name}"):
                    if not any(item['theme'] == theme_name for item in st.session_state.report_summaries):
                        st.session_state.report_summaries.append({
                            "theme": theme_name,
                            "content": intelligence_briefing
                        })
                        st.toast(f"Added '{theme_name}' summary to the report builder!")
                        st.rerun()

                st.markdown("---")
                
                st.markdown("##### Source Articles for this Briefing")
                for _, article in articles_in_theme.iterrows():
                    title = article['title']
                    link = article['link']
                    published = article.get('published', 'Date N/A')
                    source = article.get('source', 'Source N/A')
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 10px;">
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;"><b>{title}</b></a>
                        <br>
                        <small>Source: {source} | Published: {published}</small>
                    </div>
                    """, unsafe_allow_html=True)

    else:
        st.info("No articles found for the selected criteria. Try broadening your search.")
else:
    st.info("Select a theme from the sidebar and click 'Search' to begin.")


# --- Logic for Buttons (Direct Function Calls) ---
if generate_button:
    with st.sidebar:
        with st.spinner("Consolidating summaries and creating your document..."):
            final_report_content = ""
            for item in st.session_state.report_summaries:
                final_report_content += f"## Intelligence Briefing: {item['theme']}\n\n"
                final_report_content += f"{item['content']}\n\n---\n\n"
            
            response = add_content_to_document(content=final_report_content, file_name=report_title)
            st.success(response)
            
            if "Success!" in response:
                st.session_state.last_report_content = final_report_content
                st.session_state.last_report_title = report_title
                st.session_state.last_report_url = response
            
            st.session_state.report_summaries = []

if st.session_state.last_report_url:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📧 Email This Report")
    
    st.sidebar.info("Report created! You can now email it.")
    
    recipient_email = st.sidebar.text_input("Recipient's Email Address", "pushks2015@gmail.com")
    
    if st.sidebar.button("Send Email"):
        with st.sidebar:
            with st.spinner("Sending the email..."):
                email_response = send_email(
                    content=st.session_state.last_report_content,
                    subject=st.session_state.last_report_title,
                    recipient=recipient_email
                )
                st.success(email_response)
                
                st.session_state.last_report_url = None