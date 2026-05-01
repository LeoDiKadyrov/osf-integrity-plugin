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
