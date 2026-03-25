import spacy

nlp = spacy.load("en_core_web_sm")

text = "The iPhone 15 has a 3349 mAh battery and offers excellent performance."

doc = nlp(text)

for token in doc:
    print(token.text, token.pos_, token.dep_)