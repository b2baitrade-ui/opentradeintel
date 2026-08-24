"""Local keyword extraction without models or network calls."""

from opentradeintel.normalization.text import normalize_text

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)


def extract_keywords(value: str, limit: int = 20) -> list[str]:
    """Return stable, unique, non-stop-word tokens in first-seen order."""
    if limit <= 0:
        raise ValueError("keyword limit must be positive")
    seen: set[str] = set()
    keywords: list[str] = []
    for token in normalize_text(value).split():
        if token in STOP_WORDS or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) == limit:
            break
    return keywords
