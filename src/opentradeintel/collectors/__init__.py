"""Source connector interfaces and built-in implementations."""

from opentradeintel.collectors.base import SourceConnector
from opentradeintel.collectors.files import LocalFileConnector

__all__ = ["LocalFileConnector", "SourceConnector"]
