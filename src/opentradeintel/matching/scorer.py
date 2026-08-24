"""Explainable deterministic baseline scoring."""

from decimal import ROUND_HALF_UP, Decimal

from opentradeintel.models import MatchResult, Product, ScoreBreakdown, Tender
from opentradeintel.normalization import market_tokens, normalize_category, normalize_text


def _rounded_points(maximum: int, matched: int, possible: int) -> int:
    if possible == 0:
        return 0
    value = Decimal(maximum) * Decimal(matched) / Decimal(possible)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _tender_tokens(tender: Tender) -> set[str]:
    combined = " ".join([tender.title, tender.description, *tender.products])
    return set(normalize_text(combined).split())


def cpv_overlap(tender: Tender, product: Product) -> tuple[str, ...]:
    """Return exact CPV codes shared by both records in stable order."""
    return tuple(sorted(set(tender.cpv_codes) & set(product.cpv_codes)))


def _product_similarity(tender: Tender, product: Product) -> tuple[int, str]:
    tender_tokens = _tender_tokens(tender)
    name_tokens = set(normalize_text(product.name).split())
    keyword_tokens = {
        token for keyword in product.keywords for token in normalize_text(keyword).split()
    }
    name_points = _rounded_points(24, len(name_tokens & tender_tokens), len(name_tokens))
    keyword_points = _rounded_points(16, len(keyword_tokens & tender_tokens), len(keyword_tokens))
    points = name_points + keyword_points
    return points, (
        f"Product similarity: {points}/40 (name {name_points}/24, keywords {keyword_points}/16)"
    )


def _category_score(tender: Tender, product: Product) -> tuple[int, str, str | None]:
    category = normalize_category(product.category)
    category_tokens = set(category.split())
    if category_tokens and category_tokens <= _tender_tokens(tender):
        return 15, f"Category: 15/15 ({category})", None
    return 0, "Category: 0/15", f"Category not found in tender requirements: {product.category}"


def _certification_score(tender: Tender, product: Product) -> tuple[int, str, str | None]:
    if not tender.required_certifications:
        return 20, "Certifications: 20/20 (No certifications required)", None

    available = {normalize_text(item) for item in product.certifications}
    required = {normalize_text(item): item for item in tender.required_certifications}
    covered = available & required.keys()
    points = _rounded_points(20, len(covered), len(required))
    missing = [original for normalized, original in required.items() if normalized not in covered]
    warning = f"Missing required certifications: {', '.join(missing)}" if missing else None
    return points, f"Certifications: {points}/20 ({len(covered)}/{len(required)} covered)", warning


def _market_score(tender: Tender, product: Product) -> tuple[int, str, str | None]:
    if tender.destination is None:
        return 15, "Market compatibility: 15/15 (no destination restriction)", None

    destination = market_tokens(tender.destination)
    available = market_tokens(product.available_markets)
    if destination & available:
        return 15, "Market compatibility: 15/15", None
    return (
        0,
        "Market compatibility: 0/15",
        f"Destination not listed in available markets: {tender.destination}",
    )


def _moq_score(tender: Tender, product: Product) -> tuple[int, str, str | None]:
    if tender.quantity is None or product.min_order_quantity is None:
        return 5, "MOQ compatibility: 5/10 (insufficient data)", "Verify final commercial MOQ"
    if tender.quantity >= product.min_order_quantity:
        return 10, "MOQ compatibility: 10/10", None
    return (
        0,
        "MOQ compatibility: 0/10",
        f"Tender quantity {tender.quantity} is below MOQ {product.min_order_quantity}",
    )


def score_product(tender: Tender, product: Product) -> MatchResult:
    """Score one product using five fixed, local, explainable components."""
    similarity, similarity_reason = _product_similarity(tender, product)
    category, category_reason, category_warning = _category_score(tender, product)
    certifications, certification_reason, certification_warning = _certification_score(
        tender, product
    )
    market, market_reason, market_warning = _market_score(tender, product)
    moq, moq_reason, moq_warning = _moq_score(tender, product)

    breakdown = ScoreBreakdown(
        product_similarity=similarity,
        category=category,
        certifications=certifications,
        market=market,
        moq=moq,
    )
    warnings = [
        warning
        for warning in (category_warning, certification_warning, market_warning, moq_warning)
        if warning is not None
    ]
    reasons = [
        similarity_reason,
        category_reason,
        certification_reason,
        market_reason,
        moq_reason,
    ]
    overlapping_cpv = cpv_overlap(tender, product)
    if overlapping_cpv:
        reasons.append(
            f"CPV overlap: {', '.join(overlapping_cpv)} (tie-break signal; no score impact)"
        )
    return MatchResult(
        score=breakdown.total,
        product=product,
        reasons=reasons,
        warnings=warnings,
        breakdown=breakdown,
    )
