from database.connection import get_connection


def insert_attribute(
    document_id,
    entity,
    aspect,
    value,
    unit,
    attr_type,
    source,
    confidence_score
):
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO objective_facts (
            document_id,
            entity,
            attribute_name,
            value,
            unit,
            type,
            source,
            confidence_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            document_id,
            entity,
            aspect,
            value,
            unit,
            attr_type,
            source,
            confidence_score
        )
    )

    conn.commit()
    cur.close()
    conn.close()