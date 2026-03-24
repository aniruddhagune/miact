from services.preprocessing import clean_text, split_into_sentences
from services.content_extractor import extract_content

data = extract_content("https://www.leereamsnyder.com/hades-build-guide#twin-fists-of-malphon")

cleaned = clean_text(data["text"])
sentences = split_into_sentences(cleaned)

for s in sentences[:10]:
    print(s)