"""Application use cases for official TED search and local matching."""

from pathlib import Path

from opentradeintel.collectors import TEDNoticeMapper, TEDSearchClient, TEDSearchQuery
from opentradeintel.models import MatchResponse, Tender
from opentradeintel.parsers import load_catalog
from opentradeintel.services import OpportunityService


class TEDOpportunityService:
    """Compose TED ingestion with the existing transport-neutral match service."""

    def __init__(
        self,
        *,
        client: TEDSearchClient | None = None,
        mapper: TEDNoticeMapper | None = None,
        opportunity_service: OpportunityService | None = None,
    ) -> None:
        self._client = client or TEDSearchClient()
        self._mapper = mapper or TEDNoticeMapper()
        self._opportunity_service = opportunity_service or OpportunityService()

    def search(self, query: TEDSearchQuery) -> list[Tender]:
        """Search TED and map notices to generic validated tenders."""
        return [self._mapper.map_notice(notice) for notice in self._client.search(query)]

    def match_catalog(
        self,
        query: TEDSearchQuery,
        catalog_path: str | Path,
        *,
        match_limit: int | None = None,
    ) -> list[MatchResponse]:
        """Search TED once and match every normalized tender to one local catalog."""
        products = load_catalog(Path(catalog_path))
        return [
            self._opportunity_service.match(tender, products, limit=match_limit)
            for tender in self.search(query)
        ]
