from backend.nlp.analyzer_sentiment import get_sentiment
from backend.nlp.mapper_aspect_sentiment import analyze_aspect_sentiment

def test():
    text = "The camera is great."
    sentiment = get_sentiment(text)
    print(f"SENTIMENT: {sentiment}")

    res = analyze_aspect_sentiment(text, "tech")
    print(f"ANALYSIS: {res}")

if __name__ == "__main__":
    test()
