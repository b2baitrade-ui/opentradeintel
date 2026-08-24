"""Small, explicit unit alias table for the baseline workflow."""

from opentradeintel.normalization.text import normalize_text

UNIT_ALIASES = {
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "t": "t",
    "tonne": "t",
    "tonnes": "t",
    "metric ton": "t",
    "metric tons": "t",
    "metric tonne": "t",
    "metric tonnes": "t",
    "piece": "pcs",
    "pieces": "pcs",
    "pc": "pcs",
    "pcs": "pcs",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "l": "l",
}


def normalize_unit(value: str | None) -> str | None:
    """Return a canonical unit when a known alias exists."""
    if value is None:
        return None
    normalized = normalize_text(value)
    if not normalized:
        return None
    return UNIT_ALIASES.get(normalized, normalized)
