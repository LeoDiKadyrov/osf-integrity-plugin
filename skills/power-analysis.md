---
name: power-analysis
description: Calculate the required sample size (N) for a statistical test given effect size, alpha, and desired power. Supports t-test, ANOVA, and Pearson correlation.
---

# Power Analysis Workflow

Help the researcher calculate how many participants they need. If they already know their parameters, skip straight to the calculation.

---

## Step 1 — Check if Parameters Are Known

Ask:
> "Do you already know your test type, expected effect size, α, and desired power? If yes, give them to me and I'll calculate immediately. If not, I'll walk you through choosing them."

If all 4 parameters provided → skip to Step 3.

---

## Step 2 — Guide Parameter Selection

Explain each parameter, one at a time:

**Test type** — ask which statistical test they plan to use:
- `ttest` — comparing two independent groups (e.g. control vs treatment)
- `anova` — comparing two groups with ANOVA (same result as ttest for 2 groups)
- `correlation` — testing whether two variables are related

**Effect size** — ask what size effect they expect:
- Cohen's d for ttest/anova: small=0.2, medium=0.5, large=0.8
- Pearson r for correlation: small=0.1, medium=0.3, large=0.5
- If unsure: recommend d=0.5 or r=0.3 (medium, conservative)

**Alpha (α)** — significance threshold. Default: 0.05. Use 0.01 for stricter studies.

**Power (1-β)** — probability of detecting a real effect. Default: 0.80 (80%). Use 0.90 for critical studies.

---

## Step 3 — Calculate

Call:
```
calculate_power(
  test_type=<"ttest" | "anova" | "correlation">,
  effect_size=<float>,
  alpha=<float, default 0.05>,
  power=<float, default 0.80>
)
```

---

## Step 4 — Present Result

Show the returned `interpretation` field prominently.

Then add context:
> "If this N is unrealistic for your resources, consider:
> - Reducing desired power to 0.70 (N drops ~20%)
> - Targeting a larger effect size if theoretically justified
> - Switching to a within-subjects design (requires fewer participants)
> - Running a pilot study first to estimate the real effect size"

Ask:
> "Do you want to add this N to your preregistration? Run /preregister and use this number in Step 5."
