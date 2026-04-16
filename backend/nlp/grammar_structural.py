"""
Structural Grammar & Sentiment Analyzer using spaCy.
Uses dependency parsing to move beyond simple window-based heuristics.
"""
from __future__ import annotations
import re
from backend.nlp.spacy_loader import nlp
from backend.nlp.sentiment_lexicon import POSITIVE_WORDS, NEGATIVE_WORDS, INTENSIFIERS, POLARITY_INVERTERS, NEGATION_WORDS
from backend.utils.logger import logger

def _is_negated(token) -> bool:
    """
    Check if a token is grammatically negated by walking up the dependency tree
    and counting unique negations on any part of the path.
    """
    neg_tokens = set()
    
    # 1. Check the token itself or its immediate children
    for child in token.children:
        if child.dep_ == "neg":
            neg_tokens.add(child.i)
        
    # 2. Walk up the entire path to the root
    # e.g., "doesn't [root] seem like a good [token] phone"
    # we look at any ancestors that have negation children
    for ancestor in [token] + list(token.ancestors):
        for child in ancestor.children:
            if child.dep_ == "neg" or child.text.lower() in NEGATION_WORDS:
                # If the negation is modifying an inverter (e.g. "no" in "no less than"),
                # we skip it here and let _get_polarity_multiplier handle it.
                if child.head.text.lower() in POLARITY_INVERTERS:
                    continue
                neg_tokens.add(child.i)
            
    # Odd number of unique negations = negated. Even = positive (Double Negation).
    return (len(neg_tokens) % 2) != 0

def _get_intensity(token) -> float:
    """Check for intensifiers in children (adverbs)."""
    adj = 0.0
    for child in token.children:
        if child.pos_ == "ADV":
            adj += INTENSIFIERS.get(child.text.lower(), 0.0)
    return adj

def _get_polarity_multiplier(token) -> int:
    """
    Check for polarity inverters (less, least) in the dependency path.
    Handle cases like "no less than X" where the negation cancels the inversion.
    """
    multiplier = 1
    
    # Check if any ancestor is an inverter, or if we have an inverter child
    
    # 1. Check if the token itself or any ancestor is an inverter
    path = [token] + list(token.ancestors)
    for node in path:
        if node.text.lower() in POLARITY_INVERTERS:
            multiplier *= -1
            # If the inverter node has a negation child, flip back
            for child in node.children:
                if child.dep_ == "neg" or child.text.lower() in NEGATION_WORDS:
                    multiplier *= -1
            return multiplier # Found primary inverter, done
            
    # 2. Check immediate children (standard "less secure")
    for child in token.children:
        if child.text.lower() in POLARITY_INVERTERS:
            multiplier *= -1
            for g in child.children:
                if g.dep_ == "neg" or g.text.lower() in NEGATION_WORDS:
                    multiplier *= -1
            return multiplier

    return multiplier

def score_clause(text: str) -> tuple[float, list[str]]:
    # Pre-process common phrases
    mod_text = text.lower().replace("deal-breaker", "dealbreaker").replace("deal breaker", "dealbreaker")
    doc = nlp(mod_text)
    
    score = 0.0
    matched_terms = []
    
    for token in doc:
        word = token.text.lower()
        signed_base = 0
        
        if word in POSITIVE_WORDS:
            signed_base = 1
        elif word in NEGATIVE_WORDS or word == "dealbreaker":
            signed_base = -1
            
        if signed_base != 0:
            # 1. Apply structural negation (not/never)
            if _is_negated(token):
                signed_base *= -1
                
            # 2. Apply polarity inversion (less/least)
            signed_base *= _get_polarity_multiplier(token)
            
            # 3. Apply intensity/adverbsom adverbs like 'very')
            intensity = _get_intensity(token)
            score += signed_base + (intensity * (1 if signed_base > 0 else -1))
            matched_terms.append(word)
            
    # Phrases that spaCy might miss but are structurally unique
    if "not bad" in mod_text or "no issues" in mod_text:
        score += 0.5 
        
    return score, matched_terms

def is_question(doc) -> bool:
    """Use structural signals for questions."""
    text = doc.text.strip()
    if text.endswith("?"):
        return True
        
    for token in doc:
        # Question words at the start
        if token.i == 0:
            if token.lemma_ in ("what", "where", "who", "whom", "which", "how"):
                return True
            if token.text.lower() == "when":
                if len(doc) > 1 and doc[1].pos_ in ("AUX", "VERB") and doc[1].lemma_ not in ("i", "we", "you"):
                     return True
                return False
                
        # Auxiliary inversion: "Is it good?" (AUX before subject)
        if token.pos_ == "AUX" and token.dep_ == "ROOT":
             for child in token.children:
                 if child.dep_.endswith("subj") and child.i > token.i:
                     return True
                     
    return False

def sentence_completeness(doc) -> str:
    """Check for subject + verb structure."""
    has_subj = any(t.dep_ in ("nsubj", "csubj", "nsubjpass") for t in doc)
    has_verb = any(t.pos_ in ("VERB", "AUX") for t in doc)
    
    if is_question(doc):
        return "question"
    if has_subj and has_verb:
        return "complete"
    return "incomplete"

def classify_clause(text: str, prev_result: dict | None = None) -> dict:
    logger.debug("NLP", f"Analyzing clause structure: '{text[:50]}...'")
    doc = nlp(text)
    score, matched_terms = score_clause(text)
    
    completeness = sentence_completeness(doc)
    question = is_question(doc)
    
    # Rhetorical negative: "Does the battery even last a day?"
    rhetorical_neg = False
    if question:
        hedges = ("even", "ever", "really", "actually", "at all")
        if any(t.text.lower() in hedges for t in doc):
            rhetorical_neg = True
            score = min(score, -0.6)
    
    # Weight questions lower
    if question:
        score *= 0.7
        
    if score > 0.15:
        sentiment = "positive"
    elif score < -0.15:
        sentiment = "negative"
    else:
        sentiment = "neutral"
        
    inherited_aspect = None
    if completeness == "incomplete" and prev_result:
        inherited_aspect = prev_result.get("aspect")
        
    res = {
        "sentiment": sentiment,
        "score": max(-1.0, min(1.0, round(score / 3.0, 3))),
        "matched_terms": matched_terms,
        "metaphor_aspects": [], 
        "comparison_cues": [], 
        "completeness": completeness,
        "is_question": question,
        "inherited_aspect": inherited_aspect
    }
    logger.debug("NLP", f"Clause classification: sentiment={sentiment}, score={res['score']}, complete={completeness}")
    return res
