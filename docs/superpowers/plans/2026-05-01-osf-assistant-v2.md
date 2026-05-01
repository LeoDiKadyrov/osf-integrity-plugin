# OSF Assistant v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `check_bias` and `calculate_power` MCP tools + two Claude Code skills to the existing OSF Assistant plugin.

**Architecture:** Two new tool modules following the v1 pattern (`osf_assistant/tools/bias.py`, `osf_assistant/tools/power.py`), each with TDD tests, registered in the existing FastMCP server. Skills are Markdown files in `skills/`.

**Tech Stack:** Python 3.11+, `statsmodels>=0.14.0` (power analysis), `scipy` (transitive dep of statsmodels), existing `fastmcp`, `pytest`.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `pyproject.toml` | Modify | Add `statsmodels>=0.14.0` dependency |
| `osf_assistant/tools/bias.py` | Create | `check_bias` tool — field validation, rule-based flags, Markdown report |
| `osf_assistant/tools/power.py` | Create | `calculate_power` tool — statsmodels power solver |
| `osf_assistant/server.py` | Modify | Register `check_bias` and `calculate_power` |
| `skills/check-bias.md` | Create | 3-path dialogue skill for bias checking |
| `skills/power-analysis.md` | Create | Parameter explanation + tool call skill |
| `tests/test_bias.py` | Create | Tests for check_bias |
| `tests/test_power.py` | Create | Tests for calculate_power |

---

## Task 1: Add statsmodels dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add statsmodels to pyproject.toml**

Edit `pyproject.toml` — change the `dependencies` list to:

```toml
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "statsmodels>=0.14.0",
]
```

- [ ] **Step 2: Install**

```bash
pip install -e ".[dev]"
```

Expected: no errors.

- [ ] **Step 3: Verify import**

```bash
python -c "from statsmodels.stats.power import TTestIndPower, FTestAnovaPower, NormalIndPower; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add statsmodels dependency for power analysis"
```

---

## Task 2: `check_bias` tool

**Files:**
- Create: `osf_assistant/tools/bias.py`
- Create: `tests/test_bias.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_bias.py`:

```python
import pytest
from pathlib import Path
from osf_assistant.tools.bias import check_bias


def test_check_bias_raises_without_args():
    with pytest.raises(ValueError, match="Both cannot be None"):
        check_bias()


def test_check_bias_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        check_bias(preregistration_path="/nonexistent/file.md")


def test_check_bias_detects_missing_randomization():
    data = {
        "design": "Between-subjects, two groups compared on score",
        "n": "30",
        "corrections": "None",
        "dv": "Score",
    }
    report = check_bias(data=data)
    assert "🔴 Critical" in report
    assert "randomization" in report.lower()


def test_check_bias_detects_missing_control_group():
    data = {
        "design": "Randomized between-subjects experiment",
        "n": "40",
        "corrections": "None",
        "dv": "Score",
    }
    report = check_bias(data=data)
    assert "🔴 Critical" in report
    assert "control" in report.lower()


def test_check_bias_detects_low_n_between_subjects():
    data = {
        "design": "Between-subjects randomized controlled trial. Control group receives placebo.",
        "n": "15",
        "corrections": "None",
        "dv": "Score",
    }
    report = check_bias(data=data)
    assert "Low power risk" in report
    assert "N=15" in report


def test_check_bias_passes_clean_design():
    data = {
        "design": "Between-subjects randomized double-blind controlled trial. Control group receives placebo.",
        "n": "60",
        "corrections": "Bonferroni",
        "dv": "Score",
    }
    report = check_bias(data=data)
    assert "## Bias & Methodology Risk Report" in report
    assert "🔴 Critical" not in report


def test_check_bias_reads_preregistration_file(tmp_path):
    content = """# Pre-Registration: Test Study
**Date:** 2026-05-01
**Template:** osf_standard

## Context
Testing memory consolidation.

## Hypotheses
**H0:** No effect
**H1:** Some effect

## Design
Between-subjects randomized double-blind controlled trial. Control group receives placebo.

## Variables
**Independent variable(s):** Condition
**Dependent variable(s):** Recall score
**Covariates:** None
**Measurement:** Word recall task

## Sample
**Planned N:** 60 (30 per group)
**Inclusion criteria:** Adults 18-35
**Exclusion criteria:** None

## Analysis Plan
**Statistical test:** Independent samples t-test
**Alpha threshold (α):** 0.05
**Corrections for multiple comparisons:** None
"""
    f = tmp_path / "preregistration_20260501_120000.md"
    f.write_text(content, encoding="utf-8")

    report = check_bias(preregistration_path=str(f))
    assert "## Bias & Methodology Risk Report" in report
    assert "🔴 Critical" not in report


def test_check_bias_warns_multiple_dvs_no_corrections():
    data = {
        "design": "Between-subjects randomized controlled trial with blinding. Control group.",
        "n": "60",
        "corrections": "None",
        "dv": "Score, Reaction time, Accuracy",
    }
    report = check_bias(data=data)
    assert "multiple" in report.lower() or "corrections" in report.lower()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python -m pytest tests/test_bias.py -v
```

