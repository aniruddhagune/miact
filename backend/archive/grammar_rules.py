"""
DEPRECATED: Use backend.nlp.grammar_structural instead.
This regex-based module is kept only for regression baseline testing.
"""
from backend.nlp.sentiment_lexicon import POSITIVE_WORDS, NEGATIVE_WORDS, NEGATION_WORDS, INTENSIFIERS
from backend.nlp.grammar_structural import classify_clause, score_clause, is_question, sentence_completeness

# All original functions are now just aliases to the structural version,
# or you can import from grammar_structural directly.
