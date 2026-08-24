"""Typer command-line interface for OpenTradeIntel."""

from decimal import Decimal
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from opentradeintel import __version__
from opentradeintel.errors import OpenTradeIntelError
from opentradeintel.models import MatchResponse, Tender
from opentradeintel.normalization import normalize_unit
from opentradeintel.services import OpportunityService

app = typer.Typer(
    name="opentradeintel",
    help="Open-source procurement and B2B sourcing intelligence engine.",
    no_args_is_help=True,
)


def _service() -> OpportunityService:
    return OpportunityService()


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
    typer.echo(tender.title)
    typer.echo(f"Buyer: {tender.buyer}")
    typer.echo(f"Quantity: {_format_quantity(tender.quantity, tender.unit)}")
    typer.echo(f"Destination: {tender.destination or 'Not specified'}")
    typer.echo(f"Deadline: {tender.deadline or 'Not specified'}")


def _render_matches(response: MatchResponse) -> None:
    _render_tender(response.tender)
    typer.echo()
    typer.echo("Best matches:")
    if not response.matches:
        typer.echo("No catalog products were supplied.")
        return
    for index, result in enumerate(response.matches, start=1):
        typer.echo()
        typer.echo(f"{index}. {result.product.name}")
        typer.echo(f"   SKU: {result.product.sku}")
        typer.echo(f"   Score: {result.score}/100")
        typer.echo()
        typer.echo("   Reasons:")
        for reason in result.reasons:
            typer.echo(f"   [+] {reason}")
        if result.warnings:
            typer.echo()
            typer.echo("   Warnings:")
            for warning in result.warnings:
                typer.echo(f"   ! {warning}")


def _fail(error: Exception) -> NoReturn:
    typer.echo(f"Error: {error}", err=True)
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


if __name__ == "__main__":
    app()
