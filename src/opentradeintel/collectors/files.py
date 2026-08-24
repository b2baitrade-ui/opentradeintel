"""Local filesystem connector."""

from pathlib import Path

from opentradeintel.errors import SourceReadError


class LocalFileConnector:
    """Read UTF-8 data from a local path."""

    def read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8-sig")
        except OSError as error:
            raise SourceReadError(f"Could not read source file '{path}': {error}") from error
