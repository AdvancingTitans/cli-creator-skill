# cli-creator

`cli-creator` is a reusable agent skill for designing, building, and auditing high-quality Python CLI tools.

It is especially useful for Typer + Rich + questionary projects with interactive flows, data fetching, caching, LLM provider setup, structured output, local profile memory, and multi-channel delivery.

## Install As A Codex Skill

Clone this repository and copy the skill directory into your Codex skills folder:

```bash
git clone https://github.com/AdvancingTitans/cli-creator-skill.git
mkdir -p ~/.codex/skills
cp -R cli-creator-skill/skills/cli-creator ~/.codex/skills/cli-creator
```

Then ask your agent to use `cli-creator` when creating or reviewing CLI tools.

## Install From PyPI

```bash
pip install cli-creator-skill
cli-creator-skill install
```

By default this installs the skill to `~/.codex/skills/cli-creator`.

Install to a custom directory:

```bash
cli-creator-skill install --target ~/.agents/skills
```

## Release

Maintainers can publish a new version by updating `pyproject.toml`, committing the change, and pushing a version tag:

```bash
git tag v0.1.3
git push origin v0.1.3
```

## What This Skill Helps With

- Design a new Python CLI from scratch.
- Review an existing CLI for UX, packaging, errors, model setup, caching, and maintainability.
- Structure Typer + Rich + questionary applications.
- Build natural multi-turn CLI flows without making users feel like they are filling out a form.
- Add robust model provider configuration for OpenAI, Anthropic, Ark/OpenAI-compatible endpoints, and local models.
- Add cache, profile memory, diagnostics, and first-run setup flows.
- Audit machine-readable diagnostics, cache status metadata, package-data drift, and release-copy synchronization.
- Enforce review outputs with findings, scores, repair order, test gaps, and verification commands.
- Review CLI-related skills and templates for trigger clarity, reference completeness, command templates, output contracts, and maintenance strategy.

## Repository Structure

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
  pyproject.toml
  README.md
  LICENSE
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
