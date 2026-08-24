"""Optional smoke test for the public TED production API."""

import pytest

from opentradeintel.collectors import TEDSearchClient, TEDSearchQuery


@pytest.mark.live
def test_official_ted_search_returns_the_documented_notice_envelope() -> None:
    notices = TEDSearchClient(timeout=20).search(
        TEDSearchQuery(cpv="79420000", scope="ALL", limit=1)
    )

    assert len(notices) == 1
    assert isinstance(notices[0]["publication-number"], str)
