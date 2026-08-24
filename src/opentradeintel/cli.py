"""Typer command-line interface for OpenTradeIntel."""

import json
import unicodedata
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from opentradeintel import __version__
from opentradeintel.collectors import TEDSearchQuery
from opentradeintel.errors import OpenTradeIntelError
from opentradeintel.models import MatchResponse, Tender
from opentradeintel.normalization import normalize_unit
from opentradeintel.services import OpportunityService
from opentradeintel.ted_service import TEDOpportunityService

app = typer.Typer(
    name="opentradeintel",
    help="Open-source procurement and B2B sourcing intelligence engine.",
    no_args_is_help=True,
)
ted_app = typer.Typer(help="Query and match official public TED procurement notices.")
app.add_typer(ted_app, name="ted")


class OutputFormat(StrEnum):
    """Supported human and machine-readable CLI output formats."""

    TEXT = "text"
    JSON = "json"


class TEDScope(StrEnum):
    """Official TED search scopes."""

    LATEST = "LATEST"
    ACTIVE = "ACTIVE"
    ALL = "ALL"


_BIDI_CONTROL_CLASSES = {
    "ALM",
    "FSI",
    "LRE",
    "LRI",
    "LRM",
    "LRO",
    "PDF",
    "PDI",
    "RLE",
    "RLI",
    "RLM",
    "RLO",
}


def _service() -> OpportunityService:
    return OpportunityService()


def _ted_service() -> TEDOpportunityService:
    return TEDOpportunityService()


def _terminal_text(value: object) -> str:
    """Remove terminal and bidi controls from human-readable untrusted text."""
    return "".join(
        character
        for character in str(value)
        if unicodedata.category(character) not in {"Cc", "Cs"}
        and unicodedata.bidirectional(character) not in _BIDI_CONTROL_CLASSES
    )


def _format_quantity(quantity: Decimal | None, unit: str | None) -> str:
    if quantity is None:
        return "Not specified"
    if quantity == quantity.to_integral_value():
        rendered = f"{int(quantity):,}"
    else:
        rendered = f"{quantity:,.4f}".rstrip("0").rstrip(".")
    normalized_unit = normalize_unit(unit)
    return f"{rendered} {normalized_unit}" if normalized_unit else rendered


def _render_tender(tender: Tender) -> None:
    typer.echo("OpenTradeIntel")
    typer.echo()
    typer.echo("Tender:")
    typer.echo(_terminal_text(tender.title))
    typer.echo(_terminal_text(f"Buyer: {tender.buyer}"))
    typer.echo(_terminal_text(f"Quantity: {_format_quantity(tender.quantity, tender.unit)}"))
    typer.echo(_terminal_text(f"Destination: {tender.destination or 'Not specified'}"))
    typer.echo(_terminal_text(f"Deadline: {tender.deadline or 'Not specified'}"))


def _render_matches(response: MatchResponse) -> None:
    _render_tender(response.tender)
    typer.echo()
    typer.echo("Best matches:")
    if not response.matches:
        typer.echo("No catalog products were supplied.")
        return
    for index, result in enumerate(response.matches, start=1):
        typer.echo()
        typer.echo(_terminal_text(f"{index}. {result.product.name}"))
        typer.echo(_terminal_text(f"   SKU: {result.product.sku}"))
        typer.echo(f"   Score: {result.score}/100")
        typer.echo()
        typer.echo("   Reasons:")
        for reason in result.reasons:
            typer.echo(_terminal_text(f"   [+] {reason}"))
        if result.warnings:
            typer.echo()
            typer.echo("   Warnings:")
            for warning in result.warnings:
                typer.echo(_terminal_text(f"   ! {warning}"))


def _render_ted_search(tenders: list[Tender]) -> None:
    typer.echo(f"TED results: {len(tenders)}")
    if not tenders:
        typer.echo("No TED notices found.")
        return
    for index, tender in enumerate(tenders, start=1):
        typer.echo()
        typer.echo(_terminal_text(f"{index}. {tender.title}"))
        typer.echo(_terminal_text(f"   Publication: {tender.source_id or tender.id}"))
        typer.echo(_terminal_text(f"   Buyer: {tender.buyer}"))
        typer.echo(f"   Deadline: {tender.deadline or 'Not specified'}")
        typer.echo(
            f"   CPV: {', '.join(tender.cpv_codes) if tender.cpv_codes else 'Not specified'}"
        )
        if tender.source_url:
            typer.echo(_terminal_text(f"   URL: {tender.source_url}"))


