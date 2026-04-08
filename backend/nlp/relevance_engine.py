"""
Module for spaCy-based search result relevance scoring and categorization.
"""
import re
from backend.nlp.spacy_loader import nlp
from backend.domains.tech import DESCRIPTOR_TERMS, URL_TYPE_KEYWORDS

def get_result_type(url: str, title: str) -> str:
    """Categorize the URL based on title keywords and URL structure."""
    u_lower = url.lower()
    t_lower = title.lower()
    
    # 1. GSMArena Specific Patterns
    if "gsmarena.com" in u_lower:
        if re.search(r"reviewcomm-\d+", u_lower):
            return "review" # mapped as review/opinion for now
        if re.search(r"-reviews-\d+", u_lower):
            return "review"
        if re.search(r"-review-\d+", u_lower):
            return "review"
        if re.search(r"-\d+\.php", u_lower):
            return "specs"

    # 2. Comparison
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["comparison"]) or "/compare" in u_lower:
        return "comparison"
        
    # 3. Rumored
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["rumored"]):
        return "rumored"
        
    # 4. News
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["news"]) or "/news/" in u_lower:
        return "news"
        
    # 5. Review (General)
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["review"]) or "-review-" in u_lower:
        return "review"
        
    # 6. Specs (General)
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["specs"]):
        return "specs"
        
    return "unknown"

def extract_core_keywords(text: str) -> set[str]:
    """Extract meaning-bearing tokens from text."""
    if not text or len(text) < 2:
        return set()
    
    # Pre-process: Separate numbers from words (e.g., "OnePlus9" -> "OnePlus 9")
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    
    doc = nlp(text.lower())
    keywords = set()
    for token in doc:
        # Be more inclusive: Keep any non-stop, non-punct token that has substance
        if not token.is_stop and not token.is_punct and not token.is_space:
            # Keep if it has at least 2 chars OR is a digit
            if len(token.text) >= 2 or token.text.isdigit():
                keywords.add(token.lemma_)
    return keywords

def calculate_relevance_score(query: str, title: str, url: str = "") -> tuple[float, str, list[str]]:
    """
    Calculate a 0-1 relevance score, category, and trace steps.
    """
    trace = []
    u_lower = url.lower()
    t_lower_raw = title.lower()
    category = get_result_type(url, title)
    trace.append(f"Detected Category: {category}")

    q_keywords = extract_core_keywords(query)
    if not q_keywords:
        return 0.0, category, ["Empty Query"]
    
    # --- VIRTUAL TITLE FIX ---
    t_input = title
    if ("gsmarena.com" in t_input.lower() or len(t_input) < 10) and "/" in url:
        slug = url.split("/")[-1].replace("-", " ").replace("_", " ").replace(".php", "").replace(".html", "")
        t_input = f"{title} {slug}"
        trace.append(f"Virtual Title used: {t_input}")

    t_keywords = extract_core_keywords(t_input)
    
    # --- FUZZY OVERLAP ---
    # Standard intersection
    overlap = q_keywords & t_keywords
    
    # Fallback: if keywords are mashed (e.g. "oneplus9review"), check substring match
    missing_q = q_keywords - t_keywords
    fuzzy_matches = set()
    for mq in missing_q:
        if mq in t_lower_raw or mq in u_lower:
            fuzzy_matches.add(mq)
    
    total_matches = len(overlap | fuzzy_matches)
    base_score = total_matches / len(q_keywords) if q_keywords else 0
    trace.append(f"Overlap: {len(overlap)} + Fuzzy: {len(fuzzy_matches)} / {len(q_keywords)} (Base: {base_score:.2f})")
    
    # -- HEURISTIC: Numerical Integrity --
    q_numbers = {k for k in q_keywords if k.isdigit()}
    t_numbers = {k for k in t_keywords if k.isdigit()}
    
    is_trusted = any(d in u_lower for d in ["gsmarena.com", "wikipedia.org", "devicespecifications.com", "theverge.com", "notebookcheck.net"])

    if q_numbers:
        if not (q_numbers & t_numbers):
            # Leniency for trusted domains if they match on text but miss a ID match
            penalty = 0.4 if is_trusted else 0.8
            base_score *= (1 - penalty) 
            trace.append(f"Penalty -{penalty*100}%: Missing core model number {q_numbers}")
        elif len(q_numbers & t_numbers) < len(q_numbers):
            penalty = 0.2 if is_trusted else 0.4
            base_score *= (1 - penalty)
            trace.append(f"Penalty -{penalty*100}%: Partial model number match")

    # -- HEURISTIC: Variant Precision --
    q_variants = {w.lower() for w in query.split() if w.lower() in DESCRIPTOR_TERMS}
    t_variants = {w.lower() for w in t_input.lower().split() if w.lower() in DESCRIPTOR_TERMS}
    
    is_comparison = (category == "comparison")
    
    if t_variants and not q_variants and not is_comparison:
        penalty = 0.2 if is_trusted else 0.4 
        base_score -= penalty
        trace.append(f"Penalty -{penalty}: Title has unrequested variant {t_variants}")

    # -- HEURISTIC: Trusted Domain Bonus --
    if is_trusted:
        bonus = 0.2
        base_score += bonus
        trace.append(f"Bonus +{bonus}: Source is primary trusted domain.")

    # -- HEURISTIC: Opinions Bonus --
    if "opinion" in t_input.lower() or "review" in t_input.lower():
        bonus = 0.1
        base_score += bonus
        trace.append(f"Bonus +{bonus}: Matches opinion/review intent.")

    # -- HEURISTIC: Specs Bonus --
    if category == "specs" and "specs" not in query.lower():
        bonus = 0.1
        base_score += bonus
        trace.append(f"Bonus +{bonus}: High-value Specification page.")
        
    # -- HEURISTIC: Exact Multi-word Match Bonus --
    if query.lower() in t_input.lower():
        bonus = 0.2
        base_score = base_score + bonus
        trace.append(f"Bonus +{bonus}: Exact sequence match.")
        
    final_score = max(0.0, round(base_score, 3))
    return final_score, category, trace

def is_highly_relevant(query: str, title: str, threshold: float = 0.4) -> bool:
    """Filter helper."""
    score, category, trace = calculate_relevance_score(query, title, "")
    return score >= threshold
