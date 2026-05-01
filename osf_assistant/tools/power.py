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