def _json_output(records: list[Tender] | list[MatchResponse]) -> str:
    return json.dumps(
        [record.model_dump(mode="json") for record in records],
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def _save_json(path: Path, rendered: str, record_count: int, noun: str) -> None:
    path.write_text(f"{rendered}\n", encoding="utf-8")
    typer.echo(_terminal_text(f"Saved {record_count} {noun} to {path}"))


def _ted_query(
    keyword: str | None,
    cpv: str | None,
    country: str | None,
    limit: int,
    scope: TEDScope,
) -> TEDSearchQuery:
    return TEDSearchQuery(
        keyword=keyword,
        cpv=cpv,
        country=country,
        limit=limit,
        scope=scope.value,
    )


def _fail(error: Exception) -> NoReturn:
    typer.echo(_terminal_text(f"Error: {error}"), err=True)
    raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Print the installed OpenTradeIntel version."""
    typer.echo(__version__)


@app.command("inspect")
def inspect_command(
    path: Annotated[Path, typer.Argument(help="Tender JSON or CSV file.")],
) -> None:
    """Validate and summarize one tender file."""
    try:
        _render_tender(_service().inspect_tender(path))
    except (OpenTradeIntelError, ValueError) as error:
        _fail(error)


@app.command("match")
def match_command(
    tender: Annotated[Path, typer.Option("--tender", help="Tender JSON or CSV file.")],
    catalog: Annotated[Path, typer.Option("--catalog", help="Catalog JSON or CSV file.")],
    limit: Annotated[int | None, typer.Option(min=1, help="Maximum number of matches.")] = None,
) -> None:
    """Rank catalog products against one tender."""
    try:
        _render_matches(_service().match_files(tender, catalog, limit=limit))
    except (OpenTradeIntelError, ValueError) as error:
        _fail(error)


@ted_app.command("search")
def ted_search_command(
    query: Annotated[
        str | None,
        typer.Option("--query", help="Full-text keyword or phrase for TED Expert Search."),
    ] = None,
    cpv: Annotated[
        str | None,
        typer.Option(help="Eight-digit CPV code or TED prefix such as 15*."),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option(help="Two-letter EU or three-letter TED place code."),
    ] = None,
    limit: Annotated[int, typer.Option(min=1, max=1000, help="Maximum notices.")] = 10,
    scope: Annotated[TEDScope, typer.Option(help="Official TED search scope.")] = TEDScope.ACTIVE,
    output: Annotated[
        OutputFormat, typer.Option(help="Terminal output format.")
    ] = OutputFormat.TEXT,
    output_file: Annotated[
        Path | None,
        typer.Option(help="Save normalized tenders as JSON."),
    ] = None,
) -> None:
    """Search official public TED notices and normalize them to Tender."""
    try:
        tenders = _ted_service().search(_ted_query(query, cpv, country, limit, scope))
        rendered = _json_output(tenders)
        if output is OutputFormat.JSON:
            typer.echo(rendered)
        else:
            _render_ted_search(tenders)
        if output_file is not None:
            _save_json(output_file, rendered, len(tenders), "normalized tender(s)")
    except (OpenTradeIntelError, OSError, ValueError) as error:
        _fail(error)


@ted_app.command("match")
def ted_match_command(
    catalog: Annotated[Path, typer.Option(help="Local supplier catalog JSON or CSV file.")],
    query: Annotated[
        str | None,
        typer.Option("--query", help="Full-text keyword or phrase for TED Expert Search."),
    ] = None,
    cpv: Annotated[
        str | None,
        typer.Option(help="Eight-digit CPV code or TED prefix such as 15*."),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option(help="Two-letter EU or three-letter TED place code."),
    ] = None,
    limit: Annotated[int, typer.Option(min=1, max=1000, help="Maximum notices.")] = 10,
    match_limit: Annotated[
        int | None,
        typer.Option(min=1, help="Maximum matches per notice."),
    ] = 10,
    scope: Annotated[TEDScope, typer.Option(help="Official TED search scope.")] = TEDScope.ACTIVE,
    output: Annotated[
        OutputFormat, typer.Option(help="Terminal output format.")
    ] = OutputFormat.TEXT,
    output_file: Annotated[
        Path | None,
        typer.Option(help="Save match responses as JSON."),
    ] = None,
) -> None:
    """Search TED and rank one local supplier catalog for every notice."""
    try:
        responses = _ted_service().match_catalog(
            _ted_query(query, cpv, country, limit, scope),
            catalog,
            match_limit=match_limit,
        )
        rendered = _json_output(responses)
        if output is OutputFormat.JSON:
            typer.echo(rendered)
        elif not responses:
            typer.echo("No TED notices found.")
        else:
            for index, response in enumerate(responses, start=1):
                if index > 1:
                    typer.echo()
                    typer.echo("---")
                    typer.echo()
                _render_matches(response)
        if output_file is not None:
            _save_json(output_file, rendered, len(responses), "match response(s)")
    except (OpenTradeIntelError, OSError, ValueError) as error:
        _fail(error)


if __name__ == "__main__":
    app()
