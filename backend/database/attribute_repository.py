from database.connection import get_connection


def insert_attribute(entity, aspect, value, unit, source):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO attributes (entity, aspect, value, unit, source) VALUES (%s, %s, %s, %s, %s)",
        (entity, aspect, value, unit, source)
    )

    conn.commit()
    cur.close()
    conn.close()