Expected: `ImportError` — module doesn't exist yet.

- [ ] **Step 3: Implement `osf_assistant/tools/bias.py`**

Create `osf_assistant/tools/bias.py`:

```python
import re
from pathlib import Path


def check_bias(data: dict = None, preregistration_path: str = None) -> str:
    """Analyze an experiment design for methodological biases and risks.

    Args:
        data: Dict with design fields (design, n, corrections, dv, etc.)
        preregistration_path: Path to a Markdown preregistration file from generate_preregistration.

    Returns:
        Markdown-formatted bias risk report.

    Raises:
        ValueError: If both data and preregistration_path are None.
        FileNotFoundError: If preregistration_path doesn't exist.
    """
    if data is None and preregistration_path is None:
        raise ValueError(
            "Provide either 'data' dict or 'preregistration_path'. Both cannot be None."
        )

    if preregistration_path is not None:
        path = Path(preregistration_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {preregistration_path}")
        content = path.read_text(encoding="utf-8")
        data = _parse_preregistration(content)

    flags = _run_checks(data)
    return _render_report(flags)


def _parse_preregistration(content: str) -> dict:
    """Extract structured fields from a preregistration Markdown file."""
    result = {}

    # Extract section bodies by splitting on ## headers
    sections = re.split(r'\n## ', '\n' + content)
    for section in sections[1:]:
        lines = section.split('\n')
        section_name = lines[0].strip().lower().replace(' ', '_')
        body = '\n'.join(lines[1:]).strip()
        result[section_name] = body

    # Extract specific inline field values
    for line in content.split('\n'):
        if line.startswith('**Planned N:**'):
            result['n'] = line.replace('**Planned N:**', '').strip()
        elif line.startswith('**Corrections for multiple comparisons:**'):
            result['corrections'] = line.replace(
                '**Corrections for multiple comparisons:**', ''
            ).strip()
        elif line.startswith('**Dependent variable(s):**'):
            result['dv'] = line.replace('**Dependent variable(s):**', '').strip()

    return result


def _extract_n(n_str: str) -> int | None:
    """Extract the first integer from an N string like '64 (32 per group)'."""
    if not n_str:
        return None
    match = re.search(r'\d+', str(n_str))
    return int(match.group()) if match else None


def _run_checks(data: dict) -> dict:
    """Run all bias checks and return categorized flags."""
    critical = []
    important = []
    advisory = []
    ok = []

    design = data.get('design', '') or ''
    design_lower = design.lower()

    # 1. Randomization
    if any(kw in design_lower for kw in ['random', 'рандом']):
        ok.append("Randomization mentioned in design")
    else:
        critical.append("No randomization stated in Design section")

    # 2. Control group
    if any(kw in design_lower for kw in ['control', 'контрол', 'placebo', 'comparison group']):
        ok.append("Control/comparison group mentioned")
    else:
        critical.append("No control group or comparison condition mentioned in Design section")

    # 3. N / statistical power
    n_str = data.get('n', '') or ''
    n = _extract_n(n_str)
    is_between = 'between' in design_lower
    is_within = 'within' in design_lower
    threshold = 20 if (is_within and not is_between) else 30

    if n is not None:
        if n < threshold:
            design_type = 'within' if (is_within and not is_between) else 'between'
            important.append(
                f"Low power risk: N={n} may be insufficient for {design_type}-subjects design "
                f"(recommended minimum: {threshold})"
            )
        else:
            ok.append(f"Sample size N={n} meets minimum threshold")
    else:
        important.append("Sample size (N) not specified or could not be parsed")

    # 4. Blinding
    if any(kw in design_lower for kw in ['blind', 'mask']):
        ok.append("Blinding mentioned")
    else:
        important.append("Blinding not mentioned in Design section")

    # 5. Multiple comparisons corrections
    corrections = (data.get('corrections', '') or '').lower().strip()
    dv = data.get('dv', '') or ''
    multiple_dvs = ',' in dv or ';' in dv

    if multiple_dvs and corrections in ('none', 'no', ''):
        important.append(
            "Multiple dependent variables detected but no corrections for multiple comparisons specified"
        )
    elif corrections and corrections not in ('none', 'no', ''):
        ok.append(f"Corrections for multiple comparisons specified: {corrections}")

    # 6. OSF upload advisory
    if not data.get('osf_url'):
        advisory.append(
            "Study not yet uploaded to OSF — preregister before data collection"
        )

    return {'critical': critical, 'important': important, 'advisory': advisory, 'ok': ok}


def _render_report(flags: dict) -> str:
    """Render bias check results as a Markdown report."""
    lines = ["## Bias & Methodology Risk Report", ""]

    if flags['critical']:
        lines.append("### 🔴 Critical")
        for f in flags['critical']:
            lines.append(f"- {f}")
        lines.append("")

    if flags['important']:
        lines.append("### 🟡 Important")
        for f in flags['important']:
            lines.append(f"- {f}")
        lines.append("")

    if flags['advisory']:
        lines.append("### 🟠 Advisory")
        for f in flags['advisory']:
            lines.append(f"- {f}")
        lines.append("")

    if flags['ok']:
        lines.append("### ✅ No issues detected")
        for f in flags['ok']:
            lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines).strip()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python -m pytest tests/test_bias.py -v
```

Expected: all 8 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/bias.py tests/test_bias.py
git commit -m "feat: add check_bias tool"
```

---

## Task 3: `calculate_power` tool

**Files:**
- Create: `osf_assistant/tools/power.py`
- Create: `tests/test_power.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_power.py`:

```python
import pytest
import math
from osf_assistant.tools.power import calculate_power


def test_calculate_power_ttest_medium_effect():
    result = calculate_power("ttest", effect_size=0.5)
    assert result["test_type"] == "ttest"
    assert result["n_per_group"] == 64  # canonical result: Cohen's d=0.5, α=0.05, power=0.80
    assert result["n_total"] == 128
    assert "64" in result["interpretation"]
    assert "Cohen's d" in result["interpretation"]


def test_calculate_power_raises_on_unknown_test():
    with pytest.raises(ValueError, match="Unknown test_type"):
        calculate_power("regression", effect_size=0.5)


def test_calculate_power_raises_on_invalid_effect_size():
    with pytest.raises(ValueError, match="effect_size must be > 0"):
        calculate_power("ttest", effect_size=0.0)


def test_calculate_power_raises_on_invalid_alpha():
    with pytest.raises(ValueError, match="alpha must be between"):
        calculate_power("ttest", effect_size=0.5, alpha=1.5)


def test_calculate_power_raises_on_invalid_power():
    with pytest.raises(ValueError, match="power must be between"):
        calculate_power("ttest", effect_size=0.5, power=0.0)


def test_calculate_power_correlation():
    result = calculate_power("correlation", effect_size=0.3)
    assert result["test_type"] == "correlation"
    assert result["n_per_group"] == result["n_total"]  # single sample, no groups
    assert result["n_per_group"] > 0
    assert "Pearson r" in result["interpretation"]


def test_calculate_power_anova():
    result = calculate_power("anova", effect_size=0.25)
    assert result["test_type"] == "anova"
    assert result["n_total"] == result["n_per_group"] * 2
    assert result["n_per_group"] > 0
    assert "Cohen's f" in result["interpretation"]


def test_calculate_power_returns_all_required_fields():
    result = calculate_power("ttest", effect_size=0.5, alpha=0.05, power=0.80)
    required = {"test_type", "effect_size", "alpha", "power", "n_per_group", "n_total",
                "interpretation", "formula"}
    assert required.issubset(result.keys())


def test_calculate_power_higher_power_needs_more_n():
    result_80 = calculate_power("ttest", effect_size=0.5, power=0.80)
    result_90 = calculate_power("ttest", effect_size=0.5, power=0.90)
    assert result_90["n_per_group"] > result_80["n_per_group"]


def test_calculate_power_smaller_effect_needs_more_n():
    result_medium = calculate_power("ttest", effect_size=0.5)
    result_small = calculate_power("ttest", effect_size=0.2)
    assert result_small["n_per_group"] > result_medium["n_per_group"]
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python -m pytest tests/test_power.py -v
```

Expected: `ImportError` — module doesn't exist yet.

- [ ] **Step 3: Implement `osf_assistant/tools/power.py`**

Create `osf_assistant/tools/power.py`:

```python
import math
from scipy import stats
from statsmodels.stats.power import TTestIndPower, FTestAnovaPower

