from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from opentradeintel import __version__
from opentradeintel.models import MatchResult, Product, ScoreBreakdown, Tender


def valid_tender_data() -> dict[str, object]:
    return {
        "id": "rfq-001",
        "title": " Organic dried mango ",
        "buyer": "Example Import Cooperative",
        "description": "Food-service packs for retail distribution.",
        "products": [" Dried mango ", "Mango slices"],
        "quantity": "20000.5",
        "unit": " kilograms ",
        "destination": " Germany ",
        "deadline": "2026-09-30",
        "currency": "eur",
        "required_certifications": [" EU Organic ", "HACCP"],
        "source": "synthetic-demo",
    }


def valid_product_data() -> dict[str, object]:
    return {
        "sku": "DM-500",
        "name": " Dried Mango 500g ",
        "description": "Unsweetened dried mango slices.",
        "category": "Dried fruit",
        "origin": "Exampleland",
        "certifications": ["EU Organic", "HACCP"],
        "min_order_quantity": "500",
        "available_markets": ["EU", "Singapore"],
        "keywords": ["mango", "dried fruit", "organic"],
    }


def test_package_version_is_v0_1_0() -> None:
    assert __version__ == "0.1.0"


def test_tender_parses_typed_values_and_trims_strings() -> None:
    tender = Tender.model_validate(valid_tender_data())

    assert tender.title == "Organic dried mango"
    assert tender.products == ["Dried mango", "Mango slices"]
    assert tender.quantity == Decimal("20000.5")
    assert tender.unit == "kilograms"
    assert tender.destination == "Germany"
    assert tender.deadline == date(2026, 9, 30)


def test_tender_uppercases_currency() -> None:
    tender = Tender.model_validate(valid_tender_data())

    assert tender.currency == "EUR"


@pytest.mark.parametrize("currency", ["EU", "EURO", "12A"])
def test_tender_rejects_invalid_currency(currency: str) -> None:
    data = valid_tender_data()
    data["currency"] = currency

    with pytest.raises(ValidationError):
        Tender.model_validate(data)


@pytest.mark.parametrize("quantity", [0, -1])
def test_tender_rejects_non_positive_quantity(quantity: int) -> None:
    data = valid_tender_data()
    data["quantity"] = quantity

    with pytest.raises(ValidationError):
        Tender.model_validate(data)


def test_tender_allows_unknown_optional_commercial_fields() -> None:
    data = valid_tender_data()
    data.update(quantity=None, unit=None, destination=None, deadline=None, currency=None)

    tender = Tender.model_validate(data)

    assert tender.quantity is None
    assert tender.currency is None


def test_product_parses_moq_and_trims_name() -> None:
    product = Product.model_validate(valid_product_data())

    assert product.name == "Dried Mango 500g"
    assert product.min_order_quantity == Decimal("500")


def test_product_rejects_blank_sku() -> None:
    data = valid_product_data()
    data["sku"] = "   "

    with pytest.raises(ValidationError):
        Product.model_validate(data)


def test_product_rejects_non_positive_moq() -> None:
    data = valid_product_data()
    data["min_order_quantity"] = 0

    with pytest.raises(ValidationError):
        Product.model_validate(data)


def test_score_breakdown_total_is_component_sum() -> None:
    breakdown = ScoreBreakdown(
        product_similarity=31,
        category=15,
        certifications=20,
        market=15,
        moq=5,
    )

    assert breakdown.total == 86


def test_score_breakdown_rejects_component_above_maximum() -> None:
    with pytest.raises(ValidationError):
        ScoreBreakdown(
            product_similarity=41,
            category=15,
            certifications=20,
            market=15,
            moq=10,
        )


def test_match_result_requires_score_to_equal_breakdown() -> None:
    product = Product.model_validate(valid_product_data())
    breakdown = ScoreBreakdown(
        product_similarity=40,
        category=15,
        certifications=20,
        market=15,
        moq=10,
    )

    with pytest.raises(ValidationError):
        MatchResult(
            score=99,
            product=product,
            reasons=["matched"],
            warnings=[],
            breakdown=breakdown,
        )
