import json
from decimal import Decimal
from pathlib import Path

from opentradeintel.models import Product, Tender
from opentradeintel.services import OpportunityService


def tender() -> Tender:
    return Tender(
        id="rfq-service",
        title="Dried mango",
        buyer="Synthetic Buyer",
        description="Organic dried fruit",
        products=["mango"],
        quantity=Decimal("1000"),
        unit="kg",
        destination="Germany",
        currency="EUR",
        required_certifications=["EU Organic"],
        source="synthetic-test",
    )


def product() -> Product:
    return Product(
        sku="DM-001",
        name="Dried mango",
        description="Organic slices",
        category="Dried fruit",
        origin="Exampleland",
        certifications=["EU Organic"],
        min_order_quantity=Decimal("100"),
        available_markets=["EU"],
        keywords=["mango", "organic"],
    )


def test_service_matches_in_memory_models() -> None:
    response = OpportunityService().match(tender(), [product()])

    assert response.tender.id == "rfq-service"
    assert response.matches[0].product.sku == "DM-001"
    assert response.matches[0].score == 100


def test_service_applies_match_limit() -> None:
    second = product().model_copy(update={"sku": "DM-002"})

    response = OpportunityService().match(tender(), [product(), second], limit=1)

    assert len(response.matches) == 1


def test_service_inspects_tender_file(tmp_path: Path) -> None:
    path = tmp_path / "tender.json"
    path.write_text(json.dumps(tender().model_dump(mode="json")), encoding="utf-8")

    inspected = OpportunityService().inspect_tender(path)

    assert inspected == tender()


def test_service_matches_tender_and_catalog_files(tmp_path: Path) -> None:
    tender_path = tmp_path / "tender.json"
    catalog_path = tmp_path / "catalog.json"
    tender_path.write_text(json.dumps(tender().model_dump(mode="json")), encoding="utf-8")
    catalog_path.write_text(json.dumps([product().model_dump(mode="json")]), encoding="utf-8")

    response = OpportunityService().match_files(tender_path, catalog_path)

    assert response.matches[0].score == 100
