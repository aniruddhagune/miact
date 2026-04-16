from backend.database.helpers import get_or_create_entity, get_or_create_source, create_document_if_not_exists
from backend.database.attribute_repository import insert_attribute
from backend.domains.regions import REGIONS, resolve_region
import re
from backend.utils.logger import logger

# Regex to find a region code at the start (e.g. "EU:", "NA -") or end (e.g. "(EU)")
_REGION_CODE_RE = re.compile(
    r'^([A-Z]{2,5})\s*[:\-]\s*|(?:^|\s)\(([A-Z]{2,5}(?:[/,][A-Z]{2,5})*)\)\s*$'
)

# Region separators inside a single value like "International: 100W / USA: 80W"
_MULTI_REGION_RE = re.compile(
    r'([A-Za-z][A-Za-z ]{2,20})\s*:\s*([^/]+?)(?=\s+[A-Za-z][A-Za-z ]{2,20}\s*:|$)'
)

def _clean_numeric_value(val: str) -> str:
    """Remove thousands-separator commas from numbers while preserving list commas."""
    # Replace commas that are between digits (thousands sep) with nothing
    return re.sub(r'(\d),(\d)', r'\1\2', val)

def _split_regional_value(val: str) -> list[str] | None:
    """
    If a value contains multiple regional variants like
    'International: 100W / USA: 80W' or 'EU: 128GB\nNA: 256GB',
    return a list of formatted strings like ['International: 100W', 'USA: 80W'].
    Returns None if no regional structure detected.
    """
    # First try newline-separated regions
    lines = [l.strip() for l in val.split('\n') if l.strip()]
    if len(lines) > 1:
        region_lines = []
        for line in lines:
            m = _REGION_CODE_RE.match(line)
            if m:
                code = m.group(1) or ''
                full_name = resolve_region(code) if code else code
                cleaned = re.sub(r'^[A-Z]{2,5}\s*[:\-]\s*', '', line)
                region_lines.append(f"{full_name}: {cleaned}")
            else:
                region_lines.append(line)
        return region_lines if len(region_lines) > 1 else None

    # Then try slash/colon-separated regions inline
    matches = _MULTI_REGION_RE.findall(val)
    if len(matches) > 1:
        result = []
        for region_name, region_val in matches:
            resolved = resolve_region(region_name.strip().upper()) if region_name.strip().upper() in REGIONS else region_name.strip()
            result.append(f"{resolved}: {region_val.strip()}")
        return result

    return None


def group_variants_and_persist(results_dict: dict):
    logger.info("PROCESSING", f"Grouping variants and persisting for {len(results_dict)} entities")
    final_dict = {}

    for entity_name, items in results_dict.items():
        logger.debug("PROCESSING", f"Processing {len(items)} items for {entity_name}")
        processed_items = []
        
        display_specs = []
        memory_specs = []
        storage_specs = []
        
        other_items = []

        for r in items:
            aspect = r.get("aspect", "").lower().strip()
            val = str(r.get("value", "")).strip()
            unit = r.get("unit")

            # ---- NUMERIC CLEANING — strip thousands-separator commas ----
            val = _clean_numeric_value(val)

            # ---- BAND FORMATTING ----
            if "bands" in aspect:
                val = re.sub(r"\s*\n\s*|\s{2,}", ", ", val)
                val = val.replace(" ,", ",").replace(",,", ",")
            
            # ---- REGIONAL LINE SPLITTING ----
            regional_parts = _split_regional_value(val)
            if regional_parts:
                for part in regional_parts:
                    new_r = dict(r)
                    new_r["value"] = part
                    if aspect in ["display", "screen", "resolution", "refresh rate"]:
                        if unit:
                            new_r["value"] += f" {unit}"
                        display_specs.append((new_r["value"], r.get("source")))
                    elif aspect == "ram":
                        if unit:
                            new_r["value"] += f" {unit}"
                        memory_specs.append((new_r["value"], r.get("source")))
                    elif aspect == "storage":
                        if unit:
                            new_r["value"] += f" {unit}"
                        storage_specs.append((new_r["value"], r.get("source")))
                    else:
                        other_items.append(new_r)
                continue

            # ---- REGIONAL TAG (single region) ----
            region_match = _REGION_CODE_RE.search(val)
            if region_match:
                code = region_match.group(1) or region_match.group(2) or ''
                if code:
                    region_name = resolve_region(code.split('/')[0])  # first code if multi like EU/UK
                    if region_name.lower() not in val.lower():
                        val = f"[{region_name}] {val}"
            
            if aspect in ["display", "screen", "resolution", "refresh rate"]:
                if unit:
                    val += f" {unit}"
                display_specs.append((val, r.get("source")))
            
            elif aspect == "ram":
                if unit:
                    val += f" {unit}"
                memory_specs.append((val, r.get("source")))
                
            elif aspect == "storage":
                if unit:
                    val += f" {unit}"
                storage_specs.append((val, r.get("source")))
            else:
                r["value"] = val
                other_items.append(r)

        if display_specs:
            unique_d = list(set([d[0] for d in display_specs]))
            sources_d = list(set([d[1] for d in display_specs]))
            combined_display = ", ".join(unique_d)
            other_items.append({
                "entity": entity_name,
                "aspect": "display",
                "value": combined_display,
                "type": "table",
                "source": sources_d[0] if sources_d else None
            })
            
        if memory_specs or storage_specs:
            mem_str = " / ".join(list(set([m[0] for m in memory_specs]))) if memory_specs else ""
            sto_str = " / ".join(list(set([s[0] for s in storage_specs]))) if storage_specs else ""
            
            combined_mem = []
            if mem_str: combined_mem.append(f"{mem_str} RAM")
            if sto_str: combined_mem.append(f"{sto_str} Storage")
            
            ans = " + ".join(combined_mem)
            if ans:
                sources_m = list(set([m[1] for m in memory_specs + storage_specs]))
                other_items.append({
                    "entity": entity_name,
                    "aspect": "memory",
                    "value": ans,
                    "type": "table",
                    "source": sources_m[0] if sources_m else None
                })
        
        # ---- FINAL DEDUPLICATION & ORDERING ----
        unique_final = []
        seen_keys = set()
        
        for item in other_items:
            key = (item["aspect"].lower().strip(), str(item["value"]).lower().strip())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_final.append(item)
        
        other_items = unique_final
                
        # --- ASPECT SCORING LOGIC ---
        # Baseline: 5.0 (neutral). Each aspect's mean compound score adjusts it.
        subjective_opinions = [r for r in items if r.get("type", "") == "subjective"]
        if subjective_opinions:
            logger.debug("PROCESSING", f"Calculating scores from {len(subjective_opinions)} opinions")
            aspect_scores: dict[str, list[float]] = {}
            for op in subjective_opinions:
                asp = op.get("aspect", "")
                if asp not in aspect_scores:
                    aspect_scores[asp] = []
                aspect_scores[asp].append(op.get("score", 0.0))

            # Deduplicate: one score entry per aspect, blended from baseline 5
            seen_score_aspects = set()
            for asp, scores in aspect_scores.items():
                if asp in seen_score_aspects:
                    continue
                seen_score_aspects.add(asp)
                mean_compound = sum(scores) / len(scores)
                # Baseline 5 + opinion shift: compound [-1,1] * 5 gives [-5, +5] delta
                scaled = round(5.0 + (mean_compound * 5.0), 1)
                scaled = max(0.0, min(10.0, scaled))  # clamp to [0, 10]
                other_items.append({
                    "entity": entity_name,
                    "aspect": asp,
                    "value": scaled,
                    "type": "score",
                    "source": None 
                })

        final_dict[entity_name] = other_items

        logger.debug("PROCESSING", f"Persisting {len(other_items)} attributes to database")
        for r in other_items:
            url = r.get("source")
            if not url:
                continue

            try:
                source_id = get_or_create_source(url)
                create_document_if_not_exists(url, source_id)
                ent_id = get_or_create_entity(entity_name)

                if r.get("type") == "subjective":
                    val = r.get("text", "")
                    conf_score = r.get("score", 0.0)
                else:
                    val = r.get("value", "")
                    is_trusted = any(x in url.lower() for x in ["gsmarena", "devicespecifications", "wikipedia", "tomsguide"])
                    conf_score = 1.5 if is_trusted else 1.0

                insert_attribute(
                    entity_id=ent_id,
                    document_id=url,
                    aspect=r.get("aspect", ""),
                    value=str(val),
                    unit=r.get("unit"),
                    attr_type=r.get("type", "unknown"),
                    confidence_score=conf_score
                )
            except Exception as e:
                logger.error("PROCESSING", f"Persist failed for {url}: {e}")

    logger.info("PROCESSING", "All entities processed and persisted")
    return final_dict
