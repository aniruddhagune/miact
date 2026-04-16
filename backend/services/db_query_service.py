from backend.database.connection import get_connection


def fetch_from_db(parsed):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT f.aspect, f.value, f.unit, e.name, f.document_id, f.attr_type, f.confidence_score
        FROM facts f
        LEFT JOIN entities e ON f.entity_id = e.entity_id
        WHERE 1=1
    """

    params = []

    # attribute filter
    if parsed.get("attribute"):
        query += " AND f.aspect = %s"
        params.append(parsed["attribute"])

    # filter condition
    if parsed.get("filter"):
        operator_map = {
            "lt": "<=",
            "gt": ">=",
            "eq": "="
        }

        op = operator_map.get(parsed["filter"]["operator"], "=")
        query += f" AND CAST(f.value AS FLOAT) {op} %s"
        params.append(parsed["filter"]["value"])

    # entity filter
    if parsed.get("entities"):
        # If multiple entities, we fetch all of them
        placeholders = ", ".join(["%s"] * len(parsed["entities"]))
        query += f" AND e.name IN ({placeholders})"
        params.extend(parsed["entities"])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    results = []

    for row in rows:
        results.append({
            "aspect": row[0],
            "value": row[1],
            "unit": row[2],
            "entity": row[3],
            "source": row[4],
            "type": row[5],
            "score": row[6]
        })

    found_aspects = set()
    for r in results:
        found_aspects.add(r["aspect"])

    return {
        "data": results,
        "found_aspects": list(found_aspects)
    }