"""Minimal FastAPI application backed by the shared service."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from opentradeintel import __version__
from opentradeintel.api.schemas import HealthResponse, MatchRequest, VersionResponse
from opentradeintel.errors import OpenTradeIntelError
from opentradeintel.models import MatchResponse
from opentradeintel.services import OpportunityService


def get_service() -> OpportunityService:
    """Create the stateless application service used by request handlers."""
    return OpportunityService()


def create_app() -> FastAPI:
    """Build the HTTP adapter without duplicating domain behavior."""
    application = FastAPI(
        title="OpenTradeIntel",
        description="Open-source procurement and B2B sourcing intelligence engine.",
        version=__version__,
    )

    @application.exception_handler(OpenTradeIntelError)
    async def domain_error_handler(_request: Request, error: OpenTradeIntelError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(error)})

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.get("/version", response_model=VersionResponse, tags=["system"])
    def version() -> VersionResponse:
        return VersionResponse(version=__version__)

    @application.post("/match", response_model=MatchResponse, tags=["matching"])
    def match_opportunity(
        payload: MatchRequest,
        service: Annotated[OpportunityService, Depends(get_service)],
    ) -> MatchResponse:
        return service.match(payload.tender, payload.products, limit=payload.limit)

    return application


app = create_app()
