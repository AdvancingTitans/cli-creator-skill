# Changelog

## 0.1.4

- Slim `skills/cli-creator/SKILL.md` into a router while preserving the CLI type selection, minimal CLI/YAGNI rule, creation flow, review flow, and fixed audit headings.
- Add lightweight Skill OS governance routing for `skill-ir/`, `evals/`, `scripts/`, `reports/`, and `registry/` when maintaining the package.
- Clarify the one-command review gate, package verification path, and wheel/install confidence checks.
- Keep the four reference documents as the source of implementation detail instead of duplicating them in `SKILL.md`.

## 0.1.3

- Make CLI reviews executable with required reference loading, fixed output sections, scores, repair order, test gaps, and verification commands.
- Add a verification command pack for source installs, help/version checks, JSON validation, builds, wheel installs, and tests.
- Add audit coverage for CLI-related skills/templates, including triggers, references, output contracts, command templates, verification, and maintenance strategy.
- Strengthen security, cross-platform, LLM, and testing guidance.
- Add a minimal CLI exception to avoid over-engineering small internal scripts.

## 0.1.2

- Broaden the skill for command-first, configuration-driven, hybrid, and performance-oriented CLIs.
- Add technical best practices for Typer/Click, config precedence, Rich rendering, cache, errors, packaging, and LLM-enabled CLIs.
- Add audit guidance for machine-readable diagnostics, cache status metadata, and release-copy drift.

## 0.1.1

- Remove public release setup details from README.

## 0.1.0

- Initial release of the `cli-creator` skill.
- Add installable PyPI package with `cli-creator-skill install`.
- Add creation playbook, pitfalls reference, and review rubric.
