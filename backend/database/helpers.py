from database.connection import get_connection
from urllib.parse import urlparse


def get_or_create_entity(name: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT entity_id FROM entities WHERE name = %s",
        (name,)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        "INSERT INTO entities (name, entity_type) VALUES (%s, %s) RETURNING entity_id",
        (name, "product")
    )
    entity_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return entity_id


def get_or_create_source(url: str):
    domain = urlparse(url).netloc

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT source_id FROM sources WHERE base_url = %s",
        (domain,)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        "INSERT INTO sources (name, base_url) VALUES (%s, %s) RETURNING source_id",
        (domain, domain)
    )
    source_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return source_id


def create_document_if_not_exists(url: str, source_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT document_id FROM documents WHERE document_id = %s",
        (url,)
    )

    if cur.fetchone():
        cur.close()
        conn.close()
        return

    cur.execute(
        "INSERT INTO documents (document_id, source_id) VALUES (%s, %s)",
        (url, source_id)
    )

    conn.commit()
    cur.close()
    conn.close()