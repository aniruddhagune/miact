from backend.nlp.grammar_rules import classify_clause, score_clause

test_sentence = "When I say that the OnePlus 9 doesn't feel premium, this doesn't mean that it looks bad or a deal-breaker."

print(f"Testing sentence: {test_sentence}")
print("-" * 40)

# The grammar rules currently work best on clauses or sentences.
# Let's see how it handles the whole thing first.
try:
    result = classify_clause(test_sentence)
    print("Result for full sentence:")
    for k, v in result.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"Error classifying sentence: {e}")

print("\n" + "="*40 + "\n")

# Normally the pipeline splits by clauses or sentences.
# Let's try splitting it manually to see how individual parts are scored.
parts = [
    "the OnePlus 9 doesn't feel premium",
    "this doesn't mean that it looks bad",
    "this doesn't mean it is a deal-breaker"
]

for p in parts:
    print(f"Clause: {p}")
    try:
        res = classify_clause(p)
        raw_score, terms = score_clause(p)
        print(f"  Sentiment: {res['sentiment']}")
        print(f"  Normalized Score: {res['score']}")
        print(f"  Raw Score: {raw_score}")
        print(f"  Matched Terms: {terms}")
    except Exception as e:
        print(f"  Error on part: {e}")
    print("-" * 20)
