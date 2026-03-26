import re


def extract_comparison_direction(sentence: str):
    sentence_lower = sentence.lower()

    # Pattern: A is better than B
    match = re.search(r"(.+?)\s+is\s+(better|worse)\s+than\s+(.+)", sentence_lower)

    if match:
        left = match.group(1).strip()
        comparator = match.group(2)
        right = match.group(3).strip()

        if comparator == "better":
            return {
                "winner": left,
                "loser": right,
                "relation": "better"
            }
        else:
            return {
                "winner": right,
                "loser": left,
                "relation": "worse"
            }

    return None