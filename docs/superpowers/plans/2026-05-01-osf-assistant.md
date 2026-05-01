# OSF Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin + MCP server that guides researchers through OSF-compliant preregistration and evidence search using structured dialogue.

**Architecture:** Monorepo with a Python package (`osf_assistant`) serving as a FastMCP server, and Markdown skill files that drive structured dialogue in Claude Code. Skills call MCP tools for real API work; the same MCP server is usable from any MCP-compatible client (Cursor, etc.).

**Tech Stack:** Python 3.11+, `fastmcp>=2.0.0`, `httpx`, `python-dotenv`, `pytest`, `respx` (HTTP mocking)

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package config, dependencies |
| `.env.example` | Config template for OSF token, output dir |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest — registers skills + MCP server |
| `.mcp.json` | MCP server launch config |
| `osf_assistant/__init__.py` | Package marker |
| `osf_assistant/server.py` | FastMCP server — registers all tools |
| `osf_assistant/tools/__init__.py` | Package marker |
| `osf_assistant/tools/preregistration.py` | `generate_preregistration` + `osf_upload` |
| `osf_assistant/tools/evidence.py` | `search_evidence` + `format_evidence_table` |
| `osf_assistant/templates/osf_standard.json` | OSF Standard Pre-Registration field schema |
| `osf_assistant/templates/aspredicted.json` | AsPredicted field schema |
| `skills/preregister.md` | Skill: 9-step preregistration dialogue |
| `skills/find-evidence.md` | Skill: evidence search dialogue |
| `tests/test_preregistration.py` | Tests for preregistration tools |
| `tests/test_evidence.py` | Tests for evidence tools |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `osf_assistant/__init__.py`
- Create: `osf_assistant/tools/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p osf_assistant/tools osf_assistant/templates skills tests .claude-plugin
touch osf_assistant/__init__.py osf_assistant/tools/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "osf-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "respx>=0.21.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["osf_assistant"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `.env.example`**

```
OSF_TOKEN=           # your OSF Personal Access Token (optional — only needed for upload)
OSF_PROJECT_ID=      # your OSF project node ID, e.g. abc12 (optional)
OUTPUT_DIR=./preregistrations
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -e ".[dev]"
```

Expected: no errors, `fastmcp`, `httpx`, `respx`, `pytest` available.

- [ ] **Step 5: Verify install**

```bash
python -c "import fastmcp, httpx, respx; print('OK')"
```

Expected output: `OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example osf_assistant/ tests/
git commit -m "chore: project scaffold"
```

---

## Task 2: OSF Templates

**Files:**
- Create: `osf_assistant/templates/osf_standard.json`
- Create: `osf_assistant/templates/aspredicted.json`

These JSON files define the field schema for each template type. They serve as the source of truth for what fields are required and their default values.

- [ ] **Step 1: Write `osf_assistant/templates/osf_standard.json`**

```json
{
  "template_type": "osf_standard",
  "title": "",
  "context": "",
  "h0": "",
  "h1": "",
  "design": "",
  "iv": "",
  "dv": "",
  "covariates": "",
  "measurement": "",
  "n": "",
  "inclusion_criteria": "",
  "exclusion_criteria": "",
  "test": "",
  "alpha": "0.05",
  "corrections": ""
}
```

- [ ] **Step 2: Write `osf_assistant/templates/aspredicted.json`**

```json
{
  "template_type": "aspredicted",
  "title": "",
  "context": "",
  "h0": "",
  "h1": "",
  "design": "",
  "iv": "",
  "dv": "",
  "n": "",
  "test": "",
  "alpha": "0.05"
}
```

- [ ] **Step 3: Commit**

```bash
git add osf_assistant/templates/
git commit -m "feat: add OSF preregistration templates"
```

---

## Task 3: `generate_preregistration` Tool

**Files:**
- Create: `osf_assistant/tools/preregistration.py`
- Create: `tests/test_preregistration.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_preregistration.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import patch
from osf_assistant.tools.preregistration import generate_preregistration


