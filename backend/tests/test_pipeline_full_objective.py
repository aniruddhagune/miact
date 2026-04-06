from backend.utils.text_helpers import *
from services.extractor_content import extract_content
from services.mapper_domain import detect_domain
from services.detector_subjects import extract_subjects, build_subject_aliases

from services.extractor_data import extract_attributes
from services.utils import deduplicate_attributes

from database.attribute_repository import insert_attribute


# ---- CONFIG ----
MAX_SOURCES = 3


def build_urls(entity: str):
    name = entity.replace(" ", "_")

    return [
        f"https://en.wikipedia.org/wiki/{name}",
    ]


# ---- INPUT ----
query = "OnePlus 9 vs OnePlus 9 Pro"

# ---- SETUP ----
domain = detect_domain(query)
subjects = extract_subjects(query)

print("Subjects:", subjects)

if not subjects:
    print("⚠️ No subjects detected. Using fallback.")
    subjects = [query]

alias_map = build_subject_aliases(subjects)

seen_global = set()


# ---- PIPELINE ----
for subject in subjects:
    print(f"\n=== Processing: {subject} ===")

    urls = build_urls(subject)

    print("URLs:", urls)

    for url in urls:
        print(f"Fetching: {url}")

        try:
            data = extract_content(url)
        except Exception as e:
            print("❌ ERROR FETCHING:", e)
            continue

        text = data.get("text", "")
        print("Fetched text length:", len(text))

        cleaned = clean_text(text)
        sentences = split_into_sentences(cleaned)

        print("Sentence count:", len(sentences))

        for s in sentences[:10]:
            print("Sample sentence:", s)

        for s in sentences:
            attributes = extract_attributes(s, domain)
            attributes = deduplicate_attributes(attributes)

            if attributes:
                print("✅ ATTRIBUTES FOUND:", attributes)

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
                    source="test_pipeline",
                    confidence_score=1.0
                )