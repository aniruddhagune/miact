from services.search_service import fetch_search_results
from services.extractor_data import extract_tables

from database.attribute_repository import insert_attribute
from database.helpers import (
    get_or_create_entity,
    get_or_create_source,
    create_document_if_not_exists
)

# ---- INPUT ----
query = "OnePlus 9 specs"
entity_name = "OnePlus 9"

# ---- PREP ----
entity_id = get_or_create_entity(entity_name)

# ---- SEARCH ----
results = fetch_search_results(query, 5)
urls = [r["url"] for r in results[:3]]

print("URLs:")
for u in urls:
    print("-", u)

# ---- PIPELINE ----
for url in urls:
    print(f"\n=== Processing: {url} ===")

    # ---- Ensure source + document ----
    source_id = get_or_create_source(url)
    create_document_if_not_exists(url, source_id)

    # ---- Extract tables ----
    table_data = extract_tables(url)

    print("Tables found:", len(table_data))

    for row in table_data:
        print("ROW:", row)

        insert_attribute(
            entity_id=entity_id,
            document_id=url,   # TEXT now
            aspect=row["aspect"],
            value=row["value"],
            unit=None,
            attr_type="table",
            confidence_score=1.0
        )

print("\n✅ TABLE PIPELINE DONE")