@pytest.fixture
def sample_data():
    return {
        "title": "Effect of sleep on memory consolidation",
        "context": "Investigating whether sleep duration affects recall accuracy.",
        "h0": "Sleep duration has no effect on recall accuracy.",
        "h1": "Longer sleep improves recall accuracy.",
        "design": "Between-subjects, two groups: 6h vs 8h sleep",
        "iv": "Sleep duration (6h vs 8h)",
        "dv": "Recall accuracy (% correct on 50-item word list)",
        "covariates": "Age, baseline recall score",
        "measurement": "Word recall task, administered 12h after sleep",
        "n": "64 (32 per group)",
        "inclusion_criteria": "Adults 18–35, no sleep disorders",
        "exclusion_criteria": "Shift workers, medication affecting sleep",
        "test": "Independent samples t-test",
        "alpha": "0.05",
        "corrections": "None",
    }


def test_generate_creates_file(sample_data, tmp_path):
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        path = generate_preregistration(sample_data, "osf_standard")
        assert Path(path).exists()


def test_generate_file_contains_title(sample_data, tmp_path):
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        path = generate_preregistration(sample_data, "osf_standard")
        content = Path(path).read_text(encoding="utf-8")
        assert "Effect of sleep on memory consolidation" in content


def test_generate_file_contains_all_sections(sample_data, tmp_path):
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        path = generate_preregistration(sample_data, "osf_standard")
        content = Path(path).read_text(encoding="utf-8")
        for section in ["Context", "Hypotheses", "Design", "Variables", "Sample", "Analysis Plan"]:
            assert f"## {section}" in content, f"Missing section: {section}"


