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
