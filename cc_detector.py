# from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

# analyzer = AnalyzerEngine()
# # Add regex-based CCN recognizer (Visa, MasterCard, Amex, Discover)
# cc_pattern = Pattern(
#     "Credit Card",
#     r"\b(?:4[0-9]{12}(?:[0-9]{3})?"
#     r"|5[1-5][0-9]{14}"
#     r"|3[47][0-9]{13}"
#     r"|6(?:011|5[0-9]{2})[0-9]{12})\b",
#     0.8,
# )
# cc_recognizer = PatternRecognizer(
#     supported_entity="CREDIT_CARD",
#     patterns=[cc_pattern]
# )
# analyzer.registry.add_recognizer(cc_recognizer)

# def detect_credit_cards(text):
#     return analyzer.analyze(
#         text=text,
#         entities=["CREDIT_CARD"],
#         language="en",
#     )
# cc_detector.py (additions at top)

import regex
from pathlib import Path

# reuse full_cc and partial_cc from existing Pattern objects, but as byte‐regex:
BYTES_PATTERN = regex.compile(
    rb"\b(?:(?:\d[ -]?){12}|"
    rb"4[0-9]{3}(?:[ -]?[0-9]{4}){3}|"
    rb"5[1-5][0-9]{2}(?:[ -]?[0-9]{4}){3}|"
    rb"3[47][0-9]{2}(?:[ -]?[0-9]{4}){2}|"
    rb"6(?:011|5[0-9]{2})(?:[ -]?[0-9]{4}){3})\b"
)

def quick_cc_scan(path: str, head=65536, tail=65536) -> bool:
    """
    Read first+last `head`/`tail` bytes of file and run a single regex search.
    Return True if any match—else False.
    """
    p = Path(path)
    size = p.stat().st_size
    try:
        with open(path, "rb") as f:
            data = f.read(head)
            if size > head + tail:
                f.seek(size - tail)
                data += f.read(tail)
    except Exception:
        return False
    return bool(BYTES_PATTERN.search(data))


from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

engine = AnalyzerEngine()

# Full 16-digit CC pattern (spaces or hyphens allowed)
full_cc = Pattern(
    name="full_cc",
    regex=(
        r"\b(?:4[0-9]{3}(?:[ -]?[0-9]{4}){3}"
        r"|5[1-5][0-9]{2}(?:[ -]?[0-9]{4}){3}"
        r"|3[47][0-9]{2}(?:[ -]?[0-9]{4}){2}"
        r"|6(?:011|5[0-9]{2})(?:[ -]?[0-9]{4}){3})\b"
    ),
    score=0.5,
)

# Partial 12-digit prefix (spaces or hyphens allowed)
partial_cc = Pattern(
    name="partial_cc",
    regex=r"\b(?:\d[ -]?){12}\b",
    score=0.3,
)

# Register recognizers: supported_entity first, then patterns, then name
engine.registry.add_recognizer(
    PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[full_cc],
        name="FullCC"),
)
engine.registry.add_recognizer(
    PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[partial_cc],
        name="PartialCC"),
)

def detect_credit_cards(text: str):
    """Return all Presidio results for credit-card patterns in the text."""
    return engine.analyze(text=text, entities=["CREDIT_CARD"], language="en")