def test_generate_aspredicted_omits_osf_fields(tmp_path):
    data = {
        "title": "Test",
        "context": "Testing",
        "h0": "No effect",
        "h1": "Some effect",
        "design": "Between-subjects",
        "iv": "Condition",
        "dv": "Score",
        "n": "40",
        "test": "t-test",
        "alpha": "0.05",
    }
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        path = generate_preregistration(data, "aspredicted")
        content = Path(path).read_text(encoding="utf-8")
        assert "AsPredicted" in content or "aspredicted" in content
        assert "Inclusion criteria" not in content
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_preregistration.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (function doesn't exist yet).

- [ ] **Step 3: Implement `generate_preregistration`**

Create `osf_assistant/tools/preregistration.py`:

```python
import json
import os
from datetime import date
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_preregistration(data: dict, template: str = "osf_standard") -> str:
    """Generate an OSF-compatible preregistration Markdown file from collected data.

    Args:
        data: Dict with fields matching the chosen template schema.
        template: 'osf_standard' or 'aspredicted'.

    Returns:
        Absolute path to the saved Markdown file.
    """
    template_path = TEMPLATES_DIR / f"{template}.json"
    with open(template_path, encoding="utf-8") as f:
        schema = json.load(f)

    merged = {**schema, **data, "generated_date": date.today().isoformat()}
    content = _render_markdown(merged)

    output_dir = Path(os.getenv("OUTPUT_DIR", "./preregistrations"))
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"preregistration_{merged['generated_date']}.md"
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return str(output_path.resolve())


def _render_markdown(data: dict) -> str:
    template_type = data.get("template_type", "osf_standard")
    lines = [
        f"# Pre-Registration: {data.get('title', 'Untitled')}",
        f"**Date:** {data.get('generated_date', '')}",
        f"**Template:** {template_type}",
        "",
        "## Context",
        data.get("context", ""),
        "",
        "## Hypotheses",
        f"**H0:** {data.get('h0', '')}",
        f"**H1:** {data.get('h1', '')}",
        "",
        "## Design",
        data.get("design", ""),
        "",
        "## Variables",
        f"**Independent variable(s):** {data.get('iv', '')}",
        f"**Dependent variable(s):** {data.get('dv', '')}",
    ]

    if template_type == "osf_standard":
        lines += [
            f"**Covariates:** {data.get('covariates', 'None')}",
            f"**Measurement:** {data.get('measurement', '')}",
        ]

    lines += [
        "",
        "## Sample",
        f"**Planned N:** {data.get('n', '')}",
    ]

    if template_type == "osf_standard":
        lines += [
            f"**Inclusion criteria:** {data.get('inclusion_criteria', '')}",
            f"**Exclusion criteria:** {data.get('exclusion_criteria', '')}",
        ]

    lines += [
        "",
        "## Analysis Plan",
        f"**Statistical test:** {data.get('test', '')}",
        f"**Alpha threshold (α):** {data.get('alpha', '0.05')}",
    ]

    if template_type == "osf_standard":
        lines.append(
            f"**Corrections for multiple comparisons:** {data.get('corrections', 'None')}"
        )

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_preregistration.py -v
```

Expected: all 4 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/preregistration.py tests/test_preregistration.py
git commit -m "feat: add generate_preregistration tool"
```

---

## Task 4: `osf_upload` Tool

**Files:**
- Modify: `osf_assistant/tools/preregistration.py` (add `osf_upload`)
- Modify: `tests/test_preregistration.py` (add upload tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_preregistration.py`:

```python
import httpx
import respx
from osf_assistant.tools.preregistration import osf_upload


def test_osf_upload_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        osf_upload("fake_token", "proj123", "/nonexistent/file.md")


def test_osf_upload_sends_correct_request(tmp_path):
    test_file = tmp_path / "preregistration_2026-05-01.md"
    test_file.write_text("# Test preregistration", encoding="utf-8")

    mock_body = {
        "data": {
            "links": {
                "html": "https://osf.io/proj123/files/preregistration_2026-05-01.md"
            }
        }
    }

    with respx.mock:
        respx.put(
            "https://files.osf.io/v1/resources/proj123/providers/osfstorage/"
        ).mock(return_value=httpx.Response(200, json=mock_body))

        url = osf_upload("fake_token", "proj123", str(test_file))

    assert url == "https://osf.io/proj123/files/preregistration_2026-05-01.md"


def test_osf_upload_raises_on_api_error(tmp_path):
    test_file = tmp_path / "preregistration.md"
    test_file.write_text("# Test", encoding="utf-8")

    with respx.mock:
        respx.put(
            "https://files.osf.io/v1/resources/bad_proj/providers/osfstorage/"
        ).mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

        with pytest.raises(httpx.HTTPStatusError):
            osf_upload("bad_token", "bad_proj", str(test_file))
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_preregistration.py::test_osf_upload_raises_if_file_missing tests/test_preregistration.py::test_osf_upload_sends_correct_request tests/test_preregistration.py::test_osf_upload_raises_on_api_error -v
```

Expected: `ImportError` (function not defined yet).

- [ ] **Step 3: Add `osf_upload` to `preregistration.py`**

Append to the bottom of `osf_assistant/tools/preregistration.py`:

```python
import httpx


def osf_upload(token: str, project_id: str, file_path: str) -> str:
    """Upload a preregistration file to an OSF project.

    Args:
        token: OSF Personal Access Token.
        project_id: OSF project node ID (e.g. 'abc12').
        file_path: Local path to the file to upload.

    Returns:
        Public HTML URL of the uploaded file on OSF.

    Raises:
        FileNotFoundError: If file_path does not exist.
        httpx.HTTPStatusError: If the OSF API returns an error response.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    upload_url = (
        f"https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/"
    )

    with httpx.Client() as client:
        response = client.put(
            upload_url,
            params={"name": path.name},
            headers={"Authorization": f"Bearer {token}"},
            content=path.read_bytes(),
        )
        response.raise_for_status()

    return response.json()["data"]["links"]["html"]
```

Also add `import httpx` at the top of the file (after existing imports).

- [ ] **Step 4: Run all preregistration tests**

```bash
pytest tests/test_preregistration.py -v
```

Expected: all 7 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/preregistration.py tests/test_preregistration.py
git commit -m "feat: add osf_upload tool"
```

---

## Task 5: `search_evidence` Tool

**Files:**
- Create: `osf_assistant/tools/evidence.py`
- Create: `tests/test_evidence.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_evidence.py`:

```python
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_evidence.py -v
```

Expected: `ImportError` (module doesn't exist yet).

- [ ] **Step 3: Implement `search_evidence`**

Create `osf_assistant/tools/evidence.py`:

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_evidence.py -v
```

Expected: all 5 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/evidence.py tests/test_evidence.py
git commit -m "feat: add search_evidence tool"
```

---

## Task 6: `format_evidence_table` Tool

**Files:**
- Modify: `osf_assistant/tools/evidence.py` (add `format_evidence_table`)
- Modify: `tests/test_evidence.py` (add formatting tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_evidence.py`:

```python
from osf_assistant.tools.evidence import format_evidence_table


def test_format_evidence_table_returns_markdown_table():
    papers = [
        {
            "title": "Sleep and Memory: A Review",
            "authors": "Smith, J., Doe, A.",
            "year": 2022,
            "n": None,
            "effect_size": None,
            "design": None,
            "doi": "10.1234/sleep.2022",
        }
    ]

    table = format_evidence_table(papers)

    assert "| Title |" in table
    assert "|----" in table
    assert "Sleep and Memory" in table
    assert "10.1234/sleep.2022" in table
    assert "2022" in table


def test_format_evidence_table_truncates_long_titles():
    papers = [
        {
            "title": "A" * 70,
            "authors": "Smith, J.",
            "year": 2022,
            "n": None,
            "effect_size": None,
            "design": None,
            "doi": None,
        }
    ]

    table = format_evidence_table(papers)
    # Title cell should be truncated to ≤ 63 chars (60 + ellipsis)
    lines = table.split("\n")
    data_row = lines[2]  # header, separator, first data row
    title_cell = data_row.split("|")[1]
    assert len(title_cell.strip()) <= 63


def test_format_evidence_table_empty_returns_message():
    assert format_evidence_table([]) == "No papers found."
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_evidence.py::test_format_evidence_table_returns_markdown_table tests/test_evidence.py::test_format_evidence_table_truncates_long_titles tests/test_evidence.py::test_format_evidence_table_empty_returns_message -v
```

Expected: `ImportError` (function not defined).

- [ ] **Step 3: Add `format_evidence_table` to `evidence.py`**

Append to the bottom of `osf_assistant/tools/evidence.py`:

```python
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
```

- [ ] **Step 4: Run all evidence tests**

```bash
pytest tests/test_evidence.py -v
```

Expected: all 8 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/evidence.py tests/test_evidence.py
git commit -m "feat: add format_evidence_table tool"
```

---

## Task 7: MCP Server + Plugin Manifest

**Files:**
- Create: `osf_assistant/server.py`
- Create: `.mcp.json`
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Write `osf_assistant/server.py`**

```python
from dotenv import load_dotenv
from fastmcp import FastMCP
from osf_assistant.tools.preregistration import generate_preregistration, osf_upload
from osf_assistant.tools.evidence import search_evidence, format_evidence_table

load_dotenv()

mcp = FastMCP(name="OSF Assistant")

mcp.tool()(generate_preregistration)
mcp.tool()(osf_upload)
mcp.tool()(search_evidence)
mcp.tool()(format_evidence_table)

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Verify server starts without errors**

```bash
python -m osf_assistant.server &
sleep 2
kill %1
```

Expected: process starts and exits cleanly (no import errors or tracebacks).

- [ ] **Step 3: Write `.mcp.json`**

```json
{
  "mcpServers": {
    "osf-assistant": {
      "command": "python",
      "args": ["-m", "osf_assistant.server"],
      "env": {}
    }
  }
}
```

- [ ] **Step 4: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "osf-assistant",
  "version": "0.1.0",
  "description": "Open Science Framework assistant — preregistration and evidence search for researchers.",
  "skills": "../skills/",
  "mcpServers": "../.mcp.json"
}
```

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add osf_assistant/server.py .mcp.json .claude-plugin/
git commit -m "feat: add MCP server and plugin manifest"
```

---

## Task 8: Skills

**Files:**
- Create: `skills/preregister.md`
- Create: `skills/find-evidence.md`

- [ ] **Step 1: Write `skills/preregister.md`**

```markdown
---
name: preregister
description: Guide a researcher through creating an OSF-compatible preregistration document, one question at a time. Calls MCP tools to generate and optionally upload the file.
---

# Pre-Registration Workflow

Guide the user through preregistration step by step. Ask **one question per message**. Do NOT skip steps — if the user doesn't know an answer, explain why it matters and help them formulate one before moving on.

After collecting all information, call the MCP tool `generate_preregistration`.

---

## Step 1 — Title and Context

Ask:
> "What is your research question? Give it a working title and briefly describe what you're investigating and why it matters."

---

## Step 2 — Hypotheses

Ask:
> "Formulate your hypotheses explicitly:
> - **H0** (null hypothesis): what would be true if your manipulation has no effect?
> - **H1** (alternative hypothesis): what specific change or difference do you predict?"

If the user writes vague hypotheses (e.g. "I think X will affect Y"), prompt them to specify the direction of the expected effect before continuing.

---

## Step 3 — Study Design

Ask:
> "What is your study design?
> - Between-subjects (different participants per condition) or within-subjects (same participants in all conditions)?
> - Experimental, quasi-experimental, or observational?
> - Cross-sectional or longitudinal?"

---

## Step 4 — Variables

Ask:
> "Describe your variables:
> - **IV** (independent variable): what you manipulate or group by
> - **DV** (dependent variable): what you measure as the outcome
> - **Covariates**: any control variables, or write 'None'
> - **Measurement**: how each variable is measured (scale, instrument, unit)"

---

## Step 5 — Sample

Ask:
> "Describe your planned sample:
> - How many participants (**N**) do you plan to collect?
> - **Inclusion criteria**: who qualifies?
> - **Exclusion criteria**: who is excluded and why?"

If N < 20 for a between-subjects design, note:
> "A sample this small risks very low statistical power. Have you done a power analysis? I can help you calculate the required N."

---

## Step 6 — Analysis Plan

Ask:
> "Describe your analysis plan:
> - Which statistical test will you use?
> - What is your significance threshold (α)? (Typically 0.05)
> - Will you apply corrections for multiple comparisons? If so, which method? (e.g. Bonferroni, FDR)"

If the user is unsure which test to use, ask: "How many groups are you comparing, and do you expect the data to be normally distributed?" Then suggest an appropriate test.

---

## Step 7 — Template

Ask:
> "Which preregistration template would you like to use?
> - **OSF Standard** — more detailed, recommended for journal submission
> - **AsPredicted** — shorter format, good for quick preregistrations"

---

## Step 8 — Generate File

Call the MCP tool with all collected data:

```
generate_preregistration(
  data={
    "title": <from step 1>,
    "context": <from step 1>,
    "h0": <from step 2>,
    "h1": <from step 2>,
    "design": <from step 3>,
    "iv": <from step 4>,
    "dv": <from step 4>,
    "covariates": <from step 4>,
    "measurement": <from step 4>,
    "n": <from step 5>,
    "inclusion_criteria": <from step 5>,
    "exclusion_criteria": <from step 5>,
    "test": <from step 6>,
    "alpha": <from step 6>,
    "corrections": <from step 6>
  },
  template=<"osf_standard" or "aspredicted">
)
```

Tell the user:
> "Your preregistration has been saved to `[returned path]`. Review it and let me know if anything needs changing."

---

## Step 9 — OSF Upload (Optional)

Ask:
> "Would you like to upload this to your OSF project now? If yes, I'll need your OSF Personal Access Token and project node ID. You can skip this and upload manually later at osf.io."

If the user provides both, call:

```
osf_upload(
  token=<OSF Personal Access Token>,
  project_id=<project node ID>,
  file_path=<path returned in step 8>
)
```

Tell the user the URL where the preregistration is now publicly accessible.
```

