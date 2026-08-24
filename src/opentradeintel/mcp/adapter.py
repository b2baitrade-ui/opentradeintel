"""Core adapter ready to be registered by a future MCP runtime."""

from collections.abc import Sequence

from opentradeintel.models import MatchResponse, Product, Tender
from opentradeintel.services import OpportunityService


class OpenTradeIntelMCPAdapter:
    """Expose matching with an MCP-friendly method and no SDK dependency."""

    def __init__(self, service: OpportunityService | None = None) -> None:
        self._service = service or OpportunityService()

    def match_opportunity(
        self,
        tender: Tender,
        products: Sequence[Product],
        limit: int | None = None,
    ) -> MatchResponse:
        """Delegate an opportunity match to the shared application service."""
        return self._service.match(tender, products, limit=limit)
