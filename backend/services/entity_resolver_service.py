import re
from backend.database.connection import get_connection
from backend.services.search_service import fetch_search_results_async

async def determine_canonical_name(alias: str) -> str:
    from backend.config.variables import DEBUG
    if DEBUG:
        print(f"[Resolver] Attempting to find canonical identity for: {alias}")

    # Fallback to duckduckgo scrape on gsmarena for phone/tech identity
    search_query = f"{alias} site:gsmarena.com"
    results = await fetch_search_results_async(search_query, num_results=1)

    if not results:
        if DEBUG:
            print(f"[Resolver] No results found on gsmarena. Falling back to alias: {alias}")
        return alias
    
    first_hit = results[0]
    title = first_hit.get("title", "")
    
    # GSMArena title format: "Samsung Galaxy S23 - Full phone specifications"
    if " - " in title:
        title = title.split(" - ")[0]
        
    canonical = title.strip()
    
    # We might need to ensure `alias` tokens are in `canonical`. 
    # e.g., if we searched 'samsung s23' and got 'Samsung Galaxy S23' -> good.
    # What if it hallucinated and gave 'Apple iPhone 15'?
    import re
    # Extract numbers from alias. If canonical lacks the number, reject.
    alias_nums = re.findall(r'\d+', alias)
    for n in alias_nums:
        if n not in canonical:
            if DEBUG:
                print(f"[Resolver] Verification failed (missing digit {n}). Fallback to alias: {alias}")
            return alias

    if DEBUG:
        print(f"[Resolver] Confirmed Canonical Name: {canonical}")
        
    # Save to db mappings
    # For now, we will just insert it as a known mapping. We can make a simple table `entity_aliases`
    # if it doesn't exist. Actually, let's just make sure it's created.
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS entity_aliases (
            alias TEXT PRIMARY KEY,
            canonical TEXT
        )''')
        cursor.execute('''INSERT INTO entity_aliases (alias, canonical) VALUES (%s, %s) ON CONFLICT (alias) DO NOTHING''', (alias.lower(), canonical.lower()))
        conn.commit()
    except Exception as e:
        if DEBUG:
            print(f"[Resolver] DB Error: {e}")
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

    resolved = []
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS entity_aliases (
            alias TEXT PRIMARY KEY,
            canonical TEXT
        )''')
        conn.commit()
        
        for sub in subjects:
            cursor.execute("SELECT canonical FROM entity_aliases WHERE alias = %s", (sub.lower(),))
            row = cursor.fetchone()
            if row:
                resolved.append(row[0].title()) # Title case for neatness
            else:
                canon = await determine_canonical_name(sub)
                resolved.append(canon)
    except Exception as e:
         print("[Resolver] Error in resolve_canonical_entities:", e)
         # Fallback to original
         return subjects
    finally:
        cursor.close()
        conn.close()

    return resolved
