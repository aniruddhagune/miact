import re
from backend.utils.logger import logger

def normalize_value(val: str) -> str:
    """
    Normalize factual values to minimize superficial formatting differences.
    E.g., "5000mAh", "5000 mAh", "5,000 mAh" -> "5000mah"
    """
    if not isinstance(val, str):
        val = str(val)
    
    val = val.lower().strip()
    
    # Remove thousands-separator commas from numbers
    val = re.sub(r'(\d),(\d)', r'\1\2', val)
    
    # Normalize units: "mah" (case insensitive handled by lower())
    # Remove spaces between number and unit
    val = re.sub(r'(\d+)\s*(mah|gb|tb|hz|mp|w|v|mah|g|kg|lbs|inch|")', r'\1\2', val)
    
    # Normalize "inch" and '"'
    val = val.replace('"', 'inch')
    
    # Remove extra spaces
    val = " ".join(val.split())
    
    return val

# Aspects that should always show multiple entries if from different sources
# (e.g. News summaries should NOT be bundled as 'conflicts')
MULTI_PERSPECTIVE_ASPECTS = [
    "ai highlights",
    "summary",
    "brief summary",
    "updates"
]

def resolve_conflicts(items: list) -> list:
    """
    Groups items by aspect and identifies true semantic conflicts.
    If multiple sources disagree on a normalized value, bundles them as a 'conflict'.
    """
    if not items:
        return []

    logger.debug("CONFLICT_RESOLVER", f"Resolving conflicts for {len(items)} items")

    # Group items by aspect
    by_aspect = {}
    for item in items:
        aspect = item.get("aspect", "unknown").lower().strip()
        if aspect not in by_aspect:
            by_aspect[aspect] = []
        by_aspect[aspect].append(item)

    final_items = []

    for aspect, aspect_items in by_aspect.items():
        # 0. Check for Multi-Perspective (News/Research)
        # Any item with type 'news' or 'research' is considered multi-perspective
        # or if the aspect is in the whitelist or starts with Summary:
        is_multi = any(i.get("type") in ["news", "research"] for i in aspect_items) or \
                   aspect.lower() in MULTI_PERSPECTIVE_ASPECTS or \
                   aspect.lower().startswith("summary:")
                   
        if is_multi:
            final_items.extend(aspect_items)
            continue

        # Map normalized values to their original factual items
        # and keep all subjective items separately
        factual_normalized_map = {}
        subjective_items = []
        
        for item in aspect_items:
            if item.get("type") == "subjective":
                subjective_items.append(item)
            else:
                norm = normalize_value(item.get("value", ""))
                if norm not in factual_normalized_map:
                    factual_normalized_map[norm] = []
                factual_normalized_map[norm].append(item)
        
        # 1. Handle Factual Conflicts/Deduplication
        if len(factual_normalized_map) == 1:
            # All sources agree on one normalized factual value
            norm_val = list(factual_normalized_map.keys())[0]
            final_items.append(factual_normalized_map[norm_val][0])
        elif len(factual_normalized_map) > 1:
            # Multiple sources disagree -> Conflict!
            logger.warning("CONFLICT_RESOLVER", f"Conflict detected in '{aspect}': {list(factual_normalized_map.keys())}")
            template = aspect_items[0]
            conflict_obj = {
                "entity": template.get("entity"),
                "aspect": template.get("aspect"),
                "type": "conflict",
                "conflicting_values": []
            }
            for norm, items_with_norm in factual_normalized_map.items():
                rep = items_with_norm[0]
                conflict_obj["conflicting_values"].append({
                    "value": rep.get("value"),
                    "source": rep.get("source"),
                    "normalized": norm
                })
            final_items.append(conflict_obj)
            
        # 2. Add ALL subjective items (they are opinions and should always be shown)
        final_items.extend(subjective_items)

    return final_items
