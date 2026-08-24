import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from opentradeintel.collectors.ted import TEDNoticeMapper
from opentradeintel.errors import TEDMappingError

FIXTURE = Path(__file__).parents[1] / "fixtures" / "ted" / "search_success.json"


def public_notice() -> dict[str, Any]:
    payload = cast(dict[str, Any], json.loads(FIXTURE.read_text(encoding="utf-8")))
    return cast(dict[str, Any], payload["notices"][0])


def test_mapper_preserves_public_procurement_semantics() -> None:
    tender = TEDNoticeMapper().map_notice(public_notice())

    assert tender.id == "176184-2026"
    assert tender.source == "TED"
    assert tender.source_id == "176184-2026"
    assert tender.source_url == "https://ted.europa.eu/en/notice/-/detail/176184-2026"
    assert (
        tender.title
        == "Italy \u2013 Management-related services \u2013 Management and control services"
    )
    assert tender.buyer == "Giunta Regionale"
    assert tender.description == (
        "Procedura aperta per servizi di gestione e controllo.\n"
        "Servizi di gestione e controllo dell'intervento."
    )
    assert tender.products == []
    assert tender.cpv_codes == ["79420000"]
    assert tender.nuts_codes == ["ITI43", "ITA"]
    assert tender.destination == "ITI43, ITA"
    assert tender.deadline is None
    assert tender.estimated_value == Decimal("6500000.00")
    assert tender.currency == "EUR"
    assert tender.publication_date == date(2026, 3, 13)


def test_mapper_selects_english_then_deterministic_language_fallback() -> None:
    notice = public_notice()
    notice["notice-title"] = {"fra": "Titre français", "eng": "English title"}
    notice["buyer-name"] = {"ita": ["Acquirente"], "deu": ["Beschaffer"]}

    tender = TEDNoticeMapper().map_notice(notice)

    assert tender.title == "English title"
    assert tender.buyer == "Beschaffer"


def test_mapper_uses_earliest_valid_tender_deadline() -> None:
    notice = public_notice()
    notice["deadline-receipt-tender-date-lot"] = [
        "2026-10-01+02:00",
        "2026-09-15Z",
    ]
    notice["deadline-date-lot"] = ["2026-09-20"]

    tender = TEDNoticeMapper().map_notice(notice)

    assert tender.deadline == date(2026, 9, 15)


def test_mapper_accepts_numeric_estimated_value() -> None:
    notice = public_notice()
    notice["estimated-value-proc"] = 125000.5

    tender = TEDNoticeMapper().map_notice(notice)

    assert tender.estimated_value == Decimal("125000.5")


def test_mapper_supplies_neutral_fallbacks_for_missing_optional_fields() -> None:
    tender = TEDNoticeMapper().map_notice({"publication-number": "42-2026"})

    assert tender.title == "TED notice 42-2026"
    assert tender.buyer == "Buyer not specified"
    assert tender.description == "No description supplied by TED."
    assert tender.source_url == "https://ted.europa.eu/en/notice/-/detail/42-2026"
    assert tender.cpv_codes == []
    assert tender.nuts_codes == []
    assert tender.estimated_value is None
    assert tender.publication_date is None


def test_mapper_requires_publication_number() -> None:
    with pytest.raises(TEDMappingError, match="publication-number"):
        TEDNoticeMapper().map_notice({"notice-title": {"eng": "No identifier"}})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("classification-cpv", "79420000"),
        ("place-of-performance", {"code": "DEU"}),
        ("notice-title", ["not multilingual"]),
        ("buyer-name", {"eng": [1]}),
        ("deadline-date-lot", ["not-a-date"]),
        ("estimated-value-proc", "not-a-number"),
        ("estimated-value-cur-proc", 123),
        ("publication-date", "not-a-date"),
        ("links", []),
        ("links", {"html": []}),
    ],
)
def test_mapper_rejects_malformed_relevant_fields(field: str, value: object) -> None:
    notice = public_notice()
    notice[field] = value

    with pytest.raises(TEDMappingError, match=field):
        TEDNoticeMapper().map_notice(notice)
