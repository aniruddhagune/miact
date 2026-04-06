"""
Module for spaCy-based search result relevance scoring.
Designed to be generic enough for informational queries (e.g. 'India Tax 2025')
while remaining strict for tech products ('OnePlus 9').
"""
import re
from backend.nlp.spacy_loader import nlp

def extract_core_keywords(text: str) -> set[str]:
    """Extract meaning-bearing tokens: Nouns, Proper Nouns, and Numbers."""
    doc = nlp(text.lower())
    keywords = set()
    for token in doc:
        if token.pos_ in ("PROPN", "NOUN", "NUM") and not token.is_stop:
            # We use lemma for nouns to match 'taxes' with 'tax'
            keywords.add(token.lemma_)
    return keywords

def calculate_relevance_score(query: str, title: str) -> float:
    """
    Calculate a 0-1 relevance score based on entity/keyword overlap.
    """
    q_keywords = extract_core_keywords(query)
    if not q_keywords:
        return 0.0
        
    t_keywords = extract_core_keywords(title)
    
    overlap = q_keywords & t_keywords
    base_score = len(overlap) / len(q_keywords)
    
    # -- HEURISTIC: Numerical Integrity --
    q_numbers = {k for k in q_keywords if k.isdigit()}
    t_numbers = {k for k in t_keywords if k.isdigit()}
    
    if q_numbers:
        if not (q_numbers & t_numbers):
            base_score *= 0.1 # Severe penalty for wrong model number
        elif len(q_numbers & t_numbers) < len(q_numbers):
            base_score *= 0.4

    # -- HEURISTIC: Variant Precision --
    from backend.domains.tech import DESCRIPTOR_TERMS
    q_variants = {w.lower() for w in query.split() if w.lower() in DESCRIPTOR_TERMS}
    t_variants = {w.lower() for w in title.lower().split() if w.lower() in DESCRIPTOR_TERMS}
    
    is_comparison = any(x in title.lower() for x in ["vs", "compare", "versus", "or"])
    
    if t_variants and not q_variants and not is_comparison:
        # Title has variant we didn't ask for (e.g. Pro, Ultra)
        base_score -= 0.15 # Demote variants slightly below base model
        
    # -- HEURISTIC: Exact Multi-word Match Bonus --
    if query.lower() in title.lower():
        base_score = min(1.0, base_score + 0.2)
        
    return max(0.0, round(base_score, 3))

def is_highly_relevant(query: str, title: str, threshold: float = 0.6) -> bool:
    """Filter helper."""
    score = calculate_relevance_score(query, title)
    return score >= threshold
