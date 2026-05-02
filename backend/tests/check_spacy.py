import sys
import os
sys.path.append('.')

from backend.nlp.spacy_loader import nlp

def check(text):
    doc = nlp(text.lower())
    print(f"\nText: {text}")
    print("-" * 40)
    for token in doc:
        print(f"Token: {token.text:15} | Lemma: {token.lemma_:15} | POS: {token.pos_:6} | Stop: {token.is_stop}")

if __name__ == "__main__":
    check("OnePlus 9")
    check("OnePlus 9 review")
    check("OnePlus9review")
