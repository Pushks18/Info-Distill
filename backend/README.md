# Industry Market Intelligence Dashboard

This project is a proof-of-concept dashboard that uses AI and NLP to ingest, process, and summarize industry-specific news from structured and unstructured sources. It enables Schneider Electric teams (or similar industrial stakeholders) to track energy, industrial, business, and government-related insights filtered by geography and theme relevance.

## 🌟 Features

- RSS feed ingestion for energy, industrial, business, and government news
- NLP-powered keyword extraction and summarization
- Article relevance scoring using hybrid keyword and semantic similarity models
- Region-based filtering using MSA mapping from city mentions
- Interactive Streamlit dashboard with customizable filters

## 🛠️ Project Structure

```plaintext
.
├── app.py                 # Streamlit frontend application
├── data_collection.py    # RSS feed ingestion and initial processing
├── msa_mapping.py        # Fuzzy matching cities to MSA using CSV + spaCy NER
├── relevance_model.py    # Keyword + semantic vector-based relevance scoring
├── nlp_processor.py      # Summarization, keyword extraction, preprocessing
├── llm_generator.py      # Integration with OpenAI LLMs (optional for summaries)
├── city_to_msa_mapping.csv
├── rss_sources.json      # Curated industry-relevant RSS feeds
├── requirements.txt
└── README.md
