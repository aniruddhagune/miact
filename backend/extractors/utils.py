import re

def clean_text(text: str):
    # remove references like [1], [23], especially from wikipedia
    text = re.sub(r'\[\d+\]', '', text)

    # normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_into_sentences(text: str):
    # Step 1: normal sentence split
    sentences = re.split(r'(?<=[.!?]) +', text)

    final_sentences = []

    for s in sentences:
        # Step 2: split longer sentences
        if len(s) > 200:
            parts = re.split(r';|, and |, but ', s)
            final_sentences.extend(parts)
        else:
            final_sentences.append(s)

    return [s.strip() for s in final_sentences if s.strip()]
