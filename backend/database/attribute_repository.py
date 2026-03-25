from backend.database.connection import get_connection


def insert_attribute(entity, aspect, value, unit):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO specs (entity, aspect, value, unit) VALUES (%s, %s, %s, %s)",
        (entity, aspect, value, unit)
    )

    conn.commit()
    cur.close()
    conn.close()