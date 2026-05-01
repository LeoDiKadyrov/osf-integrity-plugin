import httpx

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,authors,year,externalIds"


def search_evidence(queries: list[str], limit: int = 10) -> list[dict]:
    """Search Semantic Scholar for papers relevant to a research hypothesis.

    Args:
        queries: List of search query strings (2-3 variants recommended).
        limit: Max results per query before deduplication.

    Returns:
        Deduplicated list of dicts with keys:
        title, authors, year, n, effect_size, design, doi.
        n, effect_size, design are always None — not hallucinated.

    Raises:
        httpx.HTTPStatusError: If Semantic Scholar API returns an error.
    """
    seen: set[str] = set()
    papers: list[dict] = []

    with httpx.Client() as client:
        for query in queries:
            response = client.get(
                SEMANTIC_SCHOLAR_URL,
                params={"query": query, "limit": limit, "fields": _FIELDS},
                timeout=10.0,
            )
            response.raise_for_status()

            for item in response.json().get("data", []):
                doi = item.get("externalIds", {}).get("DOI")
                dedup_key = doi or item.get("paperId", "")
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                authors = item.get("authors", [])
                papers.append({
                    "title": item.get("title", ""),
                    "authors": ", ".join(a["name"] for a in authors),
                    "year": item.get("year"),
                    "n": None,
                    "effect_size": None,
                    "design": None,
                    "doi": doi,
                })

    return papers
