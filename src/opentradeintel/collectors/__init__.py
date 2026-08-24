"""Source connector interfaces and built-in implementations."""

from opentradeintel.collectors.base import SourceConnector
from opentradeintel.collectors.files import LocalFileConnector
from opentradeintel.collectors.ted import TEDNoticeMapper, TEDSearchClient, TEDSearchQuery

__all__ = [
    "LocalFileConnector",
    "SourceConnector",
    "TEDNoticeMapper",
    "TEDSearchClient",
    "TEDSearchQuery",
]
