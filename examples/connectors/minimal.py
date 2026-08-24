"""Minimal source-neutral shape for a public procurement connector."""

from collections.abc import Mapping, Sequence
from typing import Protocol

from opentradeintel.models import Tender

RawNotice = Mapping[str, object]


class PublicSearchClient(Protocol):
    """Acquire and validate raw records from one official source."""

    def search(self, query: str) -> Sequence[RawNotice]: ...


class PublicNoticeMapper(Protocol):
    """Map one source record into the generic domain model."""

    def map_notice(self, notice: RawNotice) -> Tender: ...


class MinimalPublicConnector:
    """Compose acquisition and mapping without matching or CLI logic."""

    def __init__(self, client: PublicSearchClient, mapper: PublicNoticeMapper) -> None:
        self._client = client
        self._mapper = mapper

    def collect(self, query: str) -> list[Tender]:
        """Return typed tenders in the official source order."""
        return [self._mapper.map_notice(notice) for notice in self._client.search(query)]
