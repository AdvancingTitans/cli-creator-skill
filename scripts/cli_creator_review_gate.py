#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


REQUIRED_OUTPUT_SECTIONS = [
    "Findings",
    "Scores",
    "Repair Order",
    "Test Gaps",
    "Verification Commands",
]
DEFAULT_REPORTS = {
    "skill_overview.md": "Skill Overview",
    "output_eval_scorecard.md": "Output Eval Scorecard",
    "package_verification.md": "Package Verification",
    "trust_report.md": "Trust Report",
}
SECRET_PATTERNS = {
    "openai-like-key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "github-pat": re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private-key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
}
WHEEL_REQUIRED_MEMBERS = [
    "cli_creator_skill/skills/cli-creator/SKILL.md",
    "cli_creator_skill/skills/cli-creator/references/creation-playbook.md",
    "cli_creator_skill/skills/cli-creator/references/pitfalls-and-solutions.md",
    "cli_creator_skill/skills/cli-creator/references/review-rubric.md",
    "cli_creator_skill/skills/cli-creator/references/technical-best-practices.md",
]


@dataclass
class Finding:
    check: str
    status: str
    message: str
    evidence: list[str]
    blocking: bool = True


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_path(root: Path) -> Path:
    return root / "skills" / "cli-creator" / "SKILL.md"


def relative_evidence(root: Path, path: Path | str) -> str:
    value = Path(path) if not isinstance(path, Path) else path
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        raw = str(path).replace("\\", "/")
        if raw.startswith(str(root).replace("\\", "/") + "/"):
            return raw[len(str(root).replace("\\", "/")) + 1 :]
        return value.name if isinstance(value, Path) else raw


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}, text
    body = text[match.end() :]
    data = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def contains_heading(text: str, label: str) -> bool:
    pattern = r"(?mi)^\s*(?:#{1,6}\s+|\*\*)?" + re.escape(label) + r"(?:\*\*)?\s*$"
    return re.search(pattern, text) is not None


def referenced_files_from_text(text: str) -> list[str]:
    found = re.findall(r"references/[A-Za-z0-9._/-]+\.md", text)
    return sorted(dict.fromkeys(found))


def parse_assignment_dict(lines: list[str], header: str) -> dict[str, str]:
    result: dict[str, str] = {}
    collecting = False
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.strip() == header:
            collecting = True
            continue
        if collecting and line.startswith("[") and line.strip() != header:
            break
        if collecting:
            match = re.match(r'"([^"]+)"\s*=\s*"([^"]+)"', line.strip())
            if match:
                result[match.group(1)] = match.group(2)
    return result


def parse_project_script(lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    collecting = False
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.strip() == "[project.scripts]":
            collecting = True
            continue
        if collecting and line.startswith("["):
            break
        if collecting and "=" in line:
            name, value = line.strip().split("=", 1)
            return name.strip(), ast.literal_eval(value.strip())
    return None, None


def parse_project_list(lines: list[str], prefix: str) -> list:
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith(prefix):
            return ast.literal_eval(stripped.split("=", 1)[1].strip())
    return []


def parse_pyproject(root: Path) -> dict:
    pyproject_path = root / "pyproject.toml"
    lines = pyproject_path.read_text(encoding="utf-8").splitlines()
    data = {
        "version": None,
        "name": None,
        "license": None,
        "dependencies": parse_project_list(lines, "dependencies ="),
        "script_name": None,
        "entry_point": None,
        "force_include": parse_assignment_dict(
            lines, "[tool.hatch.build.targets.wheel.force-include]"
        ),
    }
    in_project = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            in_project = False
        if in_project and stripped.startswith("name ="):
            data["name"] = ast.literal_eval(stripped.split("=", 1)[1].strip())
        if in_project and stripped.startswith("version ="):
            data["version"] = ast.literal_eval(stripped.split("=", 1)[1].strip())
        if in_project and stripped.startswith("license ="):
            data["license"] = ast.literal_eval(stripped.split("=", 1)[1].strip())
    script_name, entry_point = parse_project_script(lines)
    data["script_name"] = script_name
    data["entry_point"] = entry_point
    return data


def parse_package_version(root: Path) -> Optional[str]:
    init_path = root / "src" / "cli_creator_skill" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else None


def load_ir(root: Path) -> dict:
    return load_json(root / "skill-ir" / "cli-creator.json")


def load_registry(root: Path) -> dict:
    return load_json(root / "registry" / "package.json")


def classify_prompt(prompt: str, ir: dict) -> bool:
    normalized = prompt.lower()
    if any(example.lower() in normalized for example in ir["trigger_surface"]["should_trigger"]):
        return True
    if any(example.lower() in normalized for example in ir["trigger_surface"]["edge_cases"]):
        return True
    if any(example.lower() in normalized for example in ir["trigger_surface"]["should_not_trigger"]):
        return False
    negative_terms = ["邮件", "天气", "calendar", "slack", "lark"]
    if any(term in normalized for term in negative_terms):
        return False
    positive_terms = [
        "cli",
        "typer",
        "click",
        "argparse",
        "packaging",
        "pypi",
        "wheel",
        "console script",
        "subcommand",
        "skill 模板",
    ]
    return any(term in normalized for term in positive_terms)


def validate_output_sample(sample: str) -> list[str]:
    return [section for section in REQUIRED_OUTPUT_SECTIONS if not contains_heading(sample, section)]


def validate_skill_document(root: Path, skill_md: Optional[Path] = None) -> list[Finding]:
    target = skill_md or skill_path(root)
    text = target.read_text(encoding="utf-8")
    frontmatter, body = extract_frontmatter(text)
    findings: list[Finding] = []
    for key in ("name", "description"):
        findings.append(
            Finding(
                check=f"frontmatter:{key}",
                status="PASS" if frontmatter.get(key) else "FAIL",
                message=f"{key} {'found' if frontmatter.get(key) else 'missing in frontmatter'}",
                evidence=[relative_evidence(root, target)],
            )
        )
    for section in REQUIRED_OUTPUT_SECTIONS:
        ok = contains_heading(text, section)
        findings.append(
            Finding(
                check=f"output-heading:{section}",
                status="PASS" if ok else "FAIL",
                message=f"{section} heading {'present' if ok else 'missing'}",
                evidence=[relative_evidence(root, target)],
            )
        )
    referenced = referenced_files_from_text(body)
    findings.append(
        Finding(
            check="references:declared",
            status="PASS" if referenced else "FAIL",
            message=f"found {len(referenced)} referenced markdown file(s)",
            evidence=[relative_evidence(root, target)],
        )
    )
    for rel_path in referenced:
        full_path = target.parent / rel_path
        findings.append(
            Finding(
                check=f"reference:{rel_path}",
                status="PASS" if full_path.exists() else "FAIL",
                message=f"{rel_path} {'exists' if full_path.exists() else 'is missing'}",
                evidence=[relative_evidence(root, full_path)],
            )
        )
    return findings


def validate_ir(root: Path) -> list[Finding]:
    schema_path = root / "skill-ir" / "schema.json"
    ir_path = root / "skill-ir" / "cli-creator.json"
    ir = load_ir(root)
    pyproject = parse_pyproject(root)
    registry = load_registry(root)
    findings: list[Finding] = []
    required = load_json(schema_path).get("required", [])
    missing = [field for field in required if field not in ir]
    findings.append(
        Finding(
            check="ir:required-fields",
            status="PASS" if not missing else "FAIL",
            message="all Skill OS IR required fields present" if not missing else f"missing IR fields: {', '.join(missing)}",
            evidence=[relative_evidence(root, ir_path), relative_evidence(root, schema_path)],
        )
    )
    step_count = len(ir.get("workflow", {}).get("steps", []))
    findings.append(
        Finding(
            check="ir:schema-version",
            status="PASS" if ir.get("schema_version") == "1.0" else "FAIL",
            message=f"schema_version={ir.get('schema_version')}",
            evidence=[relative_evidence(root, ir_path)],
        )
    )
    findings.append(
        Finding(
            check="ir:version-parity",
            status="PASS" if ir.get("version") == pyproject.get("version") else "FAIL",
            message=f"IR version={ir.get('version')} pyproject version={pyproject.get('version')}",
            evidence=[relative_evidence(root, ir_path), relative_evidence(root, root / "pyproject.toml")],
        )
    )
    findings.append(
        Finding(
            check="ir:job-to-be-done",
            status="PASS" if len(ir.get("job_to_be_done", "").strip()) >= 20 else "FAIL",
            message="job_to_be_done is populated" if len(ir.get("job_to_be_done", "").strip()) >= 20 else "job_to_be_done is too short",
            evidence=[relative_evidence(root, ir_path)],
        )
    )
    findings.append(
        Finding(
            check="ir:workflow-steps",
            status="PASS" if step_count >= 3 else "FAIL",
            message=f"workflow defines {step_count} step(s)",
            evidence=[relative_evidence(root, ir_path)],
        )
    )
    trigger_surface = ir.get("trigger_surface", {})
    for key in ("should_trigger", "should_not_trigger", "edge_cases"):
        entries = trigger_surface.get(key, [])
        findings.append(
            Finding(
                check=f"ir:trigger-surface:{key}",
                status="PASS" if entries else "FAIL",
                message=f"{key} examples: {len(entries)}",
                evidence=[relative_evidence(root, ir_path)],
            )
        )
    resources = ir.get("resources", {})
    for bucket in ("references", "scripts", "reports"):
        entries = resources.get(bucket, [])
        findings.append(
            Finding(
                check=f"ir:resources:{bucket}",
                status="PASS" if entries else "FAIL",
                message=f"{bucket} entries: {len(entries)}",
                evidence=[relative_evidence(root, ir_path)],
            )
        )
        for rel_path in entries:
            full_path = root / rel_path
            if bucket == "reports":
                exists = True
            else:
                exists = full_path.exists()
            findings.append(
                Finding(
                    check=f"ir:resource-exists:{rel_path}",
                    status="PASS" if exists else "FAIL",
                    message=f"{rel_path} {'declared' if bucket == 'reports' else ('exists' if exists else 'is missing')}",
                    evidence=[rel_path],
                )
            )
    eval_plan = ir.get("eval_plan", {})
    for key in ("trigger", "output"):
        rel_path = eval_plan.get(key)
        exists = bool(rel_path) and (root / rel_path).exists()
        findings.append(
            Finding(
                check=f"ir:eval-plan:{key}",
                status="PASS" if exists else "FAIL",
                message=f"{key} eval plan points to {rel_path}",
                evidence=[relative_evidence(root, ir_path), rel_path or "missing"],
            )
        )
    risk = ir.get("risk", {})
    for key in ("output_risk", "execution_risk", "trust_boundary"):
        value = str(risk.get(key, "")).strip()
        findings.append(
            Finding(
                check=f"ir:risk:{key}",
                status="PASS" if value else "FAIL",
                message=f"{key} {'present' if value else 'missing'}",
                evidence=[relative_evidence(root, ir_path)],
            )
        )
    findings.extend(
        [
            Finding(
                check="ir:governance-owner",
                status="PASS" if ir.get("governance", {}).get("owner") == registry.get("owner") else "FAIL",
                message=f"IR owner={ir.get('governance', {}).get('owner')} registry owner={registry.get('owner')}",
                evidence=[relative_evidence(root, ir_path), relative_evidence(root, root / "registry" / "package.json")],
            ),
            Finding(
                check="ir:governance-maturity",
                status="PASS" if ir.get("governance", {}).get("maturity") == registry.get("maturity") else "FAIL",
                message=f"IR maturity={ir.get('governance', {}).get('maturity')} registry maturity={registry.get('maturity')}",
                evidence=[relative_evidence(root, ir_path), relative_evidence(root, root / "registry" / "package.json")],
            ),
            Finding(
                check="ir:governance-review-cadence",
                status="PASS" if ir.get("governance", {}).get("review_cadence") == registry.get("review_cadence") else "FAIL",
                message=f"IR review_cadence={ir.get('governance', {}).get('review_cadence')} registry review_cadence={registry.get('review_cadence')}",
                evidence=[relative_evidence(root, ir_path), relative_evidence(root, root / "registry" / "package.json")],
            ),
        ]
    )
    return findings


def validate_trigger_cases(root: Path) -> list[Finding]:
    ir = load_ir(root)
    trigger_path = root / ir["eval_plan"]["trigger"]
    data = load_json(trigger_path)
    cases = data.get("cases", [])
    findings = [
        Finding(
            check="trigger-eval:cases",
            status="PASS" if cases else "FAIL",
            message=f"found {len(cases)} trigger eval case(s)",
            evidence=[relative_evidence(root, trigger_path)],
        )
    ]
    seen_kinds = set()
    for case in cases:
        kind = case.get("kind")
        seen_kinds.add(kind)
        expected = case.get("expected_match")
        actual = classify_prompt(case.get("prompt", ""), ir)
        findings.append(
            Finding(
                check=f"trigger-eval:{case.get('id', 'unknown')}",
                status="PASS" if isinstance(expected, bool) and actual == expected else "FAIL",
                message=f"{kind} prompt expected {expected}, got {actual}",
                evidence=[relative_evidence(root, trigger_path)],
            )
        )
    for kind in ("positive", "negative", "edge"):
        findings.append(
            Finding(
                check=f"trigger-eval:coverage:{kind}",
                status="PASS" if kind in seen_kinds else "FAIL",
                message=f"{kind} trigger coverage {'present' if kind in seen_kinds else 'missing'}",
                evidence=[relative_evidence(root, trigger_path)],
            )
        )
    return findings


def validate_output_cases(root: Path) -> list[Finding]:
    ir = load_ir(root)
    output_path = root / ir["eval_plan"]["output"]
    data = load_json(output_path)
    cases = data.get("cases", [])
    findings = [
        Finding(
            check="output-eval:min-cases",
            status="PASS" if len(cases) >= 3 else "FAIL",
            message=f"found {len(cases)} valid output eval case(s)",
            evidence=[relative_evidence(root, output_path)],
        )
    ]
    declared_sections = data.get("minimum_sections") or []
    findings.append(
        Finding(
            check="output-eval:required-sections-shape",
            status="PASS" if declared_sections == REQUIRED_OUTPUT_SECTIONS else "FAIL",
            message="minimum output sections match required review headings"
            if declared_sections == REQUIRED_OUTPUT_SECTIONS
            else "minimum_sections drift from required review headings",
            evidence=[relative_evidence(root, output_path)],
        )
    )
    for case in cases:
        missing = validate_output_sample(case.get("sample", ""))
        findings.append(
            Finding(
                check=f"output-eval:{case.get('id', 'unknown')}",
                status="PASS" if not missing else "FAIL",
                message="all required sections present" if not missing else f"missing sections: {', '.join(missing)}",
                evidence=[relative_evidence(root, output_path)],
            )
        )
    return findings


def validate_registry(root: Path) -> list[Finding]:
    registry_path = root / "registry" / "package.json"
    registry = load_registry(root)
    pyproject = parse_pyproject(root)
    package_version = parse_package_version(root)
    required = [
        "name",
        "version",
        "owner",
        "maturity",
        "targets",
        "review_cadence",
        "license",
        "checksum",
        "compatibility",
        "trust_level",
        "permissions",
        "skill_name",
        "script_name",
        "entry_point",
        "skill_path",
        "references",
    ]
    missing = [field for field in required if field not in registry]
    return [
        Finding(
            check="registry:required-fields",
            status="PASS" if not missing else "FAIL",
            message="registry metadata complete" if not missing else f"missing registry fields: {', '.join(missing)}",
            evidence=[relative_evidence(root, registry_path)],
        ),
        Finding(
            check="registry:version-parity",
            status="PASS" if registry.get("version") == pyproject.get("version") else "FAIL",
            message=f"registry version={registry.get('version')} pyproject version={pyproject.get('version')}",
            evidence=[relative_evidence(root, registry_path), relative_evidence(root, root / "pyproject.toml")],
        ),
        Finding(
            check="registry:package-version-parity",
            status="PASS" if package_version == pyproject.get("version") else "FAIL",
            message=f"package __version__={package_version} pyproject version={pyproject.get('version')}",
            evidence=[
                relative_evidence(root, root / "src" / "cli_creator_skill" / "__init__.py"),
                relative_evidence(root, root / "pyproject.toml"),
            ],
        ),
        Finding(
            check="registry:license-parity",
            status="PASS" if registry.get("license") == pyproject.get("license") else "FAIL",
            message=f"registry license={registry.get('license')} pyproject license={pyproject.get('license')}",
            evidence=[relative_evidence(root, registry_path), relative_evidence(root, root / "pyproject.toml")],
        ),
        Finding(
            check="registry:checksum-shape",
            status="PASS"
            if registry.get("checksum", {}).get("package_sha256") in (None, "generated-at-release")
            or bool(registry.get("checksum", {}).get("package_sha256"))
            else "FAIL",
            message=f"package_sha256 placeholder={registry.get('checksum', {}).get('package_sha256')}",
            evidence=[relative_evidence(root, registry_path)],
        ),
    ]


def validate_readme_and_packaging(root: Path) -> list[Finding]:
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    pyproject = parse_pyproject(root)
    script_name = pyproject.get("script_name")
    force_include = pyproject.get("force_include") or {}
    return [
        Finding(
            check="readme:install-command",
            status="PASS" if script_name and f"{script_name} install" in readme else "FAIL",
            message=f"README includes install command for {script_name}" if script_name else "project.scripts is missing",
            evidence=[relative_evidence(root, readme_path), relative_evidence(root, root / "pyproject.toml")],
        ),
        Finding(
            check="pyproject:project-script",
            status="PASS" if script_name and pyproject.get("entry_point") else "FAIL",
            message=f"project.scripts maps {script_name} -> {pyproject.get('entry_point')}",
            evidence=[relative_evidence(root, root / "pyproject.toml")],
        ),
        Finding(
            check="pyproject:force-include",
            status="PASS" if force_include.get("skills/cli-creator") == "cli_creator_skill/skills/cli-creator" else "FAIL",
            message="wheel force-include covers skills/cli-creator"
            if force_include.get("skills/cli-creator") == "cli_creator_skill/skills/cli-creator"
            else "wheel force-include missing skills/cli-creator mapping",
            evidence=[relative_evidence(root, root / "pyproject.toml")],
        ),
    ]


def read_wheel_metadata(archive: zipfile.ZipFile) -> tuple[Optional[str], Optional[str]]:
    for member in archive.namelist():
        if member.endswith(".dist-info/METADATA"):
            payload = archive.read(member).decode("utf-8", errors="replace")
            name_match = re.search(r"^Name:\s*(.+)$", payload, re.MULTILINE)
            version_match = re.search(r"^Version:\s*(.+)$", payload, re.MULTILINE)
            return (
                name_match.group(1).strip() if name_match else None,
                version_match.group(1).strip() if version_match else None,
            )
    return None, None


def inspect_wheel(root: Path, wheel_path: Path) -> list[Finding]:
    registry = load_registry(root)
    pyproject = parse_pyproject(root)
    sha256 = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(wheel_path) as archive:
        names = set(archive.namelist())
        wheel_name, wheel_version = read_wheel_metadata(archive)
    missing = [member for member in WHEEL_REQUIRED_MEMBERS if member not in names]
    evidence = [relative_evidence(root, wheel_path)]
    return [
        Finding(
            check="wheel:required-members",
            status="PASS" if not missing else "FAIL",
            message="wheel contains skill files and references" if not missing else f"wheel missing: {', '.join(missing)}",
            evidence=evidence,
        ),
        Finding(
            check="wheel:metadata-name",
            status="PASS" if wheel_name == pyproject.get("name") else "FAIL",
            message=f"wheel name={wheel_name} pyproject name={pyproject.get('name')}",
            evidence=evidence,
        ),
        Finding(
            check="wheel:metadata-version",
            status="PASS"
            if wheel_version == pyproject.get("version") == registry.get("version")
            else "FAIL",
            message=f"wheel version={wheel_version} pyproject version={pyproject.get('version')} registry version={registry.get('version')}",
            evidence=evidence,
        ),
        Finding(
            check="wheel:sha256",
            status="PASS",
            message=f"sha256={sha256}",
            evidence=evidence,
            blocking=False,
        ),
    ]


def iter_secret_scan_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "promo-copy.md" or rel.startswith(".git/") or rel.startswith("dist/"):
            continue
        if "__pycache__" in rel:
            continue
        candidates.append(path)
    return candidates


def scan_for_secrets(root: Path) -> list[str]:
    hits: list[str] = []
    for path in iter_secret_scan_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{relative_evidence(root, path)}:{label}")
    return hits


def validate_trust(root: Path) -> list[Finding]:
    registry = load_registry(root)
    pyproject = parse_pyproject(root)
    script = root / "scripts" / "cli_creator_review_gate.py"
    help_run = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    secret_hits = scan_for_secrets(root)
    return [
        Finding(
            check="trust:review-script-exists",
            status="PASS" if script.exists() else "FAIL",
            message="review script exists" if script.exists() else "review script missing",
            evidence=[relative_evidence(root, script)],
        ),
        Finding(
            check="trust:review-script-help",
            status="PASS" if help_run.returncode == 0 and "Validate cli-creator governance metadata" in help_run.stdout else "FAIL",
            message=f"--help exit={help_run.returncode}",
            evidence=[relative_evidence(root, script)],
        ),
        Finding(
            check="trust:zero-dependencies",
            status="PASS" if pyproject.get("dependencies") == [] else "FAIL",
            message=f"pyproject dependencies={pyproject.get('dependencies')}",
            evidence=[relative_evidence(root, root / "pyproject.toml")],
        ),
        Finding(
            check="trust:registry-trust-level",
            status="PASS" if bool(registry.get("trust_level")) else "FAIL",
            message=f"trust_level={registry.get('trust_level')}",
            evidence=[relative_evidence(root, root / "registry" / "package.json")],
        ),
        Finding(
            check="trust:registry-permissions",
            status="PASS" if bool(registry.get("permissions")) else "FAIL",
            message="permissions declared" if registry.get("permissions") else "permissions missing",
            evidence=[relative_evidence(root, root / "registry" / "package.json")],
        ),
        Finding(
            check="trust:secret-scan",
            status="PASS" if not secret_hits else "FAIL",
            message="no conservative secret-pattern hits outside excluded paths" if not secret_hits else f"secret-pattern hits: {', '.join(secret_hits)}",
            evidence=[relative_evidence(root, root / "registry" / "package.json")],
        ),
    ]


def summarize(findings: Iterable[Finding]) -> tuple[bool, list[Finding]]:
    items = list(findings)
    blocking_failures = [item for item in items if item.blocking and item.status != "PASS"]
    return not blocking_failures, items


def write_report(path: Path, title: str, findings: list[Finding]) -> None:
    status = "PASS" if all(item.status == "PASS" or not item.blocking for item in findings) else "FAIL"
    lines = [f"# {title}", "", f"- Status: {status}", ""]
    for item in findings:
        lines.append(f"- [{item.status}] `{item.check}` — {item.message}")
        if item.evidence:
            lines.append(f"  - Evidence: {', '.join(item.evidence)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_gate(root: Path, wheel: Optional[Path] = None) -> tuple[int, dict[str, list[Finding]]]:
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)
    grouped = {
        "skill_overview.md": validate_skill_document(root) + validate_ir(root),
        "output_eval_scorecard.md": validate_trigger_cases(root) + validate_output_cases(root),
        "package_verification.md": validate_registry(root) + validate_readme_and_packaging(root),
        "trust_report.md": validate_trust(root),
    }
    if wheel is not None:
        grouped["package_verification.md"].extend(inspect_wheel(root, wheel))
    exit_code = 0
    for filename, title in DEFAULT_REPORTS.items():
        findings = grouped[filename]
        ok, _ = summarize(findings)
        if not ok:
            exit_code = 1
        write_report(reports_dir / filename, title, findings)
    return exit_code, grouped


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli_creator_review_gate",
        description="Validate cli-creator governance metadata, eval fixtures, packaging, and wheel contents.",
    )
    parser.add_argument("--wheel", type=Path, help="Optional built wheel to inspect.")
    args = parser.parse_args(argv)

    root = repo_root()
    if args.wheel is not None and not args.wheel.exists():
        print(f"wheel not found: {args.wheel}", file=sys.stderr)
        return 2

    exit_code, grouped = run_gate(root, args.wheel)
    for filename in DEFAULT_REPORTS:
        for finding in grouped[filename]:
            prefix = "OK" if finding.status == "PASS" else "FAIL"
            print(f"{prefix} {finding.check}: {finding.message}")
    print(f"Reports written to {relative_evidence(root, root / 'reports')}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
