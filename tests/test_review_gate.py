from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "cli_creator_review_gate.py"
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def load_gate_module():
    spec = importlib.util.spec_from_file_location("cli_creator_review_gate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = load_gate_module()
CURRENT_VERSION = gate.parse_pyproject(ROOT)["version"]


def copy_repo_to_temp(tmp_root: Path) -> Path:
    dest = tmp_root / "repo"
    shutil.copytree(
        ROOT,
        dest,
        ignore=shutil.ignore_patterns(".git", "dist", "__pycache__", "promo-copy.md"),
    )
    return dest


class ReviewGateTests(unittest.TestCase):
    def test_gate_help_works(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Validate cli-creator governance metadata", completed.stdout)

    def test_gate_succeeds_on_repo(self):
        exit_code, grouped = gate.run_gate(ROOT)
        self.assertEqual(exit_code, 0)
        self.assertIn("skill_overview.md", grouped)
        self.assertTrue((ROOT / "reports" / "skill_overview.md").exists())

    def test_broken_fixture_fails_skill_heading_validation(self):
        fixture = ROOT / "evals" / "audit_fixtures" / "broken_skill_missing_output_headings.md"
        findings = gate.validate_skill_document(ROOT, fixture)
        failures = [item for item in findings if item.status == "FAIL"]
        self.assertTrue(failures)
        self.assertTrue(any("missing" in item.message for item in failures))

    def test_missing_required_output_section_fails(self):
        sample = (ROOT / "evals" / "audit_fixtures" / "output_missing_test_gaps.md").read_text(
            encoding="utf-8"
        )
        missing = gate.validate_output_sample(sample)
        self.assertIn("Test Gaps", missing)

    def test_reports_use_relative_evidence_paths(self):
        gate.run_gate(ROOT)
        for report_name in gate.DEFAULT_REPORTS:
            text = (ROOT / "reports" / report_name).read_text(encoding="utf-8")
            self.assertNotIn("/Users/yjw/", text)

    def test_installer_copies_skill_tree(self):
        from cli_creator_skill import installer

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir)
            with mock.patch.object(
                installer, "skill_source", return_value=ROOT / "skills" / "cli-creator"
            ):
                dest = installer.install(target)
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertTrue((dest / "references" / "review-rubric.md").exists())

    def test_wheel_inspection_detects_required_members(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            wheel_path = Path(tmp_dir) / "fixture.whl"
            with zipfile.ZipFile(wheel_path, "w") as archive:
                for member in gate.WHEEL_REQUIRED_MEMBERS:
                    archive.writestr(member, "fixture")
                archive.writestr(
                    f"cli_creator_skill-{CURRENT_VERSION}.dist-info/METADATA",
                    f"Name: cli-creator-skill\nVersion: {CURRENT_VERSION}\n",
                )
            findings = gate.inspect_wheel(ROOT, wheel_path)
            self.assertTrue(all(item.status == "PASS" for item in findings if item.blocking))

    def test_wheel_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            wheel_path = Path(tmp_dir) / "old.whl"
            with zipfile.ZipFile(wheel_path, "w") as archive:
                for member in gate.WHEEL_REQUIRED_MEMBERS:
                    archive.writestr(member, "fixture")
                mismatch_version = "0.0.0" if CURRENT_VERSION != "0.0.0" else "0.0.1"
                archive.writestr(
                    f"cli_creator_skill-{mismatch_version}.dist-info/METADATA",
                    f"Name: cli-creator-skill\nVersion: {mismatch_version}\n",
                )
            findings = gate.inspect_wheel(ROOT, wheel_path)
            target = next(item for item in findings if item.check == "wheel:metadata-version")
            self.assertEqual(target.status, "FAIL")

    def test_trust_check_is_not_hardcoded(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = copy_repo_to_temp(Path(tmp_dir))
            registry_path = temp_root / "registry" / "package.json"
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data.pop("trust_level", None)
            registry_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            findings = gate.validate_trust(temp_root)
            target = next(item for item in findings if item.check == "trust:registry-trust-level")
            self.assertEqual(target.status, "FAIL")

    def test_package_version_parity_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = copy_repo_to_temp(Path(tmp_dir))
            init_path = temp_root / "src" / "cli_creator_skill" / "__init__.py"
            init_path.write_text(
                '"""Installer package for the cli-creator skill."""\n\n__version__ = "0.0.0"\n',
                encoding="utf-8",
            )
            findings = gate.validate_registry(temp_root)
            target = next(item for item in findings if item.check == "registry:package-version-parity")
            self.assertEqual(target.status, "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
