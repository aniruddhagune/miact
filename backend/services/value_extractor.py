import re

UNIT_PATTERNS = [
    # battery
    (r"(\d+(\.\d+)?)\s*(mah)", "battery"),

    # refresh rate
    (r"(\d+(\.\d+)?)\s*(hz)", "display"),

    # storage / RAM
    (r"(\d+(\.\d+)?)\s*(kb|mb|gb|tb)", "memory"),

    # power
    (r"(\d+(\.\d+)?)\s*(w|watts)", "power"),

    # size
    (r"(\d+(\.\d+)?)\s*(inch|inches|cm)", "display"),

    # screen
    (r"(\d+(\.\d+)?)\s*(LCD|OLED|AMOLED|8-bit|10-bit|P3)", "screen"),

    # camera megapixels
    (r"(\d+(\.\d+)?)\s*(mp)", "camera"),

    # millimeters (lens)
    (r"(\d+(\.\d+)?)\s*(mm)", "lens"),

    # speaker loudness
    (r"(\d+(\.\d+)?)\s*(db|decibel)", "speakers"),
]


def extract_values(sentence: str, aspects: list):
    results = []
    sentence_lower = sentence.lower()

    for pattern, category in UNIT_PATTERNS:
        matches = re.finditer(pattern, sentence_lower)

        for match in matches:
            value = float(match.group(1))
            unit = match.group(3)

            start = match.start()
            window = sentence_lower[max(0, start - 40): start + 40]

            for aspect in aspects:
                # optional: match category to aspect
                if aspect not in window:
                    continue

                results.append({
                    "aspect": aspect,
                    "value": value,
                    "unit": unit
                })

    return results