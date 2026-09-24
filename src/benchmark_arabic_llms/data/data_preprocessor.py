"""
This file provides Arabic text normalization and preprocessing utilities.
It removes diacritics, unifies character forms, and cleans datasets by standardizing all text fields.
"""

import re
from typing import List, Dict, Any

ARABIC_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652]")


def normalize_arabic(text: str) -> str:
    text = str(text)

    text = re.sub(ARABIC_DIACRITICS, "", text)
    text = re.sub("[إأآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ؤ", "و", text)
    text = re.sub("ئ", "ي", text)
    text = re.sub("ة", "ه", text)
    text = re.sub("ـ", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Preprocess a list of dict records with keys like 'text' and 'summary'.
    """
    cleaned = []
    for rec in records:
        new_rec = {}
        for key, value in rec.items():
            if isinstance(value, str):
                new_rec[key] = normalize_arabic(value)
            else:
                new_rec[key] = value
        cleaned.append(new_rec)
    print("Data Preprocessed !")
    return cleaned