VALID_TESTS = {"ttest", "anova", "correlation"}

_EFFECT_LABELS = {
    "ttest": "Cohen's d",
    "anova": "Cohen's f",
    "correlation": "Pearson r",
}

_FORMULAS = {
    "ttest": "Two-sample independent t-test (Cohen, 1988)",
    "anova": "One-way ANOVA, 2 groups (Cohen, 1988)",
    "correlation": "Pearson correlation, Fisher z-transform (Cohen, 1988)",
}


def calculate_power(
    test_type: str,
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> dict:
    """Calculate the required sample size for a given statistical test.

    Args:
        test_type: One of 'ttest', 'anova', 'correlation'.
        effect_size: Expected effect size (Cohen's d for ttest, Cohen's f for anova,
                     Pearson r for correlation).
        alpha: Significance threshold, default 0.05.
        power: Desired statistical power, default 0.80.

    Returns:
        Dict with keys: test_type, effect_size, alpha, power, n_per_group, n_total,
        interpretation, formula.

    Raises:
        ValueError: For unknown test_type or invalid parameter ranges.
    """
    if test_type not in VALID_TESTS:
        raise ValueError(
            f"Unknown test_type '{test_type}'. Valid options: {sorted(VALID_TESTS)}"
        )
    if effect_size <= 0:
        raise ValueError(f"effect_size must be > 0, got {effect_size}")
    if not (0 < alpha < 1):
        raise ValueError(f"alpha must be between 0 and 1 (exclusive), got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"power must be between 0 and 1 (exclusive), got {power}")

    n_per_group = _compute_n(test_type, effect_size, alpha, power)
    n_total = n_per_group if test_type == "correlation" else n_per_group * 2

    label = _EFFECT_LABELS[test_type]
    group_info = (
        f" per group ({n_total} total)" if test_type != "correlation" else ""
    )
    interpretation = (
        f"For {label}={effect_size} with α={alpha} and {int(power * 100)}% power, "
        f"you need {n_per_group} participants{group_info}."
    )

    return {
        "test_type": test_type,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "n_per_group": n_per_group,
        "n_total": n_total,
        "interpretation": interpretation,
        "formula": _FORMULAS[test_type],
    }


def _compute_n(test_type: str, effect_size: float, alpha: float, power: float) -> int:
    """Compute required N per group using statsmodels / scipy."""
    if test_type == "ttest":
        n = TTestIndPower().solve_power(
            effect_size=effect_size, alpha=alpha, power=power
        )
    elif test_type == "anova":
        n = FTestAnovaPower().solve_power(
            effect_size=effect_size, alpha=alpha, power=power, k_groups=2
        )
    elif test_type == "correlation":
        # Fisher z-transform: n = ((z_α + z_β) / z_r)² + 3
        z_r = math.atanh(abs(effect_size))
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        n = ((z_alpha + z_beta) / z_r) ** 2 + 3

    return math.ceil(n)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python -m pytest tests/test_power.py -v
```

Expected: all 10 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add osf_assistant/tools/power.py tests/test_power.py
git commit -m "feat: add calculate_power tool"
```

---

## Task 4: Register new tools in server.py

**Files:**
- Modify: `osf_assistant/server.py`

- [ ] **Step 1: Update server.py**

Replace the content of `osf_assistant/server.py` with:

```python
from dotenv import load_dotenv
from fastmcp import FastMCP
from osf_assistant.tools.preregistration import generate_preregistration, osf_upload
from osf_assistant.tools.evidence import search_evidence, format_evidence_table
from osf_assistant.tools.bias import check_bias
from osf_assistant.tools.power import calculate_power

load_dotenv()

mcp = FastMCP(name="OSF Assistant")

mcp.tool()(generate_preregistration)
mcp.tool()(osf_upload)
mcp.tool()(search_evidence)
mcp.tool()(format_evidence_table)
mcp.tool()(check_bias)
mcp.tool()(calculate_power)

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Verify server imports cleanly**

```bash
python -c "import osf_assistant.server; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest -v
```

Expected: all 28 tests `PASSED` (18 existing + 8 bias + 10 power — wait, 18 + 8 + 10 = 36... let me recalculate: 8 evidence + 10 preregistration existing = 18, + 8 bias + 10 power = 36 total).

Expected: all 36 tests `PASSED`.

- [ ] **Step 4: Commit**

```bash
git add osf_assistant/server.py
git commit -m "feat: register check_bias and calculate_power in MCP server"
```

---

## Task 5: Skills

**Files:**
- Create: `skills/check-bias.md`
- Create: `skills/power-analysis.md`

- [ ] **Step 1: Write `skills/check-bias.md`**

```markdown
---
name: check-bias
description: Analyze an experiment design for methodological biases and risks. Accepts structured questions, a preregistration file path, or free-text description. Returns a risk report with severity flags.
---

# Bias & Methodology Check Workflow

Identify methodological weaknesses in a research design **before** data collection. All rule-based checks are done by the MCP tool `check_bias`. You add free-form analysis on top.

---

## Step 1 — Choose Entry Path

Ask:
> "How would you like to provide your experiment design?
> - **A)** I'll answer a few structured questions
> - **B)** I have a preregistration file (generated by /preregister)
> - **C)** I'll paste a free-text description"

