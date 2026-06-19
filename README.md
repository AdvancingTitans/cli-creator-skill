# cli-creator

`cli-creator` is a reusable agent skill for designing, building, and auditing Python CLI tools.

`skills/cli-creator/SKILL.md` is intentionally a router. The detailed guidance lives in the four reference docs, while maintainer-side governance can live in lightweight workspace-root folders when you need them.

## Install As A Codex Skill

Copy the skill directory into your Codex skills folder:

```bash
git clone https://github.com/AdvancingTitans/cli-creator-skill.git
mkdir -p ~/.codex/skills
cp -R cli-creator-skill/skills/cli-creator ~/.codex/skills/cli-creator
```

Then ask your agent to use `cli-creator` when creating or reviewing CLI tools.

## Install From PyPI

The console script is `cli-creator-skill`.

```bash
pip install cli-creator-skill
cli-creator-skill install
```

Install to a custom directory:

```bash
cli-creator-skill install --target ~/.agents/skills
```

Source install is the same console script after editable install:

```bash
uv pip install -e .
cli-creator-skill install
```

## Lightweight Skill OS Governance

When you maintain this package, keep the governance artifacts small and local to the workspace root. Use them as routing aids, not as shipped skill content:

- `skill-ir/` — skill intent, review notes, and IR snapshots.
- `evals/` — evaluation cases and result checks.
- `scripts/` — one-off gates and helper commands, including `scripts/cli_creator_review_gate.py`.
- `reports/` — the four Markdown audit reports emitted by the review gate.
- `registry/` — skill/package registry notes.

## One-Command Review Gate

For a quick package check, run the review gate directly:

```bash
python3 scripts/cli_creator_review_gate.py
```

For release verification, build the wheel first and then run the gate against the built wheel:

```bash
tmpdir=$(mktemp -d) && uv build --out-dir "$tmpdir" && python3 scripts/cli_creator_review_gate.py --wheel "$tmpdir"/cli_creator_skill-*.whl
```

## What This Skill Helps With

- Design a new Python CLI from scratch.
- Review an existing CLI for UX, packaging, errors, model setup, caching, and maintainability.
- Structure Typer, Click, argparse, or hybrid applications.
- Build natural multi-turn CLI flows without making users feel like they are filling out a form.
- Add diagnostics, cache, profile memory, and first-run setup flows when they are actually needed.
- Review CLI-related skills and templates for trigger clarity, reference completeness, command templates, output contracts, and maintenance strategy.

## Repository Structure

Maintainer-side governance folders are shown here as workspace-root aids, not as generated output and not as bundled skill content:

```text
cli-creator-skill/
  skills/cli-creator/
    SKILL.md
    references/
      creation-playbook.md
      pitfalls-and-solutions.md
      review-rubric.md
      technical-best-practices.md
  src/cli_creator_skill/
    installer.py
    __main__.py
  tests/
  .github/workflows/test.yml
  skill-ir/
  evals/
  scripts/
  reports/
  registry/
```

## Usage

Use this skill when you ask:

- "帮我从零设计一个 Python CLI"
- "帮我审查这个 Typer CLI"
- "这个 CLI 的交互很别扭，帮我重构"
- "帮我设计模型配置、缓存、doctor、profile memory"
- "帮我发布一个可 pip install 的 CLI"

## Design Basis

This skill distills maintainer experience and official documentation patterns for Python packaging, Typer, Click, Rich, uv, Ruff, Pydantic, and LLM provider integration. It does not vendor code or instructions from unofficial third-party repositories.

## License

MIT
