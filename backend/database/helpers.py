from backend.database.connection import get_connection, execute_query
from urllib.parse import urlparse


def get_or_create_entity(name: str):
    conn = get_connection()
    cur = conn.cursor()

    execute_query(cur, 
        "SELECT entity_id FROM entities WHERE name = %s",
        (name,)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    execute_query(cur, 
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

    execute_query(cur, 
        "SELECT source_id FROM sources WHERE base_url = %s",
        (domain,)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    execute_query(cur, 
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

    execute_query(cur, 
        "SELECT document_id FROM documents WHERE document_id = %s",
        (url,)
    )

    if cur.fetchone():
        cur.close()
        conn.close()
        return

    execute_query(cur, 
        "INSERT INTO documents (document_id, source_id) VALUES (%s, %s)",
        (url, source_id)
    )

    conn.commit()
    cur.close()
    conn.close()