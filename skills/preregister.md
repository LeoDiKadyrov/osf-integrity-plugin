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
> "Would you like to upload this to your OSF project now? You'll need your OSF project node ID and your OSF Personal Access Token set in `.env` as `OSF_TOKEN`. You can skip this and upload manually later at osf.io."

If the user wants to upload:
1. Tell them to add `OSF_TOKEN=their_token` to their `.env` file if not done already
2. Ask for their OSF project node ID (e.g. `abc12` from the URL https://osf.io/abc12/)
3. Call:

```
osf_upload(
  project_id=<project node ID>,
  file_path=<path returned in step 8>
)
```

Tell the user the URL where the preregistration is now publicly accessible.
