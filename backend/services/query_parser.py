def parse_query(query: str) -> dict:
    query = query.lower().strip()

    # ---- CASE 1: Comparison ----
    if " vs " in query:
        parts = query.split(" vs ")
        return {
            "type": "comparison",
            "entities": [p.strip() for p in parts],
            "attribute": None
        }

    # ---- CASE 2: Attribute Query ----
    keywords = ["what is", "what are", "tell me", "give me"]
    if any(query.startswith(k) for k in keywords):
        
        # naive attribute extraction
        if "battery" in query:
            attribute = "battery"
        elif "price" in query:
            attribute = "price"
        elif "camera" in query:
            attribute = "camera"
        else:
            attribute = "general"

        # naive entity extraction
        # assume "of X"
        if " of " in query:
            entity = query.split(" of ")[-1].strip()
        else:
            entity = query

        return {
            "type": "attribute",
            "entities": [entity],
            "attribute": attribute
        }

    # ---- CASE 3: Default ----
    return {
        "type": "simple",
        "entities": [query],
        "attribute": None
    }