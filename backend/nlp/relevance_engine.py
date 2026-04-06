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
    
    # 1. Comparison
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["comparison"]) or "/compare" in u_lower:
        return "comparison"
        
    # 2. Rumored
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["rumored"]):
        return "rumored"
        
    # 3. News
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["news"]) or "/news/" in u_lower:
        return "news"
        
    # 4. Review
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["review"]) or "-review-" in u_lower:
        return "review"
        
    # 5. Specs (Standard GSMArena product page is specs)
    if any(k in t_lower for k in URL_TYPE_KEYWORDS["specs"]):
        return "specs"
    
    # GSM product pattern: gsmarena.com/iphone_13-11103.php (Brand_Model-ID.php)
    if "gsmarena.com" in u_lower and re.search(r"-\d+\.php", u_lower):
        return "specs"
        
    return "unknown"

def extract_core_keywords(text: str) -> set[str]:
    """Extract meaning-bearing tokens: Nouns, Proper Nouns, and Numbers."""
    doc = nlp(text.lower())
    keywords = set()
    for token in doc:
        if token.pos_ in ("PROPN", "NOUN", "NUM") and not token.is_stop:
            keywords.add(token.lemma_)
    return keywords

def calculate_relevance_score(query: str, title: str, url: str = "") -> tuple[float, str, list[str]]:
    """
    Calculate a 0-1 relevance score, category, and trace steps.
    """
    trace = []
    category = get_result_type(url, title)
    trace.append(f"Detected Category: {category}")

    q_keywords = extract_core_keywords(query)
    if not q_keywords:
        return 0.0, category, ["Empty Query"]
        
    t_keywords = extract_core_keywords(title)
    
    overlap = q_keywords & t_keywords
    base_score = len(overlap) / len(q_keywords)
    trace.append(f"Keyword overlap: {len(overlap)}/{len(q_keywords)} (Base: {base_score:.2f})")
    
    # -- HEURISTIC: Numerical Integrity --
    q_numbers = {k for k in q_keywords if k.isdigit()}
    t_numbers = {k for k in t_keywords if k.isdigit()}
    
    if q_numbers:
        if not (q_numbers & t_numbers):
            penalty = 0.8
            base_score *= (1 - penalty) # Severe penalty for wrong model number
            trace.append(f"Penalty -{penalty*100}%: Missing core model number {q_numbers}")
        elif len(q_numbers & t_numbers) < len(q_numbers):
            penalty = 0.4
            base_score *= (1 - penalty)
            trace.append(f"Penalty -{penalty*100}%: Partial model number match")

    # -- HEURISTIC: Variant Precision --
    q_variants = {w.lower() for w in query.split() if w.lower() in DESCRIPTOR_TERMS}
    t_variants = {w.lower() for w in title.lower().split() if w.lower() in DESCRIPTOR_TERMS}
    
    is_comparison = (category == "comparison")
    
    if t_variants and not q_variants and not is_comparison:
        # Title has variant we didn't ask for (e.g. Pro, Ultra, Mini)
        penalty = 0.4 
        base_score -= penalty
        trace.append(f"Penalty -{penalty}: Title has unrequested variant {t_variants}")

    # -- HEURISTIC: Comparison Demotion --
    if is_comparison and "vs" not in query.lower() and "compare" not in query.lower():
        penalty = 0.2
        base_score -= penalty
        trace.append(f"Penalty -{penalty}: Result is comparison, while query is direct.")

    # -- HEURISTIC: Specs Bonus --
    if category == "specs" and "specs" not in query.lower():
        bonus = 0.1
        base_score += bonus
        trace.append(f"Bonus +{bonus}: High-value Specification page.")
        
    # -- HEURISTIC: Exact Multi-word Match Bonus --
    if query.lower() in title.lower():
        bonus = 0.2
        base_score = base_score + bonus
        trace.append(f"Bonus +{bonus}: Exact sequence match.")
        
    final_score = max(0.0, round(base_score, 3))
    return final_score, category, trace

def is_highly_relevant(query: str, title: str, threshold: float = 0.4) -> bool:
    """Filter helper."""
    score, category, trace = calculate_relevance_score(query, title, "")
    return score >= threshold
