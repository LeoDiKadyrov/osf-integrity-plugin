import pytest
import httpx
import respx
from osf_assistant.tools.evidence import search_evidence

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

MOCK_RESPONSE = {
    "data": [
        {
            "paperId": "abc123",
            "title": "Sleep and Memory: A Review",
            "authors": [{"name": "Smith, J."}, {"name": "Doe, A."}, {"name": "Lee, K."}],
            "year": 2022,
            "externalIds": {"DOI": "10.1234/sleep.2022"},
        },
        {
            "paperId": "def456",
            "title": "Memory Consolidation During Sleep",
            "authors": [{"name": "Jones, B."}],
            "year": 2020,
            "externalIds": {},
        },
    ]
}


def test_search_evidence_returns_structured_list():
    with respx.mock:
        respx.get(SEMANTIC_SCHOLAR_URL).mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        results = search_evidence(["sleep memory consolidation"], limit=10)

    assert len(results) == 2
    assert results[0]["title"] == "Sleep and Memory: A Review"
    assert results[0]["authors"] == "Smith, J., Doe, A., Lee, K."
    assert results[0]["doi"] == "10.1234/sleep.2022"
    assert results[0]["year"] == 2022


def test_search_evidence_effect_size_is_none():
    """effect_size must never be hallucinated — always None from Semantic Scholar."""
    with respx.mock:
        respx.get(SEMANTIC_SCHOLAR_URL).mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        results = search_evidence(["sleep memory"], limit=5)

    for paper in results:
        assert paper["effect_size"] is None
        assert paper["n"] is None


def test_search_evidence_deduplicates_by_doi():
    single_paper = {
        "data": [
            {
                "paperId": "abc123",
                "title": "Sleep and Memory: A Review",
                "authors": [{"name": "Smith, J."}],
                "year": 2022,
                "externalIds": {"DOI": "10.1234/sleep.2022"},
            }
        ]
    }

    with respx.mock:
        respx.get(SEMANTIC_SCHOLAR_URL).mock(
            return_value=httpx.Response(200, json=single_paper)
        )

        # Two queries, same paper with same DOI returned for both
        results = search_evidence(["query one", "query two"], limit=5)

    assert len(results) == 1


def test_search_evidence_deduplicates_by_paper_id_when_no_doi():
    no_doi_response = {
        "data": [
            {
                "paperId": "def456",
                "title": "Memory Consolidation During Sleep",
                "authors": [{"name": "Jones, B."}],
                "year": 2020,
                "externalIds": {},
            }
        ]
    }

    with respx.mock:
        respx.get(SEMANTIC_SCHOLAR_URL).mock(
            return_value=httpx.Response(200, json=no_doi_response)
        )

        results = search_evidence(["query one", "query two"], limit=5)

    assert len(results) == 1


def test_search_evidence_raises_on_api_error():
    with respx.mock:
        respx.get(SEMANTIC_SCHOLAR_URL).mock(
            return_value=httpx.Response(429, json={"message": "Rate limit exceeded"})
        )

        with pytest.raises(httpx.HTTPStatusError):
            search_evidence(["sleep"], limit=5)
