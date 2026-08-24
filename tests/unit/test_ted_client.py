import json
from pathlib import Path
from typing import Any, cast

import httpx2
import pytest
from pydantic import ValidationError

from opentradeintel.collectors.ted import TEDSearchClient, TEDSearchQuery
from opentradeintel.errors import (
    TEDHTTPError,
    TEDNetworkError,
    TEDResponseError,
    TEDTimeoutError,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "ted"


def fixture(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def test_query_builds_literal_expert_search_expression() -> None:
    query = TEDSearchQuery(
        keyword='dried "organic" fruit',
        cpv="15*",
        country="DE",
    )

    assert query.expert_query == (
        'FT ~ "dried \\"organic\\" fruit" AND classification-cpv = 15* '
        "AND place-of-performance = DEU"
    )


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"keyword": "   "},
        {"cpv": "123"},
        {"cpv": "123456789"},
        {"country": "ZZ"},
        {"country": "DEUT"},
        {"limit": 0, "keyword": "fruit"},
        {"limit": 1001, "keyword": "fruit"},
        {"page_size": 251, "keyword": "fruit"},
    ],
)
def test_query_rejects_invalid_or_unbounded_input(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        TEDSearchQuery.model_validate(values)


def test_client_sends_official_request_contract_and_configuration() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["url"] = str(request.url)
        captured["user_agent"] = request.headers["user-agent"]
        captured["timeout"] = request.extensions["timeout"]
        captured["body"] = json.loads(request.content)
        return httpx2.Response(200, json=fixture("search_success.json"))

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        notices = TEDSearchClient(
            base_url="https://ted.example.test/",
            timeout=4.5,
            http_client=http_client,
        ).search(TEDSearchQuery(keyword="management", limit=1))

    assert notices[0]["publication-number"] == "176184-2026"
    assert captured["url"] == "https://ted.example.test/v3/notices/search"
    assert str(captured["user_agent"]).startswith("OpenTradeIntel/")
    assert captured["timeout"] == {"connect": 4.5, "read": 4.5, "write": 4.5, "pool": 4.5}
    assert captured["body"] == {
        "query": 'FT ~ "management"',
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "description-proc",
            "description-lot",
            "classification-cpv",
            "main-classification-proc",
            "place-of-performance",
            "deadline-receipt-tender-date-lot",
            "deadline-date-lot",
            "publication-date",
            "estimated-value-proc",
            "estimated-value-cur-proc",
            "links",
        ],
        "page": 1,
        "limit": 1,
        "scope": "ACTIVE",
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER",
        "onlyLatestVersions": True,
    }


def test_client_returns_empty_search_without_extra_requests() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=fixture("search_empty.json"))

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        notices = TEDSearchClient(http_client=http_client).search(TEDSearchQuery(cpv="15897200"))

    assert notices == []
    assert calls == 1


def test_client_paginates_with_bounded_page_sizes() -> None:
    bodies: list[dict[str, object]] = []
    responses = [
        {
            "notices": [{"publication-number": "1-2026"}, {"publication-number": "2-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": None,
            "timedOut": False,
        },
        {
            "notices": [{"publication-number": "3-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": None,
            "timedOut": False,
        },
    ]

    def handler(request: httpx2.Request) -> httpx2.Response:
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=responses[len(bodies) - 1])

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        notices = TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(keyword="fruit", limit=3, page_size=2)
        )

    assert [notice["publication-number"] for notice in notices] == ["1-2026", "2-2026", "3-2026"]
    assert [(body["page"], body["limit"]) for body in bodies] == [(1, 2), (2, 2)]


def test_client_deduplicates_notices_across_pages() -> None:
    responses = [
        {
            "notices": [{"publication-number": "1-2026"}, {"publication-number": "2-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": None,
            "timedOut": False,
        },
        {
            "notices": [{"publication-number": "2-2026"}, {"publication-number": "3-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": None,
            "timedOut": False,
        },
    ]
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        response = responses[calls]
        calls += 1
        return httpx2.Response(200, json=response)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        notices = TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(keyword="fruit", limit=3, page_size=2)
        )

    assert [notice["publication-number"] for notice in notices] == [
        "1-2026",
        "2-2026",
        "3-2026",
    ]
    assert calls == 2


def test_client_rejects_repeated_page_without_unique_progress() -> None:
    calls = 0
    response = {
        "notices": [{"publication-number": "1-2026"}],
        "totalNoticeCount": 100,
        "iterationNextToken": None,
        "timedOut": False,
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=response)

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client,
        pytest.raises(TEDResponseError, match="no new unique notices"),
    ):
        TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(keyword="fruit", limit=2, page_size=1)
        )

    assert calls == 2


def test_client_follows_iteration_tokens() -> None:
    bodies: list[dict[str, object]] = []
    responses = [
        {
            "notices": [{"publication-number": "1-2026"}, {"publication-number": "2-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": "opaque-next-token",
            "timedOut": False,
        },
        {
            "notices": [{"publication-number": "3-2026"}],
            "totalNoticeCount": 3,
            "iterationNextToken": None,
            "timedOut": False,
        },
    ]

    def handler(request: httpx2.Request) -> httpx2.Response:
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=responses[len(bodies) - 1])

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        notices = TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(
                keyword="fruit",
                limit=3,
                page_size=2,
                pagination_mode="ITERATION",
            )
        )

    assert len(notices) == 3
    assert "iterationNextToken" not in bodies[0]
    assert bodies[1]["iterationNextToken"] == "opaque-next-token"
    assert "page" not in bodies[0]
    assert [body["limit"] for body in bodies] == [2, 1]


def test_client_rejects_repeated_iteration_token() -> None:
    calls = 0
    response = {
        "notices": [{"publication-number": "1-2026"}],
        "totalNoticeCount": 10,
        "iterationNextToken": "repeated-token",
        "timedOut": False,
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=response)

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client,
        pytest.raises(TEDResponseError, match="repeated an iteration token"),
    ):
        TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(
                keyword="fruit",
                limit=10,
                page_size=1,
                pagination_mode="ITERATION",
            )
        )

    assert calls == 2


def test_client_rejects_iteration_page_without_unique_progress() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        if calls > 2:
            raise AssertionError("iteration client made a third request without unique progress")
        return httpx2.Response(
            200,
            json={
                "notices": [{"publication-number": "1-2026"}],
                "totalNoticeCount": 100,
                "iterationNextToken": f"fresh-token-{calls}",
                "timedOut": False,
            },
        )

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client,
        pytest.raises(TEDResponseError, match="no new unique notices"),
    ):
        TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(
                keyword="fruit",
                limit=2,
                page_size=1,
                pagination_mode="ITERATION",
            )
        )

    assert calls == 2


