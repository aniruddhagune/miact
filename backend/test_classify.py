from services.preprocessing import clean_text, split_into_sentences
from services.content_extractor import extract_content
from services.classifier import classify_sentence

data = extract_content("https://en.wikipedia.org/wiki/OnePlus_9")

cleaned = clean_text(data["text"])
sentences = split_into_sentences(cleaned)

for s in sentences[:20]:
    print(classify_sentence(s), ":", s)