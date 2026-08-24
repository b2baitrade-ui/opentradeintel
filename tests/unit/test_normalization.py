import pytest

from opentradeintel.normalization import (
    extract_keywords,
    market_tokens,
    normalize_category,
    normalize_text,
    normalize_unit,
)


def test_normalize_text_casefolds_and_collapses_whitespace() -> None:
    assert normalize_text("  Crème\n BRÛLÉE  ") == "crème brûlée"


def test_normalize_text_replaces_punctuation_with_spaces() -> None:
    assert normalize_text("mango—slices, organic! 500g") == "mango slices organic 500g"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("kilograms", "kg"),
        (" KGs. ", "kg"),
        ("metric tonnes", "t"),
        ("pieces", "pcs"),
        ("litres", "l"),
        ("carton", "carton"),
        (None, None),
    ],
)
def test_normalize_unit_maps_common_aliases(raw: str | None, expected: str | None) -> None:
    assert normalize_unit(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Dried Fruits", "dried fruit"),
        ("dehydrated fruit", "dried fruit"),
        ("Food & Beverages", "food and beverage"),
        ("Industrial Pumps", "industrial pumps"),
    ],
)
def test_normalize_category_maps_only_known_aliases(raw: str, expected: str) -> None:
    assert normalize_category(raw) == expected


def test_extract_keywords_removes_stop_words_and_preserves_first_seen_order() -> None:
    text = "Organic mango and dried mango for the retail market"

    assert extract_keywords(text) == ["organic", "mango", "dried", "retail", "market"]


def test_extract_keywords_obeys_limit() -> None:
    assert extract_keywords("alpha beta gamma delta", limit=2) == ["alpha", "beta"]


def test_extract_keywords_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        extract_keywords("mango", limit=0)


def test_market_tokens_expand_named_eu_destination() -> None:
    assert market_tokens("Germany") == {"germany", "eu"}


def test_market_tokens_normalize_lists_and_union_aliases() -> None:
    assert market_tokens(["European Union", " Singapore ", "EU"]) == {"eu", "singapore"}


def test_market_tokens_ignore_empty_values() -> None:
    assert market_tokens(["", "  "]) == set()
