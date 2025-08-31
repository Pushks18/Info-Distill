import pandas as pd
import spacy
from rapidfuzz import process

# --- Load Models and Data ---
# This section runs only once when the module is imported, making it efficient.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Downloading...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

try:
    # Load city-to-MSA mapping from CSV
    city_msa_df = pd.read_csv("city_to_msa_mapping.csv")
    city_to_msa = dict(zip(city_msa_df["City"], city_msa_df["MSA"]))
    all_cities = list(city_to_msa.keys())
    print("✅ MSA mapping loaded successfully.")
except FileNotFoundError:
    print("⚠️ `city_to_msa_mapping.csv` not found. MSA extraction will be disabled.")
    city_to_msa = {}
    all_cities = []


def extract_msa_region(text: str) -> str:
    """
    Extracts a U.S. Metropolitan Statistical Area (MSA) from text.

    This function uses spaCy for Named Entity Recognition (NER) to find
    geopolitical entities (GPEs) and then uses fuzzy matching to map them
    to a known list of U.S. cities and their corresponding MSAs.

    Args:
        text: The input text (e.g., an article summary).

    Returns:
        The name of the matched MSA or "Uncategorized" if no match is found.
    """
    if not all_cities or not isinstance(text, str):
        return "Uncategorized"

    doc = nlp(text)

    for ent in doc.ents:
        # We only care about geopolitical entities.
        if ent.label_ != "GPE":
            continue

        gpe = ent.text.strip()

        # --- Filtering to reduce false positives ---

        # Filter 1: Skip vague or overly short terms.
        if len(gpe) < 4 or gpe.lower() in {"territory", "region", "province", "district", "area", "zone", "north", "south", "east", "west"}:
            continue

        # Filter 2: Skip if the context suggests a non-US location.
        if any(country in gpe.lower() for country in ["australia", "india", "china", "europe", "asia", "africa"]):
            continue

        # Filter 3: Skip if the GPE is part of an organization or person's name (e.g., "Bank of America", "Paris Hilton").
        if any(tok.ent_type_ in {"ORG", "PRODUCT", "PERSON", "WORK_OF_ART"} for tok in ent.subtree):
            continue
        
        # --- Fuzzy Matching ---
        # Find the best city match for the extracted GPE.
        match = process.extractOne(gpe, all_cities, score_cutoff=70)

        if match:
            # If a match with a high confidence score is found, return its MSA.
            city, score, _ = match
            # print(f"Found match: {gpe} -> {city} (Score: {score})") # Uncomment for debugging
            return city_to_msa.get(city, "Uncategorized")

    # If no suitable GPE is found after checking all entities, return "Uncategorized".
    return "Uncategorized"