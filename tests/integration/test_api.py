from typing import cast

from fastapi.testclient import TestClient

from opentradeintel.api.app import app

client = TestClient(app)


def match_payload() -> dict[str, object]:
    return {
        "tender": {
            "id": "api-rfq",
            "title": "Organic dried mango",
            "buyer": "Synthetic API Buyer",
            "description": "Dried fruit requirement",
            "products": ["dried mango"],
            "quantity": 1000,
            "unit": "kg",
            "destination": "Germany",
            "currency": "EUR",
            "required_certifications": ["EU Organic"],
            "source": "synthetic-api-test",
        },
        "products": [
            {
                "sku": "API-DM-1",
                "name": "Dried mango",
                "description": "Organic mango slices",
                "category": "Dried fruit",
                "origin": "Exampleland",
                "certifications": ["EU Organic"],
                "min_order_quantity": 100,
                "available_markets": ["EU"],
                "keywords": ["mango", "organic"],
            }
        ],
    }


def test_health_endpoint_reports_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint_reports_package_version() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "0.2.0"}


def test_match_endpoint_uses_deterministic_engine() -> None:
    response = client.post("/match", json=match_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["tender"]["id"] == "api-rfq"
    assert body["matches"][0]["product"]["sku"] == "API-DM-1"
    assert body["matches"][0]["score"] == 100
    assert body["matches"][0]["breakdown"]["total"] == 100


def test_match_endpoint_is_repeatable() -> None:
    first = client.post("/match", json=match_payload())
    second = client.post("/match", json=match_payload())

    assert first.json() == second.json()


def test_match_endpoint_rejects_invalid_product() -> None:
    payload = match_payload()
    products = payload["products"]
    assert isinstance(products, list)
    first_product = cast(dict[str, object], products[0])
    first_product["sku"] = ""

    response = client.post("/match", json=payload)

    assert response.status_code == 422


def test_match_endpoint_rejects_non_positive_limit() -> None:
    payload = match_payload()
    payload["limit"] = 0

    response = client.post("/match", json=payload)

    assert response.status_code == 422
