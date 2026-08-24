"""Format-dispatching ingestion helpers."""

from pathlib import Path

from opentradeintel.collectors import LocalFileConnector, SourceConnector
from opentradeintel.errors import UnsupportedFormatError
from opentradeintel.models import Product, Tender
from opentradeintel.parsers.base import CatalogParser, TenderParser
from opentradeintel.parsers.csv_parser import CSVCatalogParser, CSVTenderParser
from opentradeintel.parsers.json_parser import JSONCatalogParser, JSONTenderParser

TENDER_PARSERS: dict[str, TenderParser] = {
    ".json": JSONTenderParser(),
    ".csv": CSVTenderParser(),
}
CATALOG_PARSERS: dict[str, CatalogParser] = {
    ".json": JSONCatalogParser(),
    ".csv": CSVCatalogParser(),
}


def _parser_for[T](path: Path, parsers: dict[str, T]) -> T:
    suffix = path.suffix.lower()
    try:
        return parsers[suffix]
    except KeyError as error:
        supported = ", ".join(sorted(parsers))
        raise UnsupportedFormatError(
            f"Unsupported format '{suffix or '<none>'}' for '{path}'. Supported: {supported}"
        ) from error


def load_tender(path: Path, connector: SourceConnector | None = None) -> Tender:
    """Read and validate one tender selected by file extension."""
    active_connector = connector or LocalFileConnector()
    parser = _parser_for(path, TENDER_PARSERS)
    return parser.parse(active_connector.read_text(path), path)


def load_catalog(path: Path, connector: SourceConnector | None = None) -> list[Product]:
    """Read and validate a product catalog selected by file extension."""
    active_connector = connector or LocalFileConnector()
    parser = _parser_for(path, CATALOG_PARSERS)
    return parser.parse(active_connector.read_text(path), path)
