import spacy
import re

nlp = spacy.load("en_core_web_sm")


def is_valid_date(text: str):
    text_lower = text.lower()

    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]

    if any(month in text_lower for month in months):
        return True

    if re.search(r"\b(19|20)\d{2}\b", text):
        return True

    return False


def extract_dates(sentence: str):
    doc = nlp(sentence)
    results = []

    sentence_lower = sentence.lower()

    for ent in doc.ents:
        if ent.label_ == "DATE":
            text = ent.text.strip()

            # filter invalid dates
            if not is_valid_date(text):
                continue

            label = "date"

            if "release" in sentence_lower or "unveiled" in sentence_lower:
                label = "release_date"
            elif "update" in sentence_lower:
                label = "update_date"

            results.append({
                "aspect": label,
                "value": text
            })

    return results