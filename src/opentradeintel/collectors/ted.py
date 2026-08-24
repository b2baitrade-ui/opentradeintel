"""Official TED Search API connector and deterministic notice mapping."""

import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Self

import httpx2
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
    model_validator,
)
from pydantic import ValidationError as PydanticValidationError

from opentradeintel import __version__
from opentradeintel.errors import (
    TEDHTTPError,
    TEDMappingError,
    TEDNetworkError,
    TEDResponseError,
    TEDTimeoutError,
)
from opentradeintel.models import Tender

TED_SEARCH_PATH = "/v3/notices/search"
TED_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
TED_TENDER_FIELDS = (
    "publication-number",
    "notice-title",
    "buyer-name",
    "description-proc",
    "description-lot",
    "classification-cpv",
    "main-classification-proc",
    "place-of-performance",
    "deadline-receipt-tender-date-lot",
    "deadline-date-lot",
    "publication-date",
    "estimated-value-proc",
    "estimated-value-cur-proc",
    "links",
)

_EU_ALPHA2_TO_TED = {
    "AT": "AUT",
    "BE": "BEL",
    "BG": "BGR",
    "HR": "HRV",
    "CY": "CYP",
    "CZ": "CZE",
    "DE": "DEU",
    "DK": "DNK",
    "EE": "EST",
    "ES": "ESP",
    "FI": "FIN",
    "FR": "FRA",
    "GR": "GRC",
    "HU": "HUN",
    "IE": "IRL",
    "IT": "ITA",
    "LT": "LTU",
    "LU": "LUX",
    "LV": "LVA",
    "MT": "MLT",
    "NL": "NLD",
    "PL": "POL",
    "PT": "PRT",
    "RO": "ROU",
    "SE": "SWE",
    "SI": "SVN",
    "SK": "SVK",
}


class TEDSearchQuery(BaseModel):
    """Validated inputs for one bounded official TED expert search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    keyword: str | None = Field(default=None, max_length=500)
    cpv: str | None = None
    country: str | None = None
    limit: int = Field(default=10, ge=1, le=1000)
    page_size: int = Field(default=250, ge=1, le=250)
    scope: Literal["LATEST", "ACTIVE", "ALL"] = "ACTIVE"
    pagination_mode: Literal["PAGE_NUMBER", "ITERATION"] = "PAGE_NUMBER"

    @field_validator("keyword", mode="before")
    @classmethod
    def normalize_keyword(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("cpv", mode="before")
    @classmethod
    def normalize_cpv(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        code = value.strip()
        if not (re.fullmatch(r"\d{8}", code) or re.fullmatch(r"\d{2,7}\*", code)):
            raise ValueError("CPV must be eight digits or a 2-7 digit TED prefix ending in '*'")
        return code

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        code = value.strip().upper()
        if len(code) == 2:
            try:
                return _EU_ALPHA2_TO_TED[code]
            except KeyError as error:
                raise ValueError(f"unsupported two-letter EU country code: {code}") from error
        if re.fullmatch(r"[A-Z]{3}", code):
            return code
        raise ValueError("country must be a supported two-letter EU or three-letter TED code")

    @model_validator(mode="after")
    def require_filter(self) -> Self:
        if self.keyword is None and self.cpv is None and self.country is None:
            raise ValueError("at least one of keyword, cpv, or country is required")
        return self

    @property
    def expert_query(self) -> str:
        """Render filters in a stable TED Expert Search order."""
        expressions: list[str] = []
        if self.keyword is not None:
            escaped = self.keyword.replace("\\", "\\\\").replace('"', '\\"')
            expressions.append(f'FT ~ "{escaped}"')
        if self.cpv is not None:
            expressions.append(f"classification-cpv = {self.cpv}")
        if self.country is not None:
            expressions.append(f"place-of-performance = {self.country}")
        return " AND ".join(expressions)


class _TEDSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notices: list[dict[str, Any]]
    total_notice_count: StrictInt = Field(alias="totalNoticeCount", ge=0)
    iteration_next_token: str | None = Field(default=None, alias="iterationNextToken")
    timed_out: StrictBool = Field(alias="timedOut")


class TEDSearchClient:
    """Synchronous client for the public, no-auth TED Search API."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.ted.europa.eu",
        timeout: float = 15.0,
        max_response_bytes: int = TED_MAX_RESPONSE_BYTES,
        user_agent: str | None = None,
        http_client: httpx2.Client | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("TED base URL must not be blank")
        if timeout <= 0:
            raise ValueError("TED timeout must be positive")
        if isinstance(max_response_bytes, bool) or max_response_bytes <= 0:
            raise ValueError("TED maximum response size must be positive")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_response_bytes = max_response_bytes
        self._user_agent = user_agent or (
            f"OpenTradeIntel/{__version__} (+https://github.com/b2baitrade-ui/opentradeintel)"
        )
        self._http_client = http_client

    def search(self, query: TEDSearchQuery) -> list[dict[str, Any]]:
        """Return at most `query.limit` raw notices across bounded API pages."""
        if self._http_client is not None:
            return self._search_with_client(self._http_client, query)
        with httpx2.Client() as http_client:
            return self._search_with_client(http_client, query)

    def _search_with_client(
        self,
        http_client: httpx2.Client,
        query: TEDSearchQuery,
    ) -> list[dict[str, Any]]:
        notices: list[dict[str, Any]] = []
        seen_publication_numbers: set[str] = set()
        raw_notice_count = 0
        page = 1
        iteration_token: str | None = None
        seen_tokens: set[str] = set()

        while len(notices) < query.limit:
            request_limit = min(
                query.page_size,
                query.limit
                if query.pagination_mode == "PAGE_NUMBER"
                else query.limit - len(notices),
            )
            body = self._request_body(query, page, iteration_token, request_limit)
            response = self._post(http_client, body)
            raw_notice_count += len(response.notices)
            added = 0
            for notice in response.notices:
                publication_number = notice.get("publication-number")
                if isinstance(publication_number, str) and publication_number.strip():
                    identity = publication_number.strip()
                    if identity in seen_publication_numbers:
                        continue
                    seen_publication_numbers.add(identity)
                notices.append(notice)
                added += 1
                if len(notices) >= query.limit:
                    break

            if len(notices) >= query.limit or not response.notices:
                break
            if query.pagination_mode == "PAGE_NUMBER":
                if raw_notice_count >= response.total_notice_count:
                    break
                if added == 0:
                    raise TEDResponseError("TED pagination made no new unique notices")
                page += 1
                continue

            iteration_token = response.iteration_next_token
            if iteration_token is None:
                break
            if iteration_token in seen_tokens:
                raise TEDResponseError("TED response repeated an iteration token")
            if added == 0:
                raise TEDResponseError("TED pagination made no new unique notices")
            seen_tokens.add(iteration_token)

        return notices

    @staticmethod
    def _request_body(
        query: TEDSearchQuery,
        page: int,
        iteration_token: str | None,
        request_limit: int,
    ) -> dict[str, object]:
        body: dict[str, object] = {
            "query": query.expert_query,
            "fields": list(TED_TENDER_FIELDS),
            "limit": request_limit,
            "scope": query.scope,
            "checkQuerySyntax": False,
            "paginationMode": query.pagination_mode,
            "onlyLatestVersions": True,
        }
        if query.pagination_mode == "PAGE_NUMBER":
            body["page"] = page
        elif iteration_token is not None:
            body["iterationNextToken"] = iteration_token
        return body

    def _post(
        self,
        http_client: httpx2.Client,
        body: dict[str, object],
    ) -> _TEDSearchResponse:
        try:
            with http_client.stream(
                "POST",
                f"{self._base_url}{TED_SEARCH_PATH}",
                json=body,
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            ) as raw_response:
                if not 200 <= raw_response.status_code < 300:
                    raise TEDHTTPError(f"TED search returned HTTP {raw_response.status_code}")

                content_length = raw_response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        declared_size = int(content_length)
                    except ValueError:
                        declared_size = 0
                    if declared_size > self._max_response_bytes:
                        raise TEDResponseError(
                            f"TED response exceeded {self._max_response_bytes} bytes"
                        )

                content = bytearray()
                for chunk in raw_response.iter_bytes():
                    if len(content) + len(chunk) > self._max_response_bytes:
                        raise TEDResponseError(
                            f"TED response exceeded {self._max_response_bytes} bytes"
                        )
                    content.extend(chunk)
        except httpx2.TimeoutException as error:
            raise TEDTimeoutError(
                f"TED search timed out after {self._timeout:g} seconds"
            ) from error
        except httpx2.RequestError as error:
            raise TEDNetworkError("TED search failed because of a network error") from error

        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, ValueError) as error:
            raise TEDResponseError("TED search returned invalid JSON") from error
        try:
            response = _TEDSearchResponse.model_validate(payload)
        except PydanticValidationError as error:
            raise TEDResponseError(
                "TED search response does not match the expected schema"
            ) from error
        if response.timed_out:
            raise TEDResponseError("TED search server timed out before completing the response")
        return response


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        if stripped and stripped not in seen:
            result.append(stripped)
            seen.add(stripped)
    return result


def _string_list(notice: dict[str, Any], field: str) -> list[str]:
    raw = notice.get(field)
    if raw is None:
        return []
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise TEDMappingError(f"TED field '{field}' must be an array of strings")
    return _unique_strings(raw)


def _multilingual_texts(notice: dict[str, Any], field: str) -> list[str]:
    raw = notice.get(field)
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise TEDMappingError(f"TED field '{field}' must be a multilingual object")

    by_language: dict[str, list[str]] = {}
    for language, value in raw.items():
        if not isinstance(language, str):
            raise TEDMappingError(f"TED field '{field}' contains an invalid language key")
        if isinstance(value, str):
            texts = [value]
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            texts = value
        else:
            raise TEDMappingError(f"TED field '{field}' contains invalid text values")
        selected = _unique_strings(texts)
        if selected:
            by_language[language.casefold()] = selected

    if not by_language:
        return []
    language = "eng" if "eng" in by_language else sorted(by_language)[0]
    return by_language[language]


def _date_values(notice: dict[str, Any], field: str) -> list[date]:
    raw_values = _string_list(notice, field)
    result: list[date] = []
    for raw_value in raw_values:
        try:
            result.append(date.fromisoformat(raw_value[:10]))
        except ValueError as error:
            raise TEDMappingError(f"TED field '{field}' contains an invalid date") from error
    return result


def _optional_date(notice: dict[str, Any], field: str) -> date | None:
    raw = notice.get(field)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise TEDMappingError(f"TED field '{field}' must be a date string")
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError as error:
        raise TEDMappingError(f"TED field '{field}' contains an invalid date") from error


def _optional_decimal(notice: dict[str, Any], field: str) -> Decimal | None:
    raw = notice.get(field)
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)):
        raise TEDMappingError(f"TED field '{field}' must be a decimal-compatible value")
    try:
        return Decimal(str(raw).strip())
    except InvalidOperation as error:
        raise TEDMappingError(f"TED field '{field}' contains an invalid number") from error


def _notice_url(notice: dict[str, Any], publication_number: str) -> str:
    links = notice.get("links")
    fallback = f"https://ted.europa.eu/en/notice/-/detail/{publication_number}"
    if links is None:
        return fallback
    if not isinstance(links, dict):
        raise TEDMappingError("TED field 'links' must be an object")
    html = links.get("html")
    if html is None:
        return fallback
    if not isinstance(html, dict) or any(
        not isinstance(language, str) or not isinstance(url, str) for language, url in html.items()
    ):
        raise TEDMappingError("TED field 'links.html' must map languages to URLs")
    if not html:
        return fallback
    normalized: dict[str, str] = {}
    for language, url in html.items():
        if isinstance(language, str) and isinstance(url, str) and url.strip():
            normalized[language.casefold()] = url.strip()
    if not normalized:
        return fallback
    language = "eng" if "eng" in normalized else sorted(normalized)[0]
    return normalized[language]


class TEDNoticeMapper:
    """Pure deterministic mapping from a TED field projection to `Tender`."""

    def map_notice(self, notice: dict[str, Any]) -> Tender:
        """Map one raw search notice without network access or source-specific leakage."""
        publication_number = notice.get("publication-number")
        if not isinstance(publication_number, str) or not publication_number.strip():
            raise TEDMappingError("TED notice is missing a valid 'publication-number'")
        publication_number = publication_number.strip()

        title_values = _multilingual_texts(notice, "notice-title")
        buyer_values = _multilingual_texts(notice, "buyer-name")
        description_values = _unique_strings(
            [
                *_multilingual_texts(notice, "description-proc"),
                *_multilingual_texts(notice, "description-lot"),
            ]
        )
        cpv_codes = _unique_strings(
            [
                *_string_list(notice, "classification-cpv"),
                *_string_list(notice, "main-classification-proc"),
            ]
        )
        nuts_codes = _string_list(notice, "place-of-performance")
        deadlines = [
            *_date_values(notice, "deadline-receipt-tender-date-lot"),
            *_date_values(notice, "deadline-date-lot"),
        ]

        currency = notice.get("estimated-value-cur-proc")
        if currency is not None and not isinstance(currency, str):
            raise TEDMappingError("TED field 'estimated-value-cur-proc' must be a string")

        try:
            return Tender(
                id=publication_number,
                title=title_values[0] if title_values else f"TED notice {publication_number}",
                buyer=buyer_values[0] if buyer_values else "Buyer not specified",
                description=(
                    "\n".join(description_values)
                    if description_values
                    else "No description supplied by TED."
                ),
                products=[],
                destination=", ".join(nuts_codes) if nuts_codes else None,
                deadline=min(deadlines) if deadlines else None,
                currency=currency,
                required_certifications=[],
                source="TED",
                source_id=publication_number,
                source_url=_notice_url(notice, publication_number),
                cpv_codes=cpv_codes,
                nuts_codes=nuts_codes,
                estimated_value=_optional_decimal(notice, "estimated-value-proc"),
                publication_date=_optional_date(notice, "publication-date"),
            )
        except PydanticValidationError as error:
            raise TEDMappingError(
                f"TED notice '{publication_number}' cannot be represented as a Tender: {error}"
            ) from error
