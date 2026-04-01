from backend.services.preprocessing import *

from backend.services.extractor_content import extract_content
from backend.services.mapper_domain import detect_domain
from backend.services.detector_subjects import *

from backend.services.extractor_data import extract_attributes, extract_tables, parse_table_numeric
from backend.services.utils import deduplicate_attributes


def process_query_url(parsed: dict, url: str):
    query = parsed.get("original", "")
    domain = detect_domain(query)

    subjects = parsed.get("entities", [])
    if not subjects:
        subjects = extract_subjects(query)

    alias_map = build_subject_aliases(subjects)

    data = extract_content(url)

    if not data:
        return None

    results = []

    tables = data.get("tables", [])
    print("\n[DEBUG] TABLES COUNT:", len(tables))

    for row in tables:
        if "battery" in row["aspect"]:
            print("[DEBUG] BATTERY ROW:", row)

    for row in tables:
        parsed_numeric = parse_table_numeric(row["value"])

        if not parsed_numeric:
            continue

        matched_subjects = detect_subjects(row["value"], alias_map)

        # ---- FALLBACK: assume main subject if nothing matched ----
        if not matched_subjects and len(subjects) == 1:
            matched_subjects = subjects

        for subject in matched_subjects:
            results.append({
                "entity": subject,
                "aspect": row["aspect"],
                "value": parsed_numeric["value"],
                "unit": parsed_numeric["unit"],
                "type": "table",
                "source": url
            })

    if not data:
        return None

    cleaned = clean_text(data["text"])
    sentences = split_into_sentences(cleaned)

    seen_global = set()

    for s in sentences:
        parts = split_comparison(s)
        sentence_subjects = detect_subjects(s, alias_map)

        shared = (
            is_shared_context(s)
            or len(sentence_subjects) > 1
        )

        for part in parts:
            matched_subjects = detect_subjects(part, alias_map)

            if shared:
                matched_subjects = subjects

            if not matched_subjects:
                continue

            attributes = extract_attributes(part, domain)
            attributes = deduplicate_attributes(attributes)

            query_attribute = parsed.get("attribute")

            # ---- META ATTRIBUTES (do NOT filter) ----
            META_ATTRIBUTES = ["specifications", "specs"]

            if query_attribute and query_attribute not in META_ATTRIBUTES:
                attributes = [
                    a for a in attributes
                    if a.get("aspect") == query_attribute
                ]

            for subject in matched_subjects:
                for attr in attributes:
                    key = (
                        subject,
                        attr["aspect"],
                        str(attr["value"]),
                        str(attr.get("unit"))
                    )

                    if key in seen_global:
                        continue

                    seen_global.add(key)

                    results.append({
                        "entity": subject,
                        "aspect": attr["aspect"],
                        "value": attr["value"],
                        "unit": attr.get("unit"),
                        "type": attr.get("type"),
                        "source": url
                    })

    return results