from backend.nlp.spacy_loader import nlp
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from backend.nlp.analyzer_sentiment import NEGATIVE_WORDS, OPINION_WORDS
analyzer = SentimentIntensityAnalyzer()




def classify_sentence(sentence: str):
    sentence_lower = sentence.lower()

    # ---- negative override ----
    if any(word in sentence_lower for word in NEGATIVE_WORDS):
        return "subjective_negative"

    doc = nlp(sentence)

    sentiment = analyzer.polarity_scores(sentence)
    compound = sentiment["compound"]

    has_opinion_word = any(word in sentence_lower for word in OPINION_WORDS)

    factual_verbs = ["has", "is", "was", "were", "contains", "includes"]
    has_factual_verb = any(token.lemma_ in factual_verbs for token in doc)

    if has_opinion_word:
        if compound >= 0:
            return "subjective_positive"
        else:
            return "subjective_negative"

    if has_factual_verb and -0.3 < compound < 0.3:
        return "objective"

    if compound >= 0.4:
        return "subjective_positive"
    elif compound <= -0.4:
        return "subjective_negative"

    return "objective"