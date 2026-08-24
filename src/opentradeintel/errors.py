"""User-facing domain errors raised by OpenTradeIntel."""


class OpenTradeIntelError(Exception):
    """Base exception for expected OpenTradeIntel failures."""


class SourceReadError(OpenTradeIntelError):
    """Raised when a connector cannot read its source."""


class UnsupportedFormatError(OpenTradeIntelError):
    """Raised when no parser exists for a file extension."""


class ParseError(OpenTradeIntelError):
    """Raised when a source is syntactically invalid or has the wrong shape."""


class DataValidationError(OpenTradeIntelError):
    """Raised when a parsed record violates the domain model."""
