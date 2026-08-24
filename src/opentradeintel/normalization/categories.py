"""Conservative category aliases for deterministic matching."""

from opentradeintel.normalization.text import normalize_text

CATEGORY_ALIASES = {
    "dried fruits": "dried fruit",
    "dehydrated fruit": "dried fruit",
    "dehydrated fruits": "dried fruit",
    "food beverages": "food and beverage",
    "foods beverages": "food and beverage",
}


def normalize_category(value: str) -> str:
    """Normalize a category and map only explicit baseline aliases."""
    normalized = normalize_text(value)
    return CATEGORY_ALIASES.get(normalized, normalized)
