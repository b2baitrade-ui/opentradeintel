"""Application service shared by CLI, HTTP, and extension adapters."""

from collections.abc import Sequence
from pathlib import Path

from opentradeintel.matching import DeterministicMatcher
from opentradeintel.models import MatchResponse, Product, Tender
from opentradeintel.parsers import load_catalog, load_tender


class OpportunityService:
    """Orchestrate ingestion and matching without transport-specific behavior."""

    def __init__(self, matcher: DeterministicMatcher | None = None) -> None:
        self._matcher = matcher or DeterministicMatcher()

    def inspect_tender(self, path: str | Path) -> Tender:
        """Load one tender file into the validated domain model."""
        return load_tender(Path(path))

    def match(
        self,
        tender: Tender,
        products: Sequence[Product],
        limit: int | None = None,
    ) -> MatchResponse:
        """Match in-memory models through the deterministic engine."""
        matches = self._matcher.match(tender, products, limit=limit)
        return MatchResponse(tender=tender, matches=matches)

    def match_files(
        self,
        tender_path: str | Path,
        catalog_path: str | Path,
        limit: int | None = None,
    ) -> MatchResponse:
        """Load tender and catalog files, then return ranked matches."""
        tender = load_tender(Path(tender_path))
        products = load_catalog(Path(catalog_path))
        return self.match(tender, products, limit=limit)
