import re

def deduplicate_attributes(attributes):
    unique = []
    seen = set()

    for attr in attributes:
        # Case-insensitive, space-normalized value check
        val_clean = str(attr.get("value", "")).lower().strip()
        key = (
            attr["aspect"].lower().strip(),
            val_clean
        )

        if key not in seen:
            seen.add(key)
            unique.append(attr)

    return unique

def expand_variants(aspect, value):
    """
    Splits multi-value strings like '128, 256 or 512 GB' 
    into individual values.
    """
    if aspect not in ["storage", "ram", "internal", "memory"]:
        return [value]
        
    # Pattern: "128, 256 or 512 GB"
    # Pattern: "8GB/128GB, 12GB/256GB"
    # Pattern: "16 GB, 32 GB"
    
    # Simple split by common delimiters
    parts = re.split(r",\s*|\s+or\s+|\s*/\s*|\s*\+\s*", value)
    
    # Extract unit if shared (e.g., "128, 256 or 512 GB")
    unit_match = re.search(r"\s*(gb|mb|tb|ram)$", value, re.I)
    unit = unit_match.group(0) if unit_match else ""
    
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p: continue
        
        # If part doesn't have a unit but the whole string does, append it
        if unit and unit.lower().strip() not in p.lower():
            p = f"{p} {unit.strip()}"
            
        cleaned.append(p)
        
    return cleaned if cleaned else [value]

def get_manual_urls(query: str) -> list[str]:
    """
    Extracts a list of absolute URLs from a string.
    Supports comma-separated or space-separated inputs.
    """
    if not query:
        return []
    
    # regex for http/https URLs that are followed by a delimiter or end of string
    url_pattern = r"(https?://[^\s,]+)"
    matches = re.findall(url_pattern, query, re.I)
    
    # Strip common trailing punctuation like commas or brackets that might be caught
    urls = []
    for m in matches:
        u = m.strip(" ,()[]<>\"'").rstrip(".")
        if u and u not in urls:
            urls.append(u)
            
    return urls