from backend.database.helpers import get_or_create_entity, get_or_create_source, create_document_if_not_exists
from backend.database.attribute_repository import insert_attribute
from backend.domains.regions import resolve_region
import re

def group_variants_and_persist(results_dict: dict):
    final_dict = {}

    for entity_name, items in results_dict.items():
        processed_items = []
        
        display_specs = []
        memory_specs = []
        storage_specs = []
        
        other_items = []

        for r in items:
            aspect = r.get("aspect", "").lower().strip()
            val = str(r.get("value", "")).strip()
            unit = r.get("unit")
            
            # ---- BAND FORMATTING ----
            if "bands" in aspect:
                # Replace multiple lines/spaces with commas/slashes
                val = re.sub(r"\s*\n\s*|\s{2,}", ", ", val)
                val = val.replace(" ,", ",").replace(",,", ",")
            
            # ---- REGIONAL MAPPING ----
            # Check for leading regional tags like "EU: 128GB" or "(NA)"
            region_match = re.search(r"^([A-Z]{2,5})\s*[:\-]\s*|\s*\(([A-Z]{2,5})\)\s*$", val)
            if region_match:
                code = region_match.group(1) or region_match.group(2)
                region_name = resolve_region(code)
                # Ensure region is prepended or highlighted
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
                r["value"] = val # Update for later use
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
        # Prevent exact copies for the same aspect
        unique_final = []
        seen_keys = set()
        
        for item in other_items:
            key = (item["aspect"].lower().strip(), str(item["value"]).lower().strip())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_final.append(item)
        
        other_items = unique_final
                
        # --- ASPECT SCORING LOGIC ---
        subjective_opinions = [r for r in items if r.get("type", "") == "subjective"]
        if subjective_opinions:
            aspect_map = {}
            for op in subjective_opinions:
                asp = op.get("aspect", "")
                if asp not in aspect_map:
                    aspect_map[asp] = []
                aspect_map[asp].append(op.get("score", 0.0))
                
            for asp, scores in aspect_map.items():
                avg = sum(scores) / len(scores)
                scaled = round((avg + 1.0) * 5.0, 1) # [-1, 1] -> [0, 10]
                other_items.append({
                    "entity": entity_name,
                    "aspect": asp,
                    "value": scaled,
                    "type": "score",
                    "source": None 
                })

        final_dict[entity_name] = other_items

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
                print(f"[DB Error] persist failed for {url}: {e}")

    return final_dict
