from services.preprocessing import clean_text, split_into_sentences
from services.content_extractor import extract_content
from services.aspect_extractor import extract_aspects
from services.classifier import classify_sentence
from services.domain_detector import detect_domain
from services.comparison_detector import detect_comparison
from services.value_extractor import extract_values

from database.attribute_repository import insert_attribute


# ---- INPUT ----
query = "oneplus 9 vs oneplus 9 pro"
entity = "OnePlus 9"

# ---- DOMAIN ----
domain = detect_domain(query)

# ---- FETCH DATA ----
data = extract_content("https://en.wikipedia.org/wiki/OnePlus_9")

# ---- PREPROCESS ----
cleaned = clean_text(data["text"])
sentences = split_into_sentences(cleaned)


# ---- PIPELINE ----
for s in sentences:
    aspects = extract_aspects(s, domain=domain)
    sentiment = classify_sentence(s)
    comparison = detect_comparison(s)
    values = extract_values(s, aspects)

    # ---- PRINT ----
    print("\nSentence:", s)
    print("Aspects:", aspects)
    print("Sentiment:", sentiment)
    print("Comparison:", comparison)
    print("Values:", values)

    # ---- STORE ONLY OBJECTIVE DATA ----
    if sentiment == "objective":
        for v in values:
            insert_attribute(
                entity=entity,
                aspect=v["aspect"],
                value=v["value"],
                unit=v["unit"]
            )