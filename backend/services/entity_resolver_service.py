import re
from backend.database.connection import get_connection, execute_query
from backend.services.search_service import fetch_search_results_async
from backend.utils.logger import logger

async def determine_canonical_name(alias: str) -> str:
    logger.debug("RESOLVER", f"Attempting to find canonical identity for: '{alias}'")

    # Fallback to duckduckgo scrape on gsmarena for phone/tech identity
    search_query = f"{alias} site:gsmarena.com"
    results = await fetch_search_results_async(search_query, num_results=1)

    if not results:
        logger.debug("RESOLVER", f"No gsmarena results found. Using alias: '{alias}'")
        return alias
    
    first_hit = results[0]
    title = first_hit.get("title", "")
    
    # GSMArena title format: "Samsung Galaxy S23 - Full phone specifications"
    if " - " in title:
        title = title.split(" - ")[0]
        
    canonical = title.strip()
    
    # Extract numbers from alias. If canonical lacks the number, reject.
    alias_nums = re.findall(r'\d+', alias)
    for n in alias_nums:
        if n not in canonical:
            logger.debug("RESOLVER", f"Verification failed (missing digit {n}). Fallback to alias: '{alias}'")
            return alias

    logger.info("RESOLVER", f"Resolved '{alias}' -> '{canonical}'")
        
    # Save to db mappings
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_query(cursor, '''CREATE TABLE IF NOT EXISTS entity_aliases (
            alias TEXT PRIMARY KEY,
            canonical TEXT
        )''')
        execute_query(cursor, '''INSERT INTO entity_aliases (alias, canonical) VALUES (%s, %s) ON CONFLICT (alias) DO NOTHING''', (alias.lower(), canonical.lower()))
        conn.commit()
    except Exception as e:
        logger.error("RESOLVER", f"Database error during alias storage: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

    return canonical


async def resolve_canonical_entities(subjects: list[str]) -> list[str]:
    """
    Given a list of subjects like ['samsung s23', 'iphone 15'],
    check the DB for cached official names. If missed, crawl DDG to verify.
    Returns the mapped list, e.g. ['Samsung Galaxy S23', 'Apple iPhone 15']
    """
    if not subjects:
        return []

    logger.info("RESOLVER", f"Resolving {len(subjects)} entities: {subjects}")
    resolved = []
    conn = get_connection()
    cursor = conn.cursor()

    try:
        execute_query(cursor, '''CREATE TABLE IF NOT EXISTS entity_aliases (
            alias TEXT PRIMARY KEY,
            canonical TEXT
        )''')
        conn.commit()
        
        for sub in subjects:
            execute_query(cursor, "SELECT canonical FROM entity_aliases WHERE alias = %s", (sub.lower(),))
            row = cursor.fetchone()
            if row:
                logger.debug("RESOLVER", f"Cache hit: '{sub}' -> '{row[0]}'")
                resolved.append(row[0].title()) # Title case for neatness
            else:
                canon = await determine_canonical_name(sub)
                resolved.append(canon)
    except Exception as e:
         logger.error("RESOLVER", f"Resolution failed: {e}")
         return subjects
    finally:
        cursor.close()
        conn.close()

    return resolved
