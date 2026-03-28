from services.preprocessing import *
from services.objectivity_classifier import classify_sentence
from backend.services.mapper_aspect_sentiment import analyze_aspect_sentiment

from backend.services.extractor_content import extract_content
from backend.services.mapper_domain import detect_domain
from backend.services.detector_comparison import detect_comparison

from database.attribute_repository import insert_attribute

from backend.services.extractor_data import extract_attributes

from backend.services.detector_subjects import *
from services.utils import *

# ---- INPUT ----
query = "oneplus 9 vs oneplus 9 pro"
entity = "OnePlus 9"

# ---- DOMAIN ----
domain = detect_domain(query)
subjects = extract_subjects(query)
alias_map = build_subject_aliases(subjects)

# ---- FETCH DATA ----
url = "https://en.wikipedia.org/wiki/OnePlus_9"
data = extract_content(url)

# ---- SUBJECTIVE TEST ----
test_text = """
The battery life is excellent but the camera is disappointing.
Performance is smooth and fast.
The display is good, however brightness could be better.
The camera and display are okay.
"""

# ---- PREPROCESS ----
# cleaned = clean_text(data["text"])
cleaned = clean_text(test_text)
sentences = split_into_sentences(cleaned)
seen_global = set()

# ---- PIPELINE ----
for s in sentences:

    label = classify_sentence(s)
    # print("SENTENCE:", s)
    # print("LABEL:", label)
    # print("------")

    # ---- SUBJECTIVE ----
    if "subjective" in label:
        opinions = analyze_aspect_sentiment(s, domain)

        for op in opinions:
            print("SUBJECTIVE:", op)

        continue

    # ---- OBJECTIVE ----
    parts = split_comparison(s)
    sentence_subjects = detect_subjects(s, alias_map)

    shared = (
        is_shared_context(s)
        or len(sentence_subjects) > 1
    )
    
    for part in parts:
        matched_subjects = detect_subjects(part, alias_map)

        if shared:
            matched_subjects = subjects

        if not matched_subjects:
            continue  # don't pollute data

        attributes = extract_attributes(part, domain)
        attributes = deduplicate_attributes(attributes)

        for subject in matched_subjects:
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
                        source="wikipedia",
                        confidence_score=1.0
                    )