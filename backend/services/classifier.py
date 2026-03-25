from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def classify_sentence(sentence: str):
    score = analyzer.polarity_scores(sentence)
    compound = score["compound"]

    # detect factual patterns
    factual_indicators = ["has", "is", "was", "were", "measured", "contains"]

    is_factual = any(word in sentence.lower() for word in factual_indicators)

    if is_factual and -0.3 < compound < 0.3:
        return "objective"

    if compound >= 0.3:
        return "subjective_positive"
    elif compound <= -0.3:
        return "subjective_negative"
    else:
        return "objective"


# def classify_sentence(sentence: str):
#     subjective_keywords = [
#         "best", "worst", "good", "bad",
#         "amazing", "excellent", "poor",
#         "love", "hate", "better"
#     ]

#     if any(word in sentence.lower() for word in subjective_keywords):
#         return {
#             "label": 'subjective',
#             "confidence": 0.5
#             }

#     return "objective"