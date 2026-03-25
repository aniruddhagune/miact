import re

def extract_values(sentence: str, aspects: list):
    results = []

    sentence_lower = sentence.lower()

    # ---- patterns ----
    patterns = [
        # 4500 mAh
        r"(\d+)\s*(mah)",
        # 120 Hz
        r"(\d+)\s*(hz)",
        # 6.7 inch
        r"(\d+(\.\d+)?)\s*(inch|inches)",
        # 8 GB / 128 GB
        r"(\d+)\s*(gb|tb)",
        # watts
        r"(\d+)\s*(w|watts)",
    ]

    for aspect in aspects:
        for pattern in patterns:
            matches = re.findall(pattern, sentence_lower)

            for match in matches:
                value = match[0]
                unit = match[-1]

                results.append({
                    "aspect": aspect,
                    "value": float(value),
                    "unit": unit
                })

    return results