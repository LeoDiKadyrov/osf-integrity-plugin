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
