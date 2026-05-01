# OSF Assistant

A Claude Code plugin and MCP server that guides researchers through Open Science practices —
preregistration, evidence search, and methodology checks.

## Features (v1)

- **/preregister** — Step-by-step preregistration dialogue. Generates an OSF-compatible Markdown file. Optionally uploads to OSF via API.
- **/find-evidence** — Searches Semantic Scholar for peer-reviewed papers relevant to your hypothesis. Returns a structured table with title, authors, year, and DOI.

## Installation

```bash
git clone https://github.com/LeoDiKadyrov/osf-integrity-plugin
cd osf-integrity-plugin
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
