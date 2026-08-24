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


class TEDClientError(OpenTradeIntelError):
    """Base exception for expected failures in the public TED client."""


class TEDTimeoutError(TEDClientError):
    """Raised when a TED HTTP request exceeds its configured timeout."""


class TEDNetworkError(TEDClientError):
    """Raised when TED cannot be reached due to a transport failure."""


class TEDHTTPError(TEDClientError):
    """Raised when TED returns a non-success HTTP status."""


class TEDResponseError(TEDClientError):
    """Raised when TED returns invalid JSON, schema, or timeout state."""


class TEDMappingError(OpenTradeIntelError):
    """Raised when a TED notice cannot be mapped to a Tender."""
