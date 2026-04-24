from backend.utils.text_helpers import *
from services.mapper_domain import detect_domain
from services.detector_subjects import extract_subjects

from services.extractor_content import extract_content
from services.extractor_data import extract_attributes
from backend.utils.utils import deduplicate_attributes

from services.search_service import fetch_search_results

from database.attribute_repository import insert_attribute


# ---- CONFIG ----
MAX_LINKS_PER_ENTITY = 7


# ---- INPUT ----
query = "iphone 15"


# ---- SETUP ----
domain = detect_domain(query)
subjects = extract_subjects(query)

print("Subjects:", subjects)

if not subjects:
    print("⚠️ No subjects detected. Using fallback.")
    subjects = [query]

seen_global = set()


# ---- PIPELINE ----
for subject in subjects:
    print(f"\n=== Processing: {subject} ===")

    # ---- SEARCH ----
    results = fetch_search_results(subject + " wikipedia", 5)

    urls = [r["url"] for r in results[:MAX_LINKS_PER_ENTITY]]

    print("Selected URLs:")
    for u in urls:
        print(" -", u)

    # ---- PROCESS EACH URL ----
    for url in urls:
        print(f"\nFetching: {url}")

        try:
            data = extract_content(url)
        except Exception as e:
            print("❌ Fetch failed:", e)
            continue

        text = data.get("text", "")
        print("Text length:", len(text))

        if len(text) < 200:
            print("⚠️ Skipping (too little content)")
            continue

        # ---- PREPROCESS ----
        cleaned = clean_text(text)
        sentences = split_into_sentences(cleaned)

        print("Sentence count:", len(sentences))

        # ---- EXTRACT ATTRIBUTES ----
        for s in sentences:
            attributes = extract_attributes(s, domain)
            attributes = deduplicate_attributes(attributes)

            if attributes:
                print("Attributes Fetched:", attributes)

            for attr in attributes:
                key = (
                    subject,
                    attr["aspect"],
                    str(attr["value"]),
                    str(attr.get("unit"))
                )

                if key in seen_global:
                    continue

                seen_global.add(key)

                insert_attribute(
                    document_id=url,
                    entity=subject,
                    aspect=attr["aspect"],
                    value=str(attr["value"]),
                    unit=attr.get("unit"),
                    attr_type=attr.get("type"),
                    source="demo_pipeline",
                    confidence_score=1.0
                )

print("\nEndpoint")