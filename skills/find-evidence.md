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
