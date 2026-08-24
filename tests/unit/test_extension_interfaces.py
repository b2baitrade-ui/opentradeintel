from decimal import Decimal

from opentradeintel.mcp import OpenTradeIntelMCPAdapter
from opentradeintel.models import Product, Tender
from opentradeintel.providers import EnrichmentProvider


def tender() -> Tender:
    return Tender(
        id="extension-rfq",
        title="Dried mango",
        buyer="Synthetic Extension Buyer",
        description="Organic dried fruit",
        products=["mango"],
        quantity=Decimal("1000"),
        unit="kg",
        destination="Germany",
        currency="EUR",
        required_certifications=["EU Organic"],
        source="synthetic-extension-test",
    )


def product() -> Product:
    return Product(
        sku="EXT-DM-1",
        name="Dried mango",
        description="Organic slices",
        category="Dried fruit",
        origin="Exampleland",
        certifications=["EU Organic"],
        min_order_quantity=Decimal("100"),
        available_markets=["EU"],
        keywords=["mango", "organic"],
    )


def test_mcp_adapter_delegates_to_core_service_without_sdk() -> None:
    response = OpenTradeIntelMCPAdapter().match_opportunity(tender(), [product()])

    assert response.matches[0].score == 100
    assert response.matches[0].product.sku == "EXT-DM-1"


def test_enrichment_provider_is_an_optional_structural_protocol() -> None:
    class LocalProvider:
        def enrich_tender(self, value: Tender) -> Tender:
            return value

    assert isinstance(LocalProvider(), EnrichmentProvider)