def test_client_never_returns_more_than_requested_limit() -> None:
    response = {
        "notices": [{"publication-number": "1-2026"}, {"publication-number": "2-2026"}],
        "totalNoticeCount": 2,
        "iterationNextToken": None,
        "timedOut": False,
    }

    with httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=response))
    ) as http_client:
        notices = TEDSearchClient(http_client=http_client).search(
            TEDSearchQuery(keyword="fruit", limit=1)
        )

    assert [notice["publication-number"] for notice in notices] == ["1-2026"]


@pytest.mark.parametrize("fixture_name", ["search_malformed.json"])
def test_client_rejects_malformed_response_schema(fixture_name: str) -> None:
    with (
        httpx2.Client(
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(200, json=fixture(fixture_name))
            )
        ) as http_client,
        pytest.raises(TEDResponseError, match="schema"),
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))


def test_client_rejects_malformed_json() -> None:
    with (
        httpx2.Client(
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(200, content=b"{not-json")
            )
        ) as http_client,
        pytest.raises(TEDResponseError, match="JSON"),
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))


def test_client_rejects_declared_oversized_response_before_reading() -> None:
    with (
        httpx2.Client(
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(
                    200,
                    headers={"Content-Length": "65"},
                    content=b"{}",
                )
            )
        ) as http_client,
        pytest.raises(TEDResponseError, match="response exceeded 64 bytes"),
    ):
        TEDSearchClient(http_client=http_client, max_response_bytes=64).search(
            TEDSearchQuery(keyword="fruit")
        )


def test_client_rejects_streamed_response_that_crosses_size_limit() -> None:
    response = {
        "notices": [{"publication-number": "1-2026"}],
        "totalNoticeCount": 1,
        "iterationNextToken": None,
        "timedOut": False,
    }
    body = json.dumps(response).encode()

    with (
        httpx2.Client(
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(
                    200,
                    headers={"Content-Length": "1"},
                    content=body,
                )
            )
        ) as http_client,
        pytest.raises(TEDResponseError, match="response exceeded 64 bytes"),
    ):
        TEDSearchClient(http_client=http_client, max_response_bytes=64).search(
            TEDSearchQuery(keyword="fruit")
        )


def test_client_maps_http_status_without_echoing_response_body() -> None:
    body = "sensitive-or-very-large-body"
    with (
        httpx2.Client(
            transport=httpx2.MockTransport(
                lambda request: httpx2.Response(400, text=body, request=request)
            )
        ) as http_client,
        pytest.raises(TEDHTTPError, match="HTTP 400") as caught,
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))

    assert body not in str(caught.value)


def test_client_maps_timeout() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("timed out", request=request)

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client,
        pytest.raises(TEDTimeoutError, match="timed out"),
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))


def test_client_maps_network_failure() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("offline", request=request)

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client,
        pytest.raises(TEDNetworkError, match="network"),
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))


def test_client_rejects_server_side_search_timeout() -> None:
    response = {
        "notices": [],
        "totalNoticeCount": 0,
        "iterationNextToken": None,
        "timedOut": True,
    }
    with (
        httpx2.Client(
            transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=response))
        ) as http_client,
        pytest.raises(TEDResponseError, match="server timed out"),
    ):
        TEDSearchClient(http_client=http_client).search(TEDSearchQuery(keyword="fruit"))
