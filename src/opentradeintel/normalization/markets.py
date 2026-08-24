"""Baseline market aliases used for local compatibility checks."""

from collections.abc import Iterable

from opentradeintel.normalization.text import normalize_text

EU_MARKETS = frozenset(
    {
        "austria",
        "belgium",
        "bulgaria",
        "croatia",
        "cyprus",
        "czechia",
        "denmark",
        "estonia",
        "finland",
        "france",
        "germany",
        "greece",
        "hungary",
        "ireland",
        "italy",
        "latvia",
        "lithuania",
        "luxembourg",
        "malta",
        "netherlands",
        "poland",
        "portugal",
        "romania",
        "slovakia",
        "slovenia",
        "spain",
        "sweden",
    }
)

MARKET_ALIASES = {
    "europe": "eu",
    "european union": "eu",
    "eu": "eu",
    "usa": "united states",
    "us": "united states",
    "u s": "united states",
}


def market_tokens(value: str | Iterable[str]) -> set[str]:
    """Return comparable market tokens and expand EU member destinations."""
    values = [value] if isinstance(value, str) else list(value)
    tokens: set[str] = set()
    for item in values:
        normalized = normalize_text(item)
        if not normalized:
            continue
        canonical = MARKET_ALIASES.get(normalized, normalized)
        tokens.add(canonical)
        if canonical in EU_MARKETS:
            tokens.add("eu")
    return tokens
