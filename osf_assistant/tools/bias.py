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