- [ ] **Step 2: Write `skills/find-evidence.md`**

```markdown
---
name: find-evidence
description: Search peer-reviewed literature on Semantic Scholar for evidence relevant to a research hypothesis. Returns a structured Markdown table. Does not invent citations.
---

# Evidence Finder Workflow

Help the user find peer-reviewed evidence for their hypothesis. All results come from the Semantic Scholar API — do not invent or guess citations.

---

## Step 1 — Understand the Hypothesis

Ask:
> "What is the hypothesis or research question you want to find evidence for? Be as specific as possible — include the variables and the expected relationship between them."

---

## Step 2 — Formulate Search Queries

Based on the hypothesis, generate 2–3 query variants that cover:
- Core concept keywords
- Alternative terminology (e.g., "memory consolidation" vs "memory retention")
- Related constructs if the primary terms are narrow

Tell the user:
> "I'll search with these queries:
> 1. [query 1]
> 2. [query 2]
> 3. [query 3]
>
> Does this look right, or would you like to adjust any of them?"

Wait for confirmation before proceeding.

---

## Step 3 — Search

Call:

```
search_evidence(queries=[<query1>, <query2>, <query3>], limit=10)
```

---

## Step 4 — Format and Present

Call:

```
format_evidence_table(papers=<results from step 3>)
```

Present the table to the user. Add this note:
> "The N and Effect Size columns are empty when this data isn't in the paper's public metadata — this is expected, not an error. You'll need to read the papers to extract those values."

---

## Step 5 — Next Steps

Ask:
> "What would you like to do next?
> - Start a preregistration using this evidence? (use /preregister)
> - Search again with different queries?
> - I'm done for now"
```

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: add preregister and find-evidence skills"
```

---

## Task 9: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# OSF Assistant

A Claude Code plugin and MCP server that guides researchers through Open Science practices —
preregistration, evidence search, and methodology checks.

## Features (v1)

- **/preregister** — Step-by-step preregistration dialogue. Generates an OSF-compatible Markdown file. Optionally uploads to OSF via API.
- **/find-evidence** — Searches Semantic Scholar for peer-reviewed papers relevant to your hypothesis. Returns a structured table with title, authors, year, and DOI.

## Installation

```bash
git clone https://github.com/<your-username>/osf-assistant
cd osf-assistant
pip install -e .
```

Copy `.env.example` to `.env` and fill in your values (OSF token is optional):

```bash
cp .env.example .env
```

## Usage in Claude Code

Install the plugin, then use:

- `/preregister` — start a new preregistration
- `/find-evidence` — search for papers

## Usage via MCP (Cursor, etc.)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "osf-assistant": {
      "command": "python",
      "args": ["-m", "osf_assistant.server"]
    }
  }
}
```

Available tools: `generate_preregistration`, `osf_upload`, `search_evidence`, `format_evidence_table`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Self-Review

**Spec coverage:**
- ✅ Claude Code plugin with own skills: `skills/`, `.claude-plugin/plugin.json`
- ✅ MCP server: `osf_assistant/server.py`, `.mcp.json`
- ✅ `preregister` skill (9-step dialogue): Task 8
- ✅ `find-evidence` skill: Task 8
- ✅ `generate_preregistration` tool: Task 3
- ✅ `osf_upload` tool (optional, token-gated): Task 4
- ✅ `search_evidence` tool (Semantic Scholar, no hallucination): Task 5
- ✅ `format_evidence_table` tool: Task 6
- ✅ OSF templates (osf_standard, aspredicted): Task 2
- ✅ `.env` config (OSF_TOKEN optional, OUTPUT_DIR): Task 1
- ✅ Works without OSF token: `osf_upload` only called if user provides token

**Placeholder scan:** No TBDs, no "implement later", all code blocks complete.

**Type consistency:** `search_evidence` returns `list[dict]`, `format_evidence_table` accepts `list[dict]` — consistent. `generate_preregistration` returns `str` (path), `osf_upload` accepts `str` (path) — consistent.
