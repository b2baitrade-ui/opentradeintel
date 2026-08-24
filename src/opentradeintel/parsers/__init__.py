"""JSON and CSV ingestion entry points."""

from opentradeintel.parsers.loader import load_catalog, load_tender

__all__ = ["load_catalog", "load_tender"]
