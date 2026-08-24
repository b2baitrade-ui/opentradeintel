"""Provider-agnostic extension interface; the core never requires one."""

from typing import Protocol, runtime_checkable

from opentradeintel.models import Tender


@runtime_checkable
class EnrichmentProvider(Protocol):
    """Optionally enrich a tender while preserving the typed contract."""

    def enrich_tender(self, value: Tender) -> Tender:
        """Return an enriched tender without changing core matching semantics."""
        ...
