from backend.domains.domain_signals import DOMAIN_SIGNALS


def detect_domain(text: str):
    text = text.lower()

    scores = {}

    for domain, signals in DOMAIN_SIGNALS.items():
        scores[domain] = sum(1 for s in signals if s in text)

    # get best match
    best_domain = max(scores, key=scores.get)

    if scores[best_domain] == 0:
        return "generic"

    return best_domain