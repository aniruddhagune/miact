from backend.database.connection import get_connection, execute_query


def insert_attribute(
    entity_id,
    document_id,
    aspect,
    value,
    unit,
    attr_type,
    confidence_score
):
    conn = get_connection()
    cur = conn.cursor()

    execute_query(cur, """
        INSERT INTO facts (
            entity_id,
            document_id,
            aspect,
            value,
            unit,
            attr_type,
            confidence_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        entity_id,
        document_id,
        aspect,
        value,
        unit,
        attr_type,
        confidence_score
    ))

    conn.commit()
    cur.close()
    conn.close()