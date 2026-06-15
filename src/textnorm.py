"""Shared text normalization for matching Revit type/material text to SINAPI descriptions.

Normalization is deterministic and pure: same input -> same output. Used both when
parsing (to build a `*_norm` column) and when building the crosswalk shortlist.
"""
import re
import unicodedata

# Parametric / noise tokens common in Revit type names that carry no costing meaning.
_NOISE_PATTERNS = [
    r"\(\s*-+\s*/\s*[^)]*\)",   # "(----/ TINTA)" style placeholders
    r"\(\s*\d+\s*\)",            # trailing "(15)" counters
    r"\be\s*=\s*[\d.,]+\s*mm\b", # "E = 12,5 mm" thickness notes
    r"\bpei\s*[ivx]+\b",         # ceramic PEI ratings
]


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text) -> str:
    """Uppercase, de-accent, strip parametric noise, collapse whitespace/punctuation."""
    if text is None:
        return ""
    s = strip_accents(str(text)).upper()
    for pat in _NOISE_PATTERNS:
        s = re.sub(pat, " ", s, flags=re.IGNORECASE)
    # drop standalone dimension tokens like 100X210, 14X19X29
    s = re.sub(r"\b\d+\s*X\s*\d+(?:\s*X\s*\d+)?\b", " ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokens(text) -> set:
    """Content tokens (drop very short / stopword-like fragments)."""
    stop = {"DE", "DO", "DA", "DOS", "DAS", "E", "EM", "COM", "SEM", "OU", "A", "O", "PARA", "POR"}
    return {t for t in normalize(text).split() if len(t) > 1 and t not in stop}
