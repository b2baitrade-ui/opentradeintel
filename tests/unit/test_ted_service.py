import json
from pathlib import Path

import httpx2
import pytest

from opentradeintel.collectors import TEDSearchClient, TEDSearchQuery
from opentradeintel.errors import TEDNetworkError
from opentradeintel.ted_service import TEDOpportunityService

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "ted" / "search_success.json"
CATALOG = PROJECT_ROOT / "examples" / "catalogs" / "sample.csv"


def test_service_maps_raw_notices_in_source_order() -> None:
    first = json.loads(FIXTURE.read_text(encoding="utf-8"))["notices"][0]
    second = {"publication-number": "42-2026", "notice-title": {"eng": "Second notice"}}
    payload = {
        "notices": [first, second],
        "totalNoticeCount": 2,
        "iterationNextToken": None,
        "timedOut": False,
    }

    with httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
    ) as http_client:
        service = TEDOpportunityService(client=TEDSearchClient(http_client=http_client))
        tenders = service.search(TEDSearchQuery(keyword="management", limit=2))

    assert [tender.id for tender in tenders] == ["176184-2026", "42-2026"]
    assert all(tender.source == "TED" for tender in tenders)


def test_service_returns_empty_search() -> None:
    payload = {
        "notices": [],
        "totalNoticeCount": 0,
        "iterationNextToken": None,
        "timedOut": False,
    }
    with httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
    ) as http_client:
        service = TEDOpportunityService(client=TEDSearchClient(http_client=http_client))

        assert service.search(TEDSearchQuery(cpv="15897200")) == []


def test_service_composes_ted_mapping_catalog_loading_and_existing_matcher() -> None:
    payload = {
        "notices": [
            {
                "publication-number": "99-2026",
                "notice-title": {"eng": "Organic dried mango"},
                "buyer-name": {"eng": ["Synthetic Public Buyer"]},
                "description-proc": {"eng": "Dried fruit for retail distribution"},
                "place-of-performance": ["DEU"],
            }
        ],
        "totalNoticeCount": 1,
        "iterationNextToken": None,
        "timedOut": False,
    }
    with httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
    ) as http_client:
        service = TEDOpportunityService(client=TEDSearchClient(http_client=http_client))
        responses = service.match_catalog(
            TEDSearchQuery(keyword="dried mango", limit=1),
            CATALOG,
            match_limit=1,
        )

    assert len(responses) == 1
    assert responses[0].tender.id == "99-2026"
    assert responses[0].matches[0].product.sku == "SYN-DM-500"


def test_service_propagates_connector_errors() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("offline", request=request)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        service = TEDOpportunityService(client=TEDSearchClient(http_client=http_client))

        with pytest.raises(TEDNetworkError):
            service.search(TEDSearchQuery(keyword="fruit"))
