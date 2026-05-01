# OSF Assistant v2 — Design Spec
**Date:** 2026-05-01  
**Status:** Approved

---

## Overview

v2 adds two new modules to OSF Assistant: a **Bias & Methodology Checker** (`check-bias`) and a **Power Analysis Calculator** (`power-analysis`). Both follow the v1 pattern: a Claude Code skill for dialogue + an MCP tool for real computation.

**Goal:** Give researchers (especially students) proactive feedback on methodological weaknesses *before* data collection, and help them calculate statistically justified sample sizes.

---

## Architecture

All new code is additive — no changes to v1 files except `server.py` (new imports + tool registrations) and `pyproject.toml` (new dependency).

**New files:**

| File | Responsibility |
|------|---------------|
| `osf_assistant/tools/bias.py` | `check_bias` tool — validates design fields, generates risk report |
| `osf_assistant/tools/power.py` | `calculate_power` tool — computes required N via scipy/statsmodels |
| `skills/check-bias.md` | Skill: 3-path entry, collects design data, presents bias report |
| `skills/power-analysis.md` | Skill: explains parameters, calls calculate_power, interprets result |
| `tests/test_bias.py` | Tests for check_bias |
| `tests/test_power.py` | Tests for calculate_power |

**Modified files:**

| File | Change |
|------|--------|
| `osf_assistant/server.py` | Add imports + `mcp.tool()(check_bias)` + `mcp.tool()(calculate_power)` |
| `pyproject.toml` | Add `statsmodels>=0.14.0` to dependencies |

---

## Data Flow

### check-bias
```
Skill entry choice:
  A) Structured questions → dict
  B) Path to preregistration file → tool reads + parses file
  C) Free-text description → Claude extracts structure → dict

  → check_bias(data=dict, preregistration_path=str|None)
  → Python: validate fields, check N, generate structured flags
  → Returns Markdown risk report
  → Skill (Claude) adds free-form commentary on top
  → Suggests: "Fix design and update preregistration? Run /preregister"
```

### power-analysis
```
User provides test_type, effect_size, alpha, power
  (Skill helps explain and choose values if needed)
  → calculate_power(test_type, effect_size, alpha=0.05, power=0.80)
  → statsmodels solver → required N
  → Returns dict with n_per_group, n_total, interpretation, formula_used
  → Skill presents result + fallback advice if N is unrealistic
```

---

## MCP Tools

### `check_bias(data: dict = None, preregistration_path: str = None) -> str`

At least one parameter must be provided — raises `ValueError` otherwise.

**If `preregistration_path` provided:** reads the Markdown file, parses sections by `##` headers, extracts field values into a dict.

**Rule-based checks:**

| Flag | Severity | Condition |
|------|----------|-----------|
| No randomization stated | 🔴 Critical | `design` field doesn't contain "random" / "рандом" |
| No control group mentioned | 🔴 Critical | `design` doesn't contain "control" / "контрол" / "placebo" |
| Low power risk | 🟡 Important | N < 30 (between-subjects) or N < 20 (within-subjects) |
| Blinding not mentioned | 🟡 Important | `design` doesn't contain "blind" / "mask" |
| Corrections not specified | 🟡 Important | `corrections` empty or "none" when multiple DVs present |
| Not uploaded to OSF | 🟠 Advisory | No OSF URL in the data |

**Returns Markdown:**
```markdown
## Bias & Methodology Risk Report

### 🔴 Critical
- No randomization stated in Design section

### 🟡 Important
- Low power risk: N=24 may be insufficient for between-subjects design
- Blinding not mentioned

### ✅ No issues detected
- Hypotheses explicitly stated
- Analysis plan specified
```

**Raises:**
- `ValueError` if both parameters are None
- `FileNotFoundError` if `preregistration_path` doesn't exist

---

### `calculate_power(test_type: str, effect_size: float, alpha: float = 0.05, power: float = 0.80) -> dict`

**Supported test types (v2):**

| `test_type` | Effect metric | Backend |
|------------|--------------|---------|
| `"ttest"` | Cohen's d | `statsmodels TTestIndPower` |
| `"anova"` | Cohen's f | `statsmodels FTestAnovaPower` |
| `"correlation"` | Pearson r | `statsmodels NormalIndPower` (Fisher z) |

Adding `"chi2"` and `"regression"` in v3 requires only a new entry in the dispatch dict — no architectural change.

**Returns dict:**
```python
{
    "test_type": "ttest",
    "effect_size": 0.5,
    "alpha": 0.05,
    "power": 0.80,
    "n_per_group": 64,
    "n_total": 128,
    "interpretation": "For a medium effect (d=0.5) with α=0.05 and 80% power, you need 64 participants per group (128 total).",
    "formula": "Two-sample independent t-test (Cohen, 1988)"
}
```

**Raises:**
- `ValueError` for unknown `test_type` (with list of valid options)
- `ValueError` for invalid parameter ranges: `effect_size <= 0`, `alpha` outside (0,1), `power` outside (0,1)

**Dependency:** `statsmodels>=0.14.0` (added to `pyproject.toml`)

---

## Skills

### `check-bias`

Three entry paths — skill asks which to use:
- **A) Structured questions** — 5 questions: design type, N, blinding, control group, analysis plan → builds dict → calls `check_bias(data=dict)`
- **B) Preregistration file** — asks for path → calls `check_bias(preregistration_path=path)`
- **C) Free text** — user pastes description → Claude extracts structure → calls `check_bias(data=extracted)`

After receiving the MCP report: skill adds 2-3 sentences of free-form LLM analysis, then offers: "Want to fix the design? Run /preregister"

### `power-analysis`

Short skill — explains parameters and calls the tool:
1. Explain test_type / effect_size / alpha / power with examples
2. Help user choose values (defaults: d=0.5, α=0.05, power=0.80 for medium effect)
3. Call `calculate_power(...)`
4. Present result + fallback: "If N is unrealistic, consider reducing power to 0.70 or redesigning the study"

Experienced users who provide all parameters upfront skip directly to step 3.

---

## Dependencies

Add to `pyproject.toml`:
```toml
"statsmodels>=0.14.0",
```

scipy comes as a transitive dependency of statsmodels.

---

## Out of Scope (v2)

- chi-square and regression power analysis (v3)
- Integration with preregister skill (auto-run check-bias after preregistration)
- EQUATOR/CONSORT checklist integration
- Statcheck (p-value consistency checking)
