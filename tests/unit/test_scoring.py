from opentradeintel.matching import score_product
from opentradeintel.models import Product, Tender


def tender(**overrides: object) -> Tender:
    data: dict[str, object] = {
        "id": "rfq-001",
        "title": "Organic dried mango",
        "buyer": "Synthetic Buyers Guild",
        "description": "Dried fruit for retail distribution",
        "products": ["dried mango"],
        "quantity": 20000,
        "unit": "kg",
        "destination": "Germany",
        "deadline": "2026-09-30",
        "currency": "EUR",
        "required_certifications": ["EU Organic", "HACCP"],
        "source": "synthetic-demo",
    }
    data.update(overrides)
    return Tender.model_validate(data)


def product(**overrides: object) -> Product:
    data: dict[str, object] = {
        "sku": "DM-001",
        "name": "Dried Mango",
        "description": "Unsweetened slices",
        "category": "Dried fruit",
        "origin": "Exampleland",
        "certifications": ["EU Organic", "HACCP"],
        "min_order_quantity": 500,
        "available_markets": ["EU"],
        "keywords": ["mango", "organic"],
    }
    data.update(overrides)
    return Product.model_validate(data)


def test_perfect_product_receives_all_100_points() -> None:
    result = score_product(tender(), product())

    assert result.score == 100
    assert result.breakdown.model_dump() == {
        "product_similarity": 40,
        "category": 15,
        "certifications": 20,
        "market": 15,
        "moq": 10,
        "total": 100,
    }
    assert result.warnings == []


def test_product_similarity_uses_name_and_keyword_coverage() -> None:
    candidate = product(
        name="Dried Mango 500g",
        keywords=["mango", "organic", "unsweetened"],
        category="Unrelated category",
        certifications=[],
        available_markets=["Japan"],
        min_order_quantity=30000,
    )

    result = score_product(tender(), candidate)

    assert result.breakdown.product_similarity == 27
    assert any("Product similarity: 27/40" in reason for reason in result.reasons)


def test_category_scores_only_when_all_category_tokens_appear() -> None:
    matching = score_product(tender(), product(category="Dried fruits"))
    missing = score_product(tender(), product(category="Fresh fruit"))

    assert matching.breakdown.category == 15
    assert missing.breakdown.category == 0
    assert any("Category not found" in warning for warning in missing.warnings)


def test_certification_score_is_proportional_to_required_coverage() -> None:
    result = score_product(tender(), product(certifications=["EU Organic"]))

    assert result.breakdown.certifications == 10
    assert any("HACCP" in warning for warning in result.warnings)


def test_no_certification_requirement_awards_full_component() -> None:
    result = score_product(tender(required_certifications=[]), product(certifications=[]))

    assert result.breakdown.certifications == 20
    assert any("No certifications required" in reason for reason in result.reasons)


def test_named_eu_destination_matches_eu_market() -> None:
    result = score_product(tender(destination="France"), product(available_markets=["Europe"]))

    assert result.breakdown.market == 15
    assert any("Market compatibility: 15/15" in reason for reason in result.reasons)


def test_unsupported_destination_scores_zero_and_warns() -> None:
    result = score_product(tender(destination="Japan"), product(available_markets=["EU"]))

    assert result.breakdown.market == 0
    assert any("Japan" in warning for warning in result.warnings)


def test_missing_destination_has_no_market_restriction() -> None:
    result = score_product(tender(destination=None), product(available_markets=[]))

    assert result.breakdown.market == 15


def test_quantity_at_moq_awards_full_moq_component() -> None:
    result = score_product(tender(quantity=500), product(min_order_quantity=500))

    assert result.breakdown.moq == 10


def test_quantity_below_moq_scores_zero_and_warns() -> None:
    result = score_product(tender(quantity=499), product(min_order_quantity=500))

    assert result.breakdown.moq == 0
    assert any("below MOQ" in warning for warning in result.warnings)


def test_missing_quantity_or_moq_gets_neutral_points_and_warning() -> None:
    missing_quantity = score_product(tender(quantity=None), product())
    missing_moq = score_product(tender(), product(min_order_quantity=None))

    assert missing_quantity.breakdown.moq == 5
    assert missing_moq.breakdown.moq == 5
    assert any("Verify final commercial MOQ" in warning for warning in missing_quantity.warnings)


def test_score_is_repeatable_for_identical_inputs() -> None:
    first = score_product(tender(), product())
    second = score_product(tender(), product())

    assert first == second


def test_exact_cpv_overlap_is_explained_without_changing_score() -> None:
    without_cpv = score_product(tender(), product())
    with_cpv = score_product(
        tender(cpv_codes=["15897200"]),
        product(cpv_codes=["15897200"]),
    )

    assert with_cpv.score == without_cpv.score == 100
    assert with_cpv.breakdown == without_cpv.breakdown
    assert "CPV overlap: 15897200 (tie-break signal; no score impact)" in with_cpv.reasons
