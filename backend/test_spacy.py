from services.preprocessing import clean_text, split_into_sentences
from services.content_extractor import extract_content
from services.aspect_extractor import extract_aspects
from services.classifier import classify_sentence
from services.domain_detector import detect_domain

data = extract_content("https://en.wikipedia.org/wiki/OnePlus_9")

cleaned = clean_text(data["text"])
sentences = split_into_sentences(cleaned)

for s in sentences[:20]:
    aspects = extract_aspects(s)
    label = classify_sentence(s)

    print("\nSentence:", s)
    print("Aspects:", aspects)
    print("Label:", label)

query = "oneplus 9 vs oneplus 9 pro"

domain = detect_domain(query)


aspects = extract_aspects(s, domain=domain)