---

## Path A — Structured Questions

Ask these 5 questions one at a time:

**A1.** "Describe your study design: Is it between-subjects or within-subjects? Experimental or observational? Does it include a control group?"

**A2.** "How many participants (N) are you planning to collect?"

**A3.** "Is blinding used? (single-blind, double-blind, or none)"

**A4.** "What are your dependent variables (DVs)? List all of them."

**A5.** "Will you apply corrections for multiple comparisons? (e.g. Bonferroni, FDR, or None)"

After all answers, call:

```
check_bias(data={
  "design": <A1 answer>,
  "n": <A2 answer>,
  "dv": <A4 answer>,
  "corrections": <A5 answer>
})
```

---

## Path B — Preregistration File

Ask:
> "Provide the path to your preregistration file (e.g. `./preregistrations/preregistration_20260501_120000.md`)."

Call:
```
check_bias(preregistration_path=<path>)
```

---

## Path C — Free Text

Ask:
> "Paste your experiment description. Include: design type, sample size, control group, blinding, DVs, and analysis plan."

Extract the following fields from the description, then call:
```
check_bias(data={
  "design": <extracted design description>,
  "n": <extracted sample size>,
  "dv": <extracted dependent variables>,
  "corrections": <extracted corrections plan>
})
```

---

## Step 2 — Present Report + Add Analysis

After receiving the MCP report:

1. Show the report to the user as-is.
2. Add 2-3 sentences of free-form analysis, e.g.:
   - Why a flagged issue matters for their specific research question
   - Whether any 🔴 Critical flags are fatal or fixable
   - What the most impactful improvement would be

3. Ask:
> "Would you like to redesign and update your preregistration? Run /preregister to start over, or I can help you revise specific sections."
```

- [ ] **Step 2: Write `skills/power-analysis.md`**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add skills/check-bias.md skills/power-analysis.md
git commit -m "feat: add check-bias and power-analysis skills"
```

---

## Self-Review

**Spec coverage:**
- ✅ `check_bias(data, preregistration_path)` with rule-based flags: Task 2
- ✅ Raises ValueError if both None: Task 2 test
- ✅ Raises FileNotFoundError if path missing: Task 2 test
- ✅ Parses preregistration Markdown file: `_parse_preregistration` in Task 2
- ✅ Flags: no randomization (🔴), no control (🔴), low N (🟡), no blinding (🟡), multiple DVs no corrections (🟡), no OSF URL (🟠): Task 2
- ✅ `calculate_power(test_type, effect_size, alpha, power)`: Task 3
- ✅ Supports ttest, anova, correlation: Task 3
- ✅ Extensible to chi2/regression (just add to VALID_TESTS + _compute_n): Task 3 architecture
- ✅ Returns n_per_group, n_total, interpretation, formula: Task 3
- ✅ Raises ValueError for unknown test_type and invalid params: Task 3 tests
- ✅ Register both tools in server.py: Task 4
- ✅ `check-bias` skill, 3 entry paths: Task 5
- ✅ `power-analysis` skill with parameter explanation: Task 5
- ✅ statsmodels dependency: Task 1

**Placeholder scan:** No TBDs. All code blocks complete.

**Type consistency:**
- `check_bias(data: dict = None, preregistration_path: str = None)` — used consistently in tests and skill
- `calculate_power(test_type: str, effect_size: float, alpha: float, power: float)` — used consistently
- `n_per_group` / `n_total` — consistent between implementation and tests
