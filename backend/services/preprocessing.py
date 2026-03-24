import re


def clean_text(text: str):
    # remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_into_sentences(text: str):
    # simple sentence split
    sentences = re.split(r'(?<=[.!?]) +', text)

    return [s.strip() for s in sentences if s.strip()]