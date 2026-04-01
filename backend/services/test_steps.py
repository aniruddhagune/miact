### Imports

import sys
# Prevents crash for weird characters in Wikipedia table
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# 1. Query parser
from backend.services.query_parser import parse_query
# 2. Extract Subjects
from backend.services.detector_subjects import extract_subjects
# 3. Extraction from page
from backend.services.extractor_content import extract_content
# 4. Preproecssing of extracted content
from backend.services.preprocessing import clean_text, split_into_sentences
# 5. Aspect Extraction
from backend.services.extractor_aspect import extract_aspects
# 6. Attribute extraction
from backend.services.extractor_data import extract_attributes
# 7. Table Extraction
from backend.services.extractor_data import extract_tables


##################################################################

### Externals
# For 1.
query = "iphone 13"
# For 3.
url = "https://en.wikipedia.org/wiki/IPhone_13"
# For 5. 6.
test_sentence = "The iPhone 13 has a battery capacity of 3240 mAh."

### Internals
# For 2.
subjects = extract_subjects(query)
# For 1.
parsed = parse_query(query)
# For 3.
content = extract_content(url)

# For 4.
cleaned = clean_text(content["text"])
sentences = split_into_sentences(cleaned)

# For 5.
aspects = extract_aspects(test_sentence, domain="tech")

# For 6.
attributes = extract_attributes(test_sentence, domain="tech")

# For 7.
table_data = extract_tables(url)

##################################################################


### Prints for debugging

# Print 1.
# print("\n--- STEP 1: PARSE QUERY ---")
# print(parsed)

# Print 2.
# print("\n--- STEP 2: SUBJECTS ---")
# print(subjects)

# Print 3.
# print("\n--- STEP 3: CONTENT ---")
# print("Title:", content.get("title"))
# print("Text length:", len(content.get("text", "")))

# Print 4.
# print("\n--- STEP 4: SENTENCES ---")
# print("Total sentences:", len(sentences))
# print("Sample:", sentences[:8])

# Print 5.
# print("\n--- STEP 5: ASPECTS ---")
# print(aspects)

# Print 6.
# print("\n--- STEP 6: ATTRIBUTES ---")
# print(attributes)

# Print 7. First
# print("\n--- STEP 7: SCAN REAL DATA ---")

# for s in sentences:
#     attrs = extract_attributes(s, domain="tech")

#     if attrs:
#         print("\nSentence:", s)
#         print("Extracted:", attrs)

# Print 7. Second
# print("\n--- STEP 8: TABLE EXTRACTION ---")

# print("Total rows:", len(table_data))

# for row in table_data[:60]:  # show first 20
#     print(str(row).encode("utf-8", errors="replace").decode("utf-8"))

# Print 8. 
# print(content["tables"][:40])

if __name__ == "__main__":
    tests = [
        "iphone 13 battery",
        "iphone 13 wikipedia",
        "oneplus 9 battery",
        "iphone 13 vs iphone 13 pro",
        "phones under 20000",
        "rtx 4090 price",
        "iphone battery 4500mah"
    ]

    for t in tests:
        print("\nQUERY:", t)
        print(parse_query(t))