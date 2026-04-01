from database.connection import get_connection


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

    cur.execute("""
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
        ON CONFLICT DO NOTHING
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