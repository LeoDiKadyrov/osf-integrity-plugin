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


def format_evidence_table(papers: list[dict]) -> str:
    """Format a list of papers as a Markdown table.

    Args:
        papers: Output from search_evidence().

    Returns:
        Markdown-formatted table string, or 'No papers found.' if empty.
    """
    if not papers:
        return "No papers found."

    header = "| Title | Authors | Year | N | Effect Size | DOI |"
    separator = "|-------|---------|------|---|-------------|-----|"

    rows = []
    for p in papers:
        raw_title = p.get("title", "")
        title = (raw_title[:60] + "…") if len(raw_title) > 60 else raw_title
        row = (
            f"| {title} "
            f"| {p.get('authors', '')} "
            f"| {p.get('year') or ''} "
            f"| {p.get('n') or ''} "
            f"| {p.get('effect_size') or ''} "
            f"| {p.get('doi') or ''} |"
        )
        rows.append(row)

    return "\n".join([header, separator] + rows)
