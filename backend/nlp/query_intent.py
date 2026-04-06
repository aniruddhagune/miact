"""
Module 1: Query Intent Analyzer

Given a raw user query and optionally a page title, produce a structured
intent object describing what the user wants to know.

Uses spaCy dependency parsing and POS tagging to extract:
- Entities (PROPN/NUM chains)
- Aspects (NOUN tokens in subject/object positions)
- Intent specificity (broad / specific / comparative)
- Intent type (factual / opinion / exploratory)
- Title relevance score (when a title is provided)
"""
from __future__ import annotations

import re
from backend.nlp.spacy_loader import nlp
from backend.config.variables import DEBUG


# ---- Intent signal word sets ----

OPINION_SIGNALS = {
    "review", "worth", "good", "bad", "best", "worst", "recommend",
    "opinion", "experience", "how is", "how are", "should i",
    "pros", "cons", "comparison", "versus",
}

FACTUAL_SIGNALS = {
    "specs", "specifications", "spec", "price", "cost", "how much",
    "what is the", "how many", "weight", "dimensions", "release date",
    "features", "size", "resolution", "capacity",
}

TEMPORAL_SIGNALS = {
    "upcoming": "unreleased",
    "expected": "unreleased",
    "rumored": "unreleased",
    "rumoured": "unreleased",
    "leaked": "unreleased",
    "leak": "unreleased",
    "launch date": "unreleased",
    "release date": "ambiguous",  # could be asking about a past or future release
    "discontinued": "discontinued",
    "old": "discontinued",
    "replaced by": "discontinued",
}

COMPARISON_SIGNALS = {"vs", "versus", "compared to", "compared with", "or"}


def _extract_entity_chunks(doc) -> list[str]:
    """
    Extract contiguous PROPN/NUM chains as entity names.
    E.g., "Samsung Galaxy S23 Ultra" → ["samsung galaxy s23 ultra"]
    """
    entities = []
    current_chunk = []

    for token in doc:
        if token.pos_ in ("PROPN", "NUM") or (
            token.pos_ == "NOUN" and token.dep_ == "compound"
        ):
            current_chunk.append(token.text.lower())
        else:
            if current_chunk:
                entities.append(" ".join(current_chunk))
                current_chunk = []

    if current_chunk:
        entities.append(" ".join(current_chunk))

    return entities


def _extract_aspect_nouns(doc) -> dict[str, int]:
    """
    Extract NOUN tokens in meaningful dependency positions and count their frequency.
    For short queries, we also include compound and ROOT deps since queries
    often lack full sentence structure (e.g., "OnePlus 9 battery specs").
    Returns {noun: count}.
    """
    freq = {}
    for token in doc:
        if token.pos_ != "NOUN":
            continue
        # Include broader dep roles — queries are fragments, not sentences
        if token.dep_ in ("nsubj", "dobj", "pobj", "attr", "conj", "appos",
                          "ROOT", "compound"):
            word = token.lemma_.lower()
            # Skip generic filler nouns
            if word in ("thing", "part", "feature", "system", "way", "lot", "kind"):
                continue
            if len(word) <= 2:
                continue
            freq[word] = freq.get(word, 0) + 1

    return freq


def _detect_intent_type(query_lower: str) -> str:
    """Classify the query as factual, opinion-seeking, or exploratory."""
    for signal in OPINION_SIGNALS:
        if signal in query_lower:
            return "opinion"

    for signal in FACTUAL_SIGNALS:
        if signal in query_lower:
            return "factual"

    return "exploratory"


def _detect_entity_temporal_state(query_lower: str) -> str | None:
    """Check if query contains temporal signals about entity state."""
    for signal, state in TEMPORAL_SIGNALS.items():
        if signal in query_lower:
            return state
    return None


def _compute_title_relevance(query_doc, title: str) -> float:
    """
    Compute a 0-1 relevance score between the query and a page title.
    Uses token overlap weighted by POS importance.
    """
    title_doc = nlp(title.lower())

    query_tokens = set()
    for t in query_doc:
        if t.pos_ in ("PROPN", "NUM", "NOUN") and not t.is_stop:
            query_tokens.add(t.text.lower())

    if not query_tokens:
        return 0.0

    title_tokens = set()
    for t in title_doc:
        if not t.is_stop:
            title_tokens.add(t.text.lower())

    overlap = query_tokens & title_tokens
    return len(overlap) / len(query_tokens)


def analyze_query_intent(query: str, title: str = None) -> dict:
    """
    Main entry point. Analyze a user query for intent.

    Args:
        query: Raw user query string
        title: Optional page title for relevance scoring

    Returns:
        {
            "entities": [...],
            "aspects": [...],
            "aspect_frequency": {...},
            "intent_specificity": "broad" | "specific" | "comparative",
            "intent_type": "factual" | "opinion" | "exploratory",
            "is_comparison": bool,
            "temporal_state": "unreleased" | "discontinued" | None,
            "title_relevance": float | None,
        }
    """
    doc = nlp(query)
    query_lower = query.lower()

    # Extract entities and aspects
    entities = _extract_entity_chunks(doc)
    aspect_freq = _extract_aspect_nouns(doc)
    aspects = list(aspect_freq.keys())

    # Comparison detection
    is_comparison = any(sig in query_lower for sig in COMPARISON_SIGNALS)
    # Also check for spaCy-detected coordination between PROPN chains
    if not is_comparison:
        for token in doc:
            if token.dep_ == "cc" and token.text.lower() in ("or",):
                is_comparison = True
                break

    # Intent classification
    if is_comparison:
        specificity = "comparative"
    elif aspects:
        specificity = "specific"
    else:
        specificity = "broad"

    intent_type = _detect_intent_type(query_lower)
    temporal_state = _detect_entity_temporal_state(query_lower)

    # Title relevance (optional)
    title_relevance = None
    if title:
        title_relevance = round(_compute_title_relevance(doc, title), 3)

    result = {
        "entities": entities,
        "aspects": aspects,
        "aspect_frequency": aspect_freq,
        "intent_specificity": specificity,
        "intent_type": intent_type,
        "is_comparison": is_comparison,
        "temporal_state": temporal_state,
        "title_relevance": title_relevance,
    }

    if DEBUG:
        print(f"[query_intent] '{query}' → specificity={specificity}, "
              f"type={intent_type}, entities={entities}, aspects={aspects}, "
              f"temporal={temporal_state}")

    return result
