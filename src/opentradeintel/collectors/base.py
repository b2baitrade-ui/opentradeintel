"""Connector protocol for acquiring source data."""

from pathlib import Path
from typing import Protocol


class SourceConnector(Protocol):
    """Read raw text from a source path without interpreting its format."""

    def read_text(self, path: Path) -> str:
        """Return UTF-8 source text."""
        ...
