import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

import opentradeintel.cli as cli_module
from opentradeintel.cli import app
from opentradeintel.collectors import TEDSearchQuery
from opentradeintel.errors import TEDNetworkError
from opentradeintel.models import MatchResponse, Product, Tender
from opentradeintel.services import OpportunityService

runner = CliRunner()
PROJECT_ROOT = Path(__file__).parents[2]
TENDER_PATH = PROJECT_ROOT / "examples" / "tenders" / "sample.json"
CATALOG_PATH = PROJECT_ROOT / "examples" / "catalogs" / "sample.csv"


def ted_tender() -> Tender:
    return Tender(
        id="176184-2026",
        title="Management and control services",
        buyer="Giunta Regionale",
        description="Public procurement management services.",
        destination="ITI43, ITA",
        source="TED",
        source_id="176184-2026",
        source_url="https://ted.europa.eu/en/notice/-/detail/176184-2026",
        cpv_codes=["79420000"],
        nuts_codes=["ITI43", "ITA"],
        estimated_value=Decimal("6500000"),
        currency="EUR",
        publication_date=date(2026, 3, 13),
    )


class StubTEDService:
    def __init__(self, tenders: list[Tender] | None = None) -> None:
        self.tenders = tenders if tenders is not None else [ted_tender()]
        self.queries: list[TEDSearchQuery] = []
        self.match_arguments: list[tuple[Path, int | None]] = []

    def search(self, query: TEDSearchQuery) -> list[Tender]:
        self.queries.append(query)
        return self.tenders

    def match_catalog(
        self,
        query: TEDSearchQuery,
        catalog_path: str | Path,
        *,
        match_limit: int | None = None,
    ) -> list[MatchResponse]:
        self.queries.append(query)
        self.match_arguments.append((Path(catalog_path), match_limit))
        product = Product(
            sku="SVC-7942",
            name="Management services",
            description="Synthetic supplier service.",
            category="Management services",
            origin="Exampleland",
            available_markets=["EU"],
            keywords=["management", "services"],
            cpv_codes=["79420000"],
        )
        return [
            OpportunityService().match(tender, [product], limit=match_limit)
            for tender in self.tenders
        ]


class FailingTEDService(StubTEDService):
    def search(self, query: TEDSearchQuery) -> list[Tender]:
        raise TEDNetworkError("TED search failed because of a network error")


def test_cli_help_describes_the_tool() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "procurement and B2B sourcing intelligence" in result.stdout
    assert "inspect" in result.stdout
    assert "match" in result.stdout
    assert "ted" in result.stdout


def test_cli_version_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "0.2.0"


def test_cli_inspect_prints_validated_tender_summary() -> None:
    result = runner.invoke(app, ["inspect", str(TENDER_PATH)])

    assert result.exit_code == 0
    assert "Organic dried mango" in result.stdout
    assert "Demo Meridian Buyers Cooperative" in result.stdout
    assert "20,000 kg" in result.stdout
    assert "Germany" in result.stdout


def test_cli_match_prints_computed_results_and_explanations() -> None:
    result = runner.invoke(
        app,
        ["match", "--tender", str(TENDER_PATH), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 0
    assert "Best matches:" in result.stdout
    assert "Dried Mango 500g" in result.stdout
    assert "Score: 100/100" in result.stdout
    assert "Reasons:" in result.stdout
    assert "Product similarity: 40/40" in result.stdout
    assert "Warnings:" in result.stdout


def test_cli_match_output_is_safe_for_ascii_only_terminals() -> None:
    result = runner.invoke(
        app,
        ["match", "--tender", str(TENDER_PATH), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 0
    result.stdout.encode("ascii")


def test_cli_match_reports_missing_file_without_traceback(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    result = runner.invoke(
        app,
        ["match", "--tender", str(missing), "--catalog", str(CATALOG_PATH)],
    )

    assert result.exit_code == 1
    assert "Could not read source file" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_ted_search_outputs_normalized_json_and_builds_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubTEDService()
    monkeypatch.setattr(cli_module, "_ted_service", lambda: service)

    result = runner.invoke(
        app,
        ["ted", "search", "--query", "management", "--limit", "1", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["id"] == "176184-2026"
    assert payload[0]["estimated_value"] == "6500000"
    assert service.queries == [TEDSearchQuery(keyword="management", limit=1)]


def test_cli_ted_search_text_neutralizes_terminal_control_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tender = ted_tender().model_copy(
        update={
            "title": "TED \x1b]0;untrusted-title\x07 \u202espoofed",
            "buyer": "Buyer \x1b[31mred\x1b[0m",
            "source_url": "https://example.test/notice\rspoofed",
        }
    )
    monkeypatch.setattr(cli_module, "_ted_service", lambda: StubTEDService([tender]))

    result = runner.invoke(app, ["ted", "search", "--query", "management"])

    assert result.exit_code == 0
    assert "untrusted-title" in result.stdout
    assert "\x1b" not in result.stdout
    assert "\x07" not in result.stdout
    assert "\r" not in result.stdout
    assert "\u202e" not in result.stdout


def test_cli_ted_search_writes_normalized_json_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubTEDService()
    monkeypatch.setattr(cli_module, "_ted_service", lambda: service)
    output_file = tmp_path / "tenders.json"

    result = runner.invoke(
        app,
        [
            "ted",
            "search",
            "--cpv",
            "79420000",
            "--country",
            "DE",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Saved 1 normalized tender" in result.stdout
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload[0]["source"] == "TED"
    assert service.queries[0].country == "DEU"
    assert service.queries[0].cpv == "79420000"


def test_cli_ted_search_requires_at_least_one_filter() -> None:
    result = runner.invoke(app, ["ted", "search"])

    assert result.exit_code == 1
    assert "at least one of keyword, cpv, or country is required" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_ted_match_uses_shared_service_and_renders_ranked_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubTEDService()
    monkeypatch.setattr(cli_module, "_ted_service", lambda: service)

    result = runner.invoke(
        app,
        [
            "ted",
            "match",
            "--query",
            "management services",
            "--catalog",
            str(CATALOG_PATH),
            "--match-limit",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Management and control services" in result.stdout
    assert "Management services" in result.stdout
    assert "CPV overlap: 79420000" in result.stdout
    assert service.match_arguments == [(CATALOG_PATH, 1)]


def test_cli_ted_match_bounds_default_matches_per_notice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubTEDService()
    monkeypatch.setattr(cli_module, "_ted_service", lambda: service)

    result = runner.invoke(
        app,
        [
            "ted",
            "match",
            "--query",
            "management services",
            "--catalog",
            str(CATALOG_PATH),
        ],
    )

    assert result.exit_code == 0
    assert service.match_arguments == [(CATALOG_PATH, 10)]


def test_cli_ted_search_reports_connector_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_module, "_ted_service", FailingTEDService)

    result = runner.invoke(app, ["ted", "search", "--query", "fruit"])

    assert result.exit_code == 1
    assert "TED search failed because of a network error" in result.stderr
    assert "Traceback" not in result.stderr
