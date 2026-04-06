from backend.nlp.grammar_rules import classify_clause

TEST_SENTENCES = [
    "The display is bright and sharp.",
    "Battery life is not good.",
    "This phone feels buttery smooth in daily use.",
    "The camera is better than the previous model.",
    "Build quality is premium, but the speakers are weak.",
    "Other than the price, I really like this laptop.",
    "The screen is not bad, but it could be better.",
    "Unlike the older version, this one runs cool.",
    "The device is overpriced and a bit slow.",
    "Does the battery last even a day?",
    "Does the battery ever run out?",
    "Does the camera ever work?",
    "Do iPhones ever fail to deliver?",
    "Just because I think the phone does not feel like a premium phone, does not mean I think it's bad or a deal-breaker."
]

# Ascertain if question without a question mark.

def main():
    for sentence in TEST_SENTENCES:
        result = classify_clause(sentence)

        print(sentence)
        print(result)
        print("-" * 80)


if __name__ == "__main__":
    main()



# - Improve the sentiment analysis for sentences like "Like with the portraits from before" (not positive, it is comparison and still incomplete),
# "which reached its peak in OxygenOS 11" (this is negative because it was a previos version),
# "I was an established critic" (not related to the subject or even the company),
# "In low light" (not enough of anything), "which might disappoint some people."
# (incomplete), "OnePlus 9: design Image 1 of 2 (Image credit: Magnus Blix) (Image credit: Magnus Blix) Looks a lot like the OnePlus 8T" (more factual than not)



# I think the sentiment analysis can follow this rule.

# If no other name or "successor" or "predecessor", it is about the current subject, PROVIDED the opinion is from a page dedicated to the product.

# If there is a name for another entity, then it is about that product, and we can ignore the rest of the sentence, UNLESS it references our subject by name.

# If the sentence is a question, then it is not about the current subject.
# If a sentence is a question, but it references an aspect, then it is about that aspect. 
# This can be positive or negative.

# Since we split sentences using commas and periods, we should allow sentences to have a value that decides if it's an incomplete sentence or not. 
# If it is an incomplete sentence, then we check the previous as well as the next sentence to determine aspects and sentiments.
# If it is a complete sentence, then we check the sentence itself to determine the aspect and sentiment.