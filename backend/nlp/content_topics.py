"""
Module 2: Content Topic Extractor

After scraping a page's text, determine what the article is about:
- Primary subjects (role-weighted noun TF-IDF)
- Named entities (PERSON, ORG, GPE via spaCy NER)
- Subject-verb-object relationship triples (via textacy)
- Event type classification (cross-ref with news categories)
- Inferred domain

Uses spaCy md for POS/dep/NER and textacy for SVO extraction.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Optional

from backend.nlp.spacy_loader import nlp
from backend.config.variables import DEBUG
from backend.utils.text_helpers import split_into_sentences

# ---- Static English IDF baseline (Strategy 1) ----
# Pre-computed approximate IDF values from English Wikipedia frequency data.
# Words not in this dict default to IDF = 6.0 (moderately rare).
# This is a starter set; can be expanded from a full Wikipedia dump later.
_STATIC_IDF = {
    # Ultra-common (near-zero information value)
    "the": 0.01, "is": 0.05, "are": 0.05, "was": 0.05, "were": 0.05,
    "has": 0.1, "have": 0.1, "had": 0.1, "be": 0.1, "been": 0.1,
    "it": 0.1, "this": 0.15, "that": 0.15, "its": 0.15,
    # Common but slightly informative
    "phone": 1.5, "device": 1.8, "review": 2.0, "product": 2.0,
    "company": 2.0, "model": 2.2, "year": 1.5, "time": 1.2,
    "new": 1.0, "first": 1.5, "also": 0.8, "one": 0.9,
    "people": 1.8, "said": 1.5, "like": 1.0, "just": 0.8,
    # Tech domain (moderately rare in general English)
    "battery": 4.2, "camera": 3.8, "display": 3.5, "screen": 3.5,
    "processor": 4.8, "ram": 5.0, "storage": 4.0, "charging": 4.5,
    "software": 3.5, "performance": 3.0, "design": 2.8,
    "snapdragon": 8.0, "mediatek": 8.0, "dimensity": 8.5,
    "megapixel": 7.0, "pixel": 4.5, "sensor": 5.0,
    # News domain
    "killed": 5.0, "injured": 5.2, "dead": 4.5, "accident": 5.0,
    "crash": 4.8, "explosion": 5.5, "fire": 3.5, "earthquake": 6.0,
    "election": 4.5, "government": 3.5, "minister": 4.5,
    "president": 4.0, "police": 3.8, "court": 4.0,
    "war": 4.0, "attack": 4.2, "bomb": 5.5,
}

_DEFAULT_IDF = 6.0  # Words not in the baseline are assumed moderately rare

# Dependency role weights for TF computation
_ROLE_WEIGHTS = {
    "nsubj": 3.0,     # Grammatical subject — the thing the sentence is about
    "nsubjpass": 3.0,  # Passive subject
    "dobj": 2.0,       # Direct object — the thing being acted upon
    "pobj": 1.5,       # Prepositional object
    "attr": 2.0,       # Predicate attribute ("X is Y")
    "conj": 1.5,       # Coordinated items
    "appos": 2.0,      # Appositives
    "compound": 1.0,   # Part of a compound noun
}

# Location-signaling prepositions — pobj children of these get extra weight
_LOCATION_PREPS = {"in", "at", "near", "from", "around", "outside", "across"}


def _get_idf(word: str) -> float:
    """Look up IDF from the static baseline. Unknown words get default."""
    return _STATIC_IDF.get(word.lower(), _DEFAULT_IDF)


def _extract_weighted_nouns(doc) -> dict[str, float]:
    """
    Walk spaCy doc and build role-weighted TF scores for nouns.
    """
    scores: dict[str, float] = {}

    for token in doc:
        if token.pos_ not in ("NOUN", "PROPN"):
            continue

        word = token.lemma_.lower()
        if len(word) <= 2 or token.is_stop:
            continue

        # Base weight from dependency role
        weight = _ROLE_WEIGHTS.get(token.dep_, 1.0)

        # Boost for PROPN (named entities tend to be more important)
        if token.pos_ == "PROPN":
            weight *= 1.5

        # Boost for location prepositions
        if token.dep_ == "pobj" and token.head.text.lower() in _LOCATION_PREPS:
            weight *= 1.5

        scores[word] = scores.get(word, 0.0) + weight

    return scores


def _compute_tfidf(tf_scores: dict[str, float]) -> dict[str, float]:
    """Multiply role-weighted TF by static IDF."""
    return {word: tf * _get_idf(word) for word, tf in tf_scores.items()}


def _extract_named_entities(doc) -> dict[str, list[str]]:
    """Extract NER entities grouped by label."""
    entities: dict[str, set[str]] = {}
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG", "GPE", "LOC", "DATE", "MONEY", "PRODUCT"):
            label = ent.label_
            if label not in entities:
                entities[label] = set()
            entities[label].add(ent.text)

    return {k: list(v) for k, v in entities.items()}


def _extract_svo_triples(doc) -> list[dict]:
    """
    Extract subject-verb-object triples using textacy.
    Falls back to manual extraction if textacy is not available.
    """
    triples = []

    try:
        import textacy.extract
        raw_triples = list(textacy.extract.subject_verb_object_triples(doc))
        for subj, verb, obj in raw_triples:
            # textacy returns Span objects; join their tokens
            s = " ".join([t.text for t in subj]).strip()
            v = " ".join([t.text for t in verb]).strip()
            o = " ".join([t.text for t in obj]).strip()
            if s and v and o:
                triples.append({"subject": s, "verb": v, "object": o})
    except ImportError:
        # Fallback: manual SVO from dependency tree
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                subj = None
                obj = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        # Expand compound children
                        compounds = [c.text for c in child.lefts if c.dep_ == "compound"]
                        subj = " ".join(compounds + [child.text])
                    elif child.dep_ == "dobj":
                        compounds = [c.text for c in child.lefts if c.dep_ == "compound"]
                        obj = " ".join(compounds + [child.text])
                    elif child.dep_ == "acomp" or child.dep_ == "attr":
                        obj = child.text

                if subj and obj:
                    triples.append({"subject": subj, "verb": token.text, "object": obj})

    return triples


def _extract_attributive_relations(doc) -> list[dict]:
    """
    Extract non-SVO attributive relations from spec-list patterns.
    E.g., "phone with 5000mAh battery" → (phone, has-attribute, 5000mAh battery)
    """
    relations = []

    for token in doc:
        # Pattern: NOUN/PROPN + prep("with"/"featuring") + pobj
        if token.dep_ == "prep" and token.text.lower() in ("with", "featuring", "including"):
            head_noun = token.head
            if head_noun.pos_ in ("NOUN", "PROPN"):
                for child in token.children:
                    if child.dep_ == "pobj":
                        # Expand the full noun phrase
                        phrase_tokens = [c.text for c in child.lefts if c.dep_ in ("compound", "amod", "nummod")]
                        phrase_tokens.append(child.text)
                        phrase = " ".join(phrase_tokens)

                        head_compounds = [c.text for c in head_noun.lefts if c.dep_ == "compound"]
                        head_phrase = " ".join(head_compounds + [head_noun.text])

                        relations.append({
                            "subject": head_phrase,
                            "verb": "has-attribute",
                            "object": phrase,
                        })

    return relations


def _classify_event_type(tfidf_scores: dict[str, float]) -> str | None:
    """Cross-reference top nouns with news categories to classify event type."""
    from backend.domains.news import NEWS_CATEGORIES

    category_scores: dict[str, float] = {}
    for category, keywords in NEWS_CATEGORIES.items():
        score = sum(tfidf_scores.get(kw, 0.0) for kw in keywords)
        if score > 0:
            category_scores[category] = score

    if not category_scores:
        return None

    return max(category_scores, key=category_scores.get)


def _infer_domain(tfidf_scores: dict[str, float]) -> str:
    """Infer the content domain from top-scoring terms."""
    from backend.domains.domain_signals import DOMAIN_SIGNALS

    domain_scores: dict[str, float] = {}
    for domain, signals in DOMAIN_SIGNALS.items():
        score = sum(tfidf_scores.get(s, 0.0) for s in signals)
        if score > 0:
            domain_scores[domain] = score

    if not domain_scores:
        return "general"

    return max(domain_scores, key=domain_scores.get)


def extract_content_topics(
    text: str,
    sentences: list[str] | None = None,
    max_sentences: int = 50,
) -> dict:
    """
    Main entry point. Analyze scraped article text for topics and structure.

    Args:
        text: Full article text
        sentences: Pre-split sentences (optional, saves re-splitting)
        max_sentences: Cap on sentences to process (performance guard)

    Returns:
        {
            "primary_subjects": [...],       # Top 5 nouns by TF-IDF
            "named_entities": {...},          # {PERSON: [...], ORG: [...], GPE: [...]}
            "noun_tfidf": {...},              # Full TF-IDF scores
            "relationships": [...],           # SVO triples + attributive relations
            "event_type": str | None,         # news category if applicable
            "inferred_domain": str,           # tech_phone, news_accident, etc.
            "dates_mentioned": [...],         # DATE entities from NER
        }
    """
    if sentences is None:
        sentences = split_into_sentences(text)

    # Cap for performance
    sentences = sentences[:max_sentences]

    # Accumulate across all sentences
    all_tf: dict[str, float] = {}
    all_ner: dict[str, set[str]] = {}
    all_svo: list[dict] = []
    all_attr: list[dict] = []
    all_dates: set[str] = set()

    for sent in sentences:
        if len(sent.strip()) < 10:
            continue

        doc = nlp(sent)

        # Weighted noun TF
        sent_tf = _extract_weighted_nouns(doc)
        for word, score in sent_tf.items():
            all_tf[word] = all_tf.get(word, 0.0) + score

        # NER
        sent_ner = _extract_named_entities(doc)
        for label, ents in sent_ner.items():
            if label == "DATE":
                all_dates.update(ents)
            else:
                if label not in all_ner:
                    all_ner[label] = set()
                all_ner[label].update(ents)

        # SVO triples
        all_svo.extend(_extract_svo_triples(doc))

        # Attributive relations
        all_attr.extend(_extract_attributive_relations(doc))

    # Compute TF-IDF
    tfidf = _compute_tfidf(all_tf)

    # Primary subjects: top 5 by TF-IDF score
    sorted_terms = sorted(tfidf.items(), key=lambda x: x[1], reverse=True)
    primary_subjects = [term for term, _ in sorted_terms[:5]]

    # Deduplicate relationships
    seen_rels = set()
    unique_rels = []
    for rel in all_svo + all_attr:
        key = (rel["subject"].lower(), rel["verb"].lower(), rel["object"].lower())
        if key not in seen_rels:
            seen_rels.add(key)
            unique_rels.append(rel)

    # Classify
    event_type = _classify_event_type(tfidf)
    inferred_domain = _infer_domain(tfidf)

    result = {
        "primary_subjects": primary_subjects,
        "named_entities": {k: list(v) for k, v in all_ner.items()},
        "noun_tfidf": {k: round(v, 2) for k, v in sorted_terms[:20]},
        "relationships": unique_rels[:15],  # Cap output size
        "event_type": event_type,
        "inferred_domain": inferred_domain,
        "dates_mentioned": sorted(all_dates),
    }

    if DEBUG:
        print(f"[content_topics] primary_subjects={primary_subjects[:3]}, "
              f"domain={inferred_domain}, event={event_type}, "
              f"NER_count={sum(len(v) for v in all_ner.values())}, "
              f"triples={len(unique_rels)}")

    return result
