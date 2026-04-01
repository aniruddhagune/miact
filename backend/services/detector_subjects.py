import re

# ---- Extract subjects  ----

def extract_subjects(query: str):
    from backend.domains.tech import ASPECT_KEYWORDS

    query = query.lower()

    parts = re.split(r"\bvs\band\b|,", query)

    subjects = []

    # flatten all aspect keywords
    aspect_words = set()
    for words in ASPECT_KEYWORDS.values():
        for w in words:
            aspect_words.add(w)

    for p in parts:
        p = p.strip()
        p = re.sub(r"\s+", " ", p)

        # ---- remove aspect words ----
        words = p.split()
        cleaned_words = [w for w in words if w not in aspect_words]

        cleaned = " ".join(cleaned_words).strip()

        if cleaned:
            subjects.append(cleaned)

    return subjects


# ---- STEP 2: Parse subject structure (for phones at least) ----

def parse_subject(subject: str):
    words = subject.lower().split()

    if not words:
        return None

    brand = words[0]

    iteration = None
    variant = None
    core = []

    # right-to-left parsing
    for w in reversed(words[1:]):
        if w.isdigit() and iteration is None:
            iteration = w
        elif iteration is None:
            core.insert(0, w)
        else:
            variant = w

    return {
        "brand": brand,
        "core": core,
        "iteration": iteration,
        "variant": variant
    }


# ---- STEP 3: Generate aliases (STRUCTURAL) ----

def generate_aliases(parsed):
    aliases = set()

    brand = parsed["brand"]
    core = parsed["core"]
    iteration = parsed["iteration"]
    variant = parsed["variant"]

    # full subject
    full = " ".join(
        [brand] + core +
        ([iteration] if iteration else []) +
        ([variant] if variant else [])
    )
    aliases.add(full)

    # iteration + variant (e.g., "9 pro")
    if iteration and variant:
        aliases.add(f"{iteration} {variant}")

    # iteration only (e.g., "9")
    if iteration:
        aliases.add(iteration)

    # variant only (e.g., "pro")
    if variant:
        aliases.add(variant)

    # core name (e.g., "phone")
    if core:
        aliases.add(" ".join(core))

    return list(aliases)


# ---- STEP 4: Build alias map ----

def build_subject_aliases(subjects):
    alias_map = {}

    for sub in subjects:
        parsed = parse_subject(sub)
        if parsed:
            alias_map[sub] = generate_aliases(parsed)

    return alias_map


# ---- STEP 5: Match strength scoring ----

def match_strength(text: str, aliases: list):
    score = 0

    for alias in aliases:
        if alias in text:
            if " " in alias:        # multi-word → strongest (e.g., "9 pro")
                score += 3
            elif alias.isdigit():  # numbers → medium (e.g., "9")
                score += 2
            else:                  # weak (e.g., "pro")
                score += 1

    return score


# ---- STEP 6: Detect subjects (SCORING-BASED) ----

def detect_subjects(text: str, alias_map):
    text = text.lower()
    scored = []

    # prioritize longer subjects first
    for subject in sorted(alias_map.keys(), key=len, reverse=True):
        score = match_strength(text, alias_map[subject])

        if score > 0:
            scored.append((subject, score))

    if not scored:
        return []

    # keep only strongest matches
    max_score = max(score for _, score in scored)

    return [sub for sub, score in scored if score == max_score]


# ---- STEP 7: Shared context detection ----

def is_shared_context(sentence: str):
    sentence = sentence.lower()

    shared_keywords = [
        "both", "same", "identical",
        "share", "shared", "use the same", "have the same"
    ]

    return any(k in sentence for k in shared_keywords)