# ---- Imports ---- 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

import re
import spacy
from bs4 import BeautifulSoup
import requests

from backend.extractors.extractor_aspect import extract_aspects


from backend.domains.tech import *
from backend.domains.news import *

nlp = spacy.load("en_core_web_sm")
 
# ---- Numeric ---- 

def extract_numeric(sentence, aspects):
    results = []
    sentence_lower = sentence.lower()

    for pattern in TECH_NUMERIC_PATTERNS:
        matches = re.finditer(pattern, sentence_lower)

        for match in matches:
            raw = match.group(1)
            raw = raw.replace(",", "")   # normalize commas
            value = float(raw)
            unit = match.group(2).lower()

            aspect = UNIT_ASPECT_MAPPING.get(unit)
            
            # ---- CONTEXT VALIDATION ----
            context_window = sentence_lower[max(0, match.start()-40):match.end()+40]

            if aspect == "storage" and unit in ["gb", "mb", "tb"]:
                if "ram" in context_window or "memory" in context_window:
                    aspect = "ram"
            
            if not aspect:
                continue

            # require aspect keyword in context
            from backend.domains.tech import ASPECT_KEYWORDS

            valid = False
            for key, words in ASPECT_KEYWORDS.items():
                if key == aspect:
                    if any(w in context_window for w in words):
                        valid = True
                        break

            if not valid:
                continue

            # ---- ADVANCED: POWER CONTEXT ----
            if aspect == "power" and unit in ["w", "watts"]:
                if "wireless" in context_window:
                    aspect = "wireless charging"
                elif "reverse" in context_window:
                    aspect = "reverse charging"
                elif "magsafe" in context_window:
                    aspect = "magsafe"
                elif "charger" in context_window or "charging" in context_window:
                    aspect = "wired charging"
                else:
                    aspect = "wired charging"

            # ---- CONTEXT WINDOW ----
            start = match.start()
            end = match.end()
            context_window = sentence_lower[max(0, start-40):end+40]

            score = 0

            # ---- POSITIVE SIGNALS ----
            POSITIVE_KEYWORDS = [
                "battery", "capacity", "spec", "specs",
                "features", "comes with", "equipped with"
            ]

            for k in POSITIVE_KEYWORDS:
                if k in context_window:
                    score += 1

            # ---- NEGATIVE SIGNALS ----
            NEGATIVE_KEYWORDS = [
                "cell", "cells", "per", "each",
                "module", "teardown", "replacement"
            ]

            for k in NEGATIVE_KEYWORDS:
                if k in context_window:
                    score -= 2

            # ---- DECISION ----
            if score < 0:
                continue

            results.append({
                "aspect": aspect,
                "value": value,
                "unit": unit,
                "type": "numeric"
            })

    return results

# ---- Date ---- 

def is_valid_date(text):
    import re

    months = [
        "january","february","march","april","may","june",
        "july","august","september","october","november","december"
    ]

    text_lower = text.lower()

    if any(m in text_lower for m in months):
        return True

    if re.search(r"\b(19|20)\d{2}\b", text):
        return True

    return False


def extract_dates(sentence, domain="tech"):
    doc = nlp(sentence)
    results = []

    sentence_lower = sentence.lower()

    if domain == "tech":
        keywords = TECH_DATE_KEYWORDS
    else:
        keywords = NEWS_DATE_KEYWORDS

    for ent in doc.ents:
        if ent.label_ == "DATE":
            text = ent.text.strip()

            if not is_valid_date(text):
                continue

            label = "date"

            for key, words in keywords.items():
                if any(w in sentence_lower for w in words):
                    # stricter distance check
                    for w in words:
                        if w in sentence_lower:
                            idx = sentence_lower.find(w)
                            date_idx = sentence_lower.find(text.lower())
                            if abs(idx - date_idx) < 50:
                                label = key
                                break

            if label == "date":
                continue # Skip generic dates without context

            results.append({
                "aspect": label,
                "value": text,
                "type": "date"
            })

    return results


# ---- Named Values ----

def extract_named_values(sentence, aspects):
    results = []
    sentence_lower = sentence.lower()

    for pattern in TECH_NAMED_PATTERNS:
        matches = re.findall(pattern, sentence_lower)

        for match in matches:
            if isinstance(match, tuple):
                match = match[0]

            match_lower = match.lower()

            aspect = None

            for key, keywords in NAMED_ENTITY_MAPPING.items():
                if any(k in match_lower for k in keywords):
                    aspect = key
                    break

            if not aspect:
                aspect = aspects[0] if aspects else "unknown"

            results.append({
                "aspect": aspect,
                "value": match.strip(),
                "unit": None,
                "type": "named"
            })

    return results


# ---- Tables ----

import pandas as pd


def extract_tables(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # ---- TARGET INFOBOX TABLE ----
        tables = soup.find_all("table", {"class": "infobox"})

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                header = row.find("th")
                data = row.find("td")

                if not header or not data:
                    continue

                key = header.get_text(strip=True).lower()
                value = data.get_text(" ", strip=True)

                # ---- NORMALIZE UNICODE ----
                value = (
                    value
                    .replace("\xa0", " ")
                    .replace("·", " ")
                    .replace("╖", " ")
                    .replace("–", "-")
                    .replace("û", "-")
                    .lower()   # 👈 ADD THIS
                )

                if key and value:
                    results.append({
                        "aspect": key,
                        "value": value,
                        "type": "table"
                    })

        return results

    except Exception as e:
        print("[TABLE ERROR]", e)
        return []

def parse_table_numeric(value: str):
    import re

    value_lower = value.lower()

    # normalize units spacing
    value_lower = value_lower.replace("m a h", "mah")
    value_lower = value_lower.replace("w h", "wh")

    # ---- find mah pattern ----
    match = re.search(r"(\d{3,5})\s*mah", value_lower)

    if match:
        return {
            "value": int(match.group(1)),
            "unit": "mah"
        }

    # ---- fallback: wh (convert directly to mAh assuming 3.85V for tech/mobile) ----
    match = re.search(r"(\d+(\.\d+)?)\s*wh", value_lower)

    if match:
        wh_val = float(match.group(1))
        mah_val = round((wh_val * 1000) / 3.85)
        return {
            "value": mah_val,
            "unit": "mah"
        }

    return None


# ---- Function ----

def extract_attributes(sentence, domain="generic"):
    results = []

    aspects = extract_aspects(sentence, domain=domain)

    # ---- domain fallback ----
    if domain == "generic":
        if aspects:
            domain = "tech"   # for now, simple rule

    results.extend(extract_numeric(sentence, aspects))
    results.extend(extract_dates(sentence, domain))
    results.extend(extract_named_values(sentence, aspects))

    # ---- Remove duplicates ----
    unique = []
    seen = set()

    for r in results:
        key = (r["aspect"], str(r["value"]), str(r.get("unit")))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique