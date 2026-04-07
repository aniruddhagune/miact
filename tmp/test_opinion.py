from backend.nlp.mapper_aspect_sentiment import analyze_aspect_sentiment
from backend.nlp.grammar_structural import classify_clause

def test():
    texts = [
        "The camera is great.",
        "I really liked the display.",
        "Battery life is disappointing.",
        "The phone is fast and snappy.",
        "It feels premium in hand.",
        "The software has some bugs but it is okay."
    ]

    for t in texts:
        print(f"\nTEXT: {t}")
        # Test sentiment extraction
        res = analyze_aspect_sentiment(t, "tech")
        print(f"EXTRACTED: {res}")

        # Test structural analysis
        struct = classify_clause(t)
        print(f"STRUCTURAL: {struct}")

        # Test valid opinion logic (mimicking pipeline_service.py)
        for sa in res:
            text_lower = sa["text"].lower()
            TANGIBLE_TERMS = ["feel", "build", "performance", "speed", "camera", "battery",
                              "display", "screen", "price", "value", "design", "quality",
                              "software", "smooth", "fast", "slow", "hot", "heat", "lag",
                              "charging", "speakers", "audio", "storage", "graphics"]
            
            WORDS_MINIMUM = 5 if any(t in text_lower for t in TANGIBLE_TERMS) else 10
            is_valid = True
            if struct.get("completeness") == "incomplete": is_valid = False
            if struct.get("is_question"): is_valid = False
            if sa["score"] == 0: is_valid = False
            if len(sa["text"].split()) < WORDS_MINIMUM: is_valid = False

            print(f"  -> Aspect: {sa['aspect']}, Score: {sa['score']}, Valid: {is_valid}")

if __name__ == "__main__":
    test()
