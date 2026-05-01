import json
import os
from datetime import date, datetime
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

VALID_TEMPLATES = {"osf_standard", "aspredicted"}


def generate_preregistration(data: dict, template: str = "osf_standard") -> str:
    """Generate an OSF-compatible preregistration Markdown file from collected data.

    Args:
        data: Dict with fields matching the chosen template schema.
        template: 'osf_standard' or 'aspredicted'.

    Returns:
        Absolute path to the saved Markdown file.
    """
    if template not in VALID_TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Valid options: {sorted(VALID_TEMPLATES)}")

    template_path = TEMPLATES_DIR / f"{template}.json"
    with open(template_path, encoding="utf-8") as f:
        schema = json.load(f)

    merged = {**schema, **data, "generated_date": date.today().isoformat()}
    content = _render_markdown(merged)

    output_dir = Path(os.getenv("OUTPUT_DIR", "./preregistrations"))
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"preregistration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return str(output_path.resolve())


def _render_markdown(data: dict) -> str:
    """Render merged preregistration data as a Markdown document."""
    template_type = data.get("template_type", "osf_standard")
    lines = [
        f"# Pre-Registration: {data.get('title', 'Untitled')}",
        f"**Date:** {data.get('generated_date', '')}",
        f"**Template:** {template_type}",
        "",
        "## Context",
        data.get("context", ""),
        "",
        "## Hypotheses",
        f"**H0:** {data.get('h0', '')}",
        f"**H1:** {data.get('h1', '')}",
        "",
        "## Design",
        data.get("design", ""),
        "",
        "## Variables",
        f"**Independent variable(s):** {data.get('iv', '')}",
        f"**Dependent variable(s):** {data.get('dv', '')}",
    ]

    if template_type == "osf_standard":
        lines += [
            f"**Covariates:** {data.get('covariates', 'None')}",
            f"**Measurement:** {data.get('measurement', '')}",
        ]

    lines += [
        "",
        "## Sample",
        f"**Planned N:** {data.get('n', '')}",
    ]

    if template_type == "osf_standard":
        lines += [
            f"**Inclusion criteria:** {data.get('inclusion_criteria', '')}",
            f"**Exclusion criteria:** {data.get('exclusion_criteria', '')}",
        ]

    lines += [
        "",
        "## Analysis Plan",
        f"**Statistical test:** {data.get('test', '')}",
        f"**Alpha threshold (α):** {data.get('alpha', '0.05')}",
    ]

    if template_type == "osf_standard":
        lines.append(
            f"**Corrections for multiple comparisons:** {data.get('corrections', 'None')}"
        )

    return "\n".join(lines)
