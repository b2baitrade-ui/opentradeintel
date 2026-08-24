from decimal import Decimal

import pytest

from opentradeintel.matching import DeterministicMatcher
from opentradeintel.models import Product, Tender


def tender() -> Tender:
    return Tender(
        id="rfq-001",
        title="Dried mango",
        buyer="Synthetic Buyers Guild",
        description="Organic dried fruit",
        products=["mango"],
        quantity=Decimal("1000"),
        unit="kg",
        destination="Germany",
        currency="EUR",
        required_certifications=["EU Organic"],
        source="synthetic-demo",
    )


def product(sku: str, name: str, category: str = "Dried fruit") -> Product:
    return Product(
        sku=sku,
        name=name,
        description="Synthetic catalog item",
        category=category,
        origin="Exampleland",
        certifications=["EU Organic"],
        min_order_quantity=Decimal("100"),
        available_markets=["EU"],
        keywords=["mango"],
    )


def test_matcher_orders_products_by_descending_score() -> None:
    matcher = DeterministicMatcher()
    low = product("LOW", "Steel pump", category="Industrial pumps")
    high = product("HIGH", "Dried mango")

    results = matcher.match(tender(), [low, high])

    assert [result.product.sku for result in results] == ["HIGH", "LOW"]


def test_matcher_uses_casefolded_sku_as_stable_tie_breaker() -> None:
    matcher = DeterministicMatcher()
    products = [product("beta", "Dried mango"), product("Alpha", "Dried mango")]

    results = matcher.match(tender(), products)

    assert [result.product.sku for result in results] == ["Alpha", "beta"]


def test_matcher_prefers_exact_cpv_overlap_for_equal_scores() -> None:
    matcher = DeterministicMatcher()
    opportunity = tender().model_copy(update={"cpv_codes": ["15897200"]})
    no_overlap = product("Alpha", "Dried mango").model_copy(update={"cpv_codes": ["15897300"]})
    overlap = product("Zulu", "Dried mango").model_copy(update={"cpv_codes": ["15897200"]})

    results = matcher.match(opportunity, [no_overlap, overlap])

    assert [result.product.sku for result in results] == ["Zulu", "Alpha"]
    assert results[0].score == results[1].score


def test_matcher_prefers_more_exact_cpv_overlaps_before_sku() -> None:
    matcher = DeterministicMatcher()
    opportunity = tender().model_copy(update={"cpv_codes": ["15897200", "15897300"]})
    one_overlap = product("Alpha", "Dried mango").model_copy(update={"cpv_codes": ["15897200"]})
    two_overlaps = product("Zulu", "Dried mango").model_copy(
        update={"cpv_codes": ["15897200", "15897300"]}
    )

    results = matcher.match(opportunity, [one_overlap, two_overlaps])

    assert [result.product.sku for result in results] == ["Zulu", "Alpha"]


def test_matcher_limit_returns_only_requested_count() -> None:
    products = [product("A", "Dried mango"), product("B", "Dried mango")]

    results = DeterministicMatcher().match(tender(), products, limit=1)

    assert len(results) == 1


@pytest.mark.parametrize("limit", [0, -1])
def test_matcher_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        DeterministicMatcher().match(tender(), [], limit=limit)


def test_matcher_accepts_empty_catalog() -> None:
    assert DeterministicMatcher().match(tender(), []) == []


def test_matcher_does_not_reorder_input_catalog() -> None:
    products = [product("B", "Dried mango"), product("A", "Dried mango")]

    DeterministicMatcher().match(tender(), products)

    assert [item.sku for item in products] == ["B", "A"]
