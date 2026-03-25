import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nlp = spacy.load("en_core_web_sm")
analyzer = SentimentIntensityAnalyzer()

# opinion-heavy adjectives
OPINION_WORDS = [
    "good", "bad", "excellent", "poor", "amazing",
    "terrible", "great", "awful", "best", "worst",
    "impressive", "disappointing"
]


def classify_sentence(sentence: str):
    doc = nlp(sentence)

    sentiment = analyzer.polarity_scores(sentence)
    compound = sentiment["compound"]

    # check for opinion words explicitly
    has_opinion_word = any(word in sentence.lower() for word in OPINION_WORDS)

    # detect factual verbs
    factual_verbs = ["has", "is", "was", "were", "contains", "includes"]
    has_factual_verb = any(token.lemma_ in factual_verbs for token in doc)

    # ---- logic ----
    if has_opinion_word:
        if compound >= 0:
            return "subjective_positive"
        else:
            return "subjective_negative"

    # neutral factual statements
    if has_factual_verb and -0.3 < compound < 0.3:
        return "objective"

    # fallback to sentiment
    if compound >= 0.4:
        return "subjective_positive"
    elif compound <= -0.4:
        return "subjective_negative"

    return "objective"