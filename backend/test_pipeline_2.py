from services.preprocessing import clean_text, split_into_sentences
from backend.services.objectivity_classifier import classify_sentence
from services.domain_detector import detect_domain
from services.comparison_detector import detect_comparison

from database.attribute_repository import insert_attribute

from services.data_extractor import extract_attributes

# ---- INPUT ----
query = "oneplus 9 vs oneplus 9 pro"
entity = "OnePlus 9"

# ---- DOMAIN ----
domain = detect_domain(query)

# ---- FETCH DATA ----
url = "https://en.wikipedia.org/wiki/OnePlus_9"
data = extract_content(url)

# ---- PREPROCESS ----
cleaned = clean_text(data["text"])
sentences = split_into_sentences(cleaned)


# ---- PIPELINE ----
for s in sentences:
    sentiment = classify_sentence(s)
    comparison = detect_comparison(s)

    attributes = extract_attributes(s, domain)

    print("\nSentence:", s)
    print("Sentiment:", sentiment)
    print("Comparison:", comparison)
    print("Attributes:", attributes)

    if sentiment == "objective":
        for attr in attributes:
            insert_attribute(
                document_id=url,
                entity=entity,
                aspect=attr["aspect"],
                value=str(attr["value"]),
                unit=attr.get("unit"),
                attr_type=attr.get("type"),
                source="wikipedia",
                confidence_score=1.0
            )