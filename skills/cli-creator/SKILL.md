---
name: cli-creator
description: Use when designing, scaffolding, refactoring, or auditing Python CLI tools, including command-first CLIs, configuration-driven tools, performance-oriented utilities, interactive assistants, data pipelines, and LLM-enabled command line products.
---

# CLI Creator

Use this skill to create or review production-grade Python CLI tools. Apply it to Typer, Click, argparse, or hybrid CLIs, with special attention to command design, configuration, terminal UX, packaging, performance, testability, and long-term maintenance.

## Step 1: Learn And Extract Principles

Before designing or reviewing a non-trivial CLI, ground your judgment in these patterns:

- Typer: prefer type-hint-driven command definitions, automatic help, shell completion, and gradual growth from one command to command trees.
- uv: treat speed, cache behavior, installability, and cross-platform distribution as product features, not backend details.
- Ruff: provide a cohesive command surface, fast defaults, file discovery rules, config-file support, and explicit CLI overrides.
- Rich: standardize terminal rendering through one console layer; use tables, panels, progress, Markdown, and rich tracebacks intentionally.
- HTTPie: optimize syntax and output for humans; make common actions short, natural, colorized, and inspectable.
- Your own CLI experience: never hide model/provider/config failures behind empty results; make cache, profile memory, refresh semantics, delivery channels, and diagnostics observable.

## Core Philosophy

Build CLIs as durable products, not one-off scripts.

1. Design from the user's job, not the implementation mode. A CLI should make the next action obvious.
2. Keep command semantics stable. Names, flags, exit codes, config keys, and output modes are product contracts.
3. Make defaults useful and safe. Zero-config should do something helpful, or fail with a concrete fix.
4. Separate routing, domain logic, IO, config, persistence, rendering, and integrations.
5. Optimize both humans and automation. Rich output is for people; JSON/plain output is for scripts.
6. Treat performance as UX. Startup, help, cache hits, file discovery, and progress feedback matter.
7. Make state explainable. Config, cache, credentials, profiles, history, and remote auth must be inspectable and resettable.
8. Verify installability early. The command in README must be the command installed from PyPI, uv, pipx, Homebrew, or standalone binaries.

## CLI Type Selection

Classify the CLI before choosing architecture.

| CLI type | Examples | Primary design concern | Architecture bias |
|---|---|---|---|
| Command-first utility | `ruff check`, `uv pip install`, data query tools | Fast, scriptable, predictable | Thin CLI, service layer, strict exit codes, JSON option |
| Configuration-driven tool | linters, formatters, deploy tools | Config precedence, discovery, reproducibility | Settings loader, config schema, project root detection |
| Interactive assistant | setup wizards, research assistants, LLM tools | Natural flow, state, recovery | Flow/state machine, prompts, profile/cache memory |
| Hybrid CLI | `run`, `setup`, `doctor`, `config`, `export` | Friendly first run plus automation | Commands wrap reusable orchestration services |
| Performance-heavy CLI | scanners, batch processors, package tools | Startup, concurrency, cache, progress | Lazy imports, compiled hot paths when needed, bounded IO |
| Plugin/extensible CLI | cloud tools, delivery-channel frameworks | Stable extension contracts | Adapter registry, entry points, versioned plugin API |

Do not force an interactive assistant architecture onto a command-first tool. Do not force a single-command script structure onto a growing product.

## New CLI Creation Workflow

### 1. Determine The Product Shape

Ask and answer:

- Who runs this CLI, and under what pressure?
- Is the main value a command result, a generated file, a changed remote state, or a guided decision?
- Does the user need zero-config use, project config, global config, or credentials?
- Will it be used in terminals only, or also cron, CI, automations, and pipes?
- What should be cached, remembered, logged, or deliberately forgotten?

### 2. Design The Command Surface

Prefer a small stable command tree:

```text
my-cli run                 # main workflow
my-cli init                # create project config or scaffold
my-cli config show         # inspect config safely
my-cli config set          # update config
my-cli doctor              # diagnose environment
my-cli cache clear         # clear derived state
my-cli completion          # shell completion, if not provided by framework
```

For command-first tools, prefer verbs that match user intent:

```text
my-cli check PATH
my-cli format PATH
my-cli fetch QUERY --json
my-cli export ID --output result.md
```

Rules:

- Use arguments for required domain objects.
- Use options for modifiers, output modes, and optional behavior.
- Provide `--json` or `--format json` for automation.
- Provide `--quiet`, `--verbose`, and `--debug` consistently.
- Avoid surprising network or mutation in commands that sound read-only.

### 3. Choose The Stack

Use Typer when type hints, async-ish orchestration, and Rich integration matter. Use Click when you need mature low-level control, custom contexts, or an existing Click ecosystem. Use argparse only for minimal standard-library scripts or dependency-sensitive tools.

Default Python stack:

- Typer or Click for command routing.
- Rich for terminal rendering and tracebacks.
- Pydantic v2 for domain models and validation.
- pydantic-settings for env/config loading.
- tomllib/tomli-w or `tomlkit` for project config.
- platformdirs for config/cache/data directories.
- httpx for HTTP with timeouts and retries.
- SQLite, diskcache, or sqlite-utils for durable local cache.
- loguru or stdlib logging with a single configured logger.
- pytest plus CliRunner or subprocess smoke tests.
- ruff for lint/format; uv for build, sync, and release workflows when available.

Add questionary only when prompts are core to the product. Add litellm/instructor only when LLM calls are genuinely needed.

### 4. Pick An Architecture Level

Choose the smallest architecture that will survive the next two releases:

- Single file: one or two commands, no config, no network, no long-term state.
- Small package: 3-8 commands, config, HTTP, output renderers, tests.
- Modular package: multiple workflows, cache, integrations, domain models, plugins.
- Plugin platform: stable extension API, third-party integrations, versioned contracts.

Never keep HTTP calls, prompt text, SQL, Rich tables, and Typer callbacks in the same module once the tool has real users.

### 5. Implement The Product Loop

For any workflow, make these explicit:

- Input collection.
- Validation.
- Execution.
- Rendering.
- Persistence.
- Exit code.
- Recovery hint.

For interactive flows, use a state object. For command-first flows, use request/result models.

### 6. Verify Before Shipping

Always verify:

- `my-cli --help`
- each top-level command `--help`
- clean install into a new venv
- missing config first run
- invalid config
- success path
- JSON/scriptable mode
- cache refresh and cache clear
- packaging metadata and console script

## Review Workflow

When auditing an existing CLI:

1. Inspect repository shape: package layout, command entry points, config files, tests, docs, CI.
2. Run help: `my-cli --help` and command-level help.
3. Trace one successful command from CLI callback to domain service to renderer.
4. Trace one failure path and inspect error quality.
5. Check configuration precedence: flags, env, project config, user config, defaults.
6. Check performance: startup imports, network timeouts, cache behavior, file discovery.
7. Check automation: exit codes, JSON output, non-TTY behavior.
8. Check packaging: Python version, dependencies, scripts, wheels, README commands.
9. Score with `references/review-rubric.md`.
10. Return findings first, then prioritized fixes.

## Common Pitfalls

Read `references/pitfalls-and-solutions.md` when implementing or auditing. Watch especially for:

- Command names that expose internals instead of user intent.
- Prompt-only workflows with no flags or non-TTY fallback.
- Config fields hidden behind a single "API key" setup.
- Undefined precedence between flags, env, local config, and global config.
- Slow `--help` caused by heavy imports or network probes.
- Pretty Rich output with no JSON mode.
- Cache failures stored as valid empty results.
- README install commands that do not match `[project.scripts]`.
- No `doctor` command for environment, auth, model, cache, and path issues.

## Recommended Structure

Use this as the default for a modern medium-sized CLI:

```text
my-cli/
  pyproject.toml
  README.md
  CHANGELOG.md
  .env.example
  src/my_cli/
    __init__.py
    __main__.py
    cli.py
    console.py
    errors.py
    models.py
    settings.py
    config.py
    paths.py
    logging.py
    app/
      __init__.py
      commands.py
      workflows.py
    services/
      __init__.py
      http.py
      cache.py
      domain.py
    renderers/
      __init__.py
      terminal.py
      json.py
      markdown.py
    integrations/
      __init__.py
      base.py
    plugins/
      __init__.py
      registry.py
  tests/
    test_cli_help.py
    test_config.py
    test_errors.py
    test_smoke.py
```

Read `references/creation-playbook.md` for scale-specific templates and implementation phases.

## Technical Best Practices

Read `references/technical-best-practices.md` when implementing:

- Typer callbacks, command groups, context objects, parameter validation, and completions.
- Config precedence with TOML, env vars, flags, and secrets.
- Rich rendering rules for tables, progress, panels, Markdown, and tracebacks.
- Cache, logs, error classes, exit codes, and JSON output.
- Packaging with `pyproject.toml`, uv, wheels, and CI.

## Output Expectations

For a new CLI, deliver:

- Product type decision.
- Command tree.
- Project structure.
- Core models and config schema.
- Main command implementation.
- Tests and smoke checks.
- README with real commands.

For a review, deliver:

- Findings ordered by severity.
- File/line references.
- Reproduction steps.
- Concrete fixes.
- Test gaps.
- Suggested migration sequence.

## References

- `references/pitfalls-and-solutions.md`
- `references/creation-playbook.md`
- `references/review-rubric.md`
- `references/technical-best-practices.md`
