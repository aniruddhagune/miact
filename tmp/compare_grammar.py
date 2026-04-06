import sys
import os

# Set PYTHONPATH to root so we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.nlp.grammar_rules import classify_clause as old_classify
from backend.nlp.grammar_structural import classify_clause as new_classify

test_cases = [
    "When I say that the OnePlus 9 doesn't feel premium, this doesn't mean that it looks bad or a deal-breaker.",
    "The camera is not at all disappointing.",
    "This is not a very good phone, but it is not bad.",
    "When was the iPhone 15 released?",
    "When I got the package, it was damaged.",
    "Does the battery even last a day?",
    "Wait, it doesn't really seem like a very good phone.",
    "The OnePlus 9 battery.",
    "Is it better than the S23?",
]

print(f"{'TEST CASE':<70} | {'OLD (REGEX)':<25} | {'NEW (STRUCTURAL)':<25}")
print("-" * 130)

for case in test_cases:
    old_res = old_classify(case)
    new_res = new_classify(case)
    
    old_out = f"{old_res['sentiment']} ({old_res['score']}) [{'Q' if old_res['is_question'] else 'S'}]"
    new_out = f"{new_res['sentiment']} ({new_res['score']}) [{'Q' if new_res['is_question'] else 'S'}]"
    
    print(f"{case[:68]:<70} | {old_out:<25} | {new_out:<25}")
