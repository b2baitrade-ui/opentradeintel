"""Unicode-aware baseline text normalization."""

import unicodedata


def normalize_text(value: str) -> str:
    """Casefold text and replace punctuation or symbols with single spaces."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    characters = (
        " " if unicodedata.category(character)[0] in {"P", "S", "Z"} else character
        for character in normalized
    )
    return " ".join("".join(characters).split())
