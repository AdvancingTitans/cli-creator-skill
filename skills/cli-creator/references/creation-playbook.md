# CLI Creation Playbook

Use this playbook to build a modern Python CLI from zero.

## Phase 0: Requirements And Type Selection

Classify the CLI:

- Command-first: fast commands, stable flags, JSON output.
- Configuration-driven: config discovery, precedence, reproducibility.
- Interactive/hybrid: first-run wizard, prompts, state machine.
- Data/LLM: evidence, cache, provider verification, structured output.
- Performance-heavy: startup, concurrency, streaming, cache.
- Plugin-based: extension API and adapter contracts.

Write:

- one-sentence product promise
- main command examples
- non-goals for v1
- expected output forms
- failure/recovery model

## Phase 1: Command Design

Design examples before code.

```bash
my-cli --help
my-cli init
my-cli check .
my-cli fetch "query" --json
my-cli export result --output report.md
my-cli config show
my-cli doctor
```

Rules:

- Required domain objects are arguments.
- Behavior modifiers are options.
- Mutating commands use clear verbs.
- Machine-readable output is explicit.
- Global options are consistent: `--config`, `--verbose`, `--quiet`, `--debug`, `--no-color`.

## Phase 2: Project Initialization

Recommended package layout:

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
    settings.py
    config.py
    models.py
    app/
    services/
    renderers/
  tests/
```

Recommended `pyproject.toml`:

```toml
[project]
name = "my-cli"
version = "0.1.0"
requires-python = ">=3.10"
readme = "README.md"
dependencies = [
  "typer>=0.12",
  "rich>=13",
  "pydantic>=2",
  "pydantic-settings>=2",
  "platformdirs>=4",
  "httpx>=0.27",
]

[project.scripts]
my-cli = "my_cli.cli:main"

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.8"]
```

Use `uv` for environment, build, and release workflows when available.

## Phase 3: Core Models And Boundaries

Define models early:

- `AppContext`: console, settings, logger, paths.
- `Settings`: validated config.
- `CommandRequest`: parsed input for a command.
- `CommandResult`: structured output and exit status.
- `CacheEntry`: key, status, payload, created_at, expires_at.
- `EvidenceItem`: source-backed data for data/LLM CLIs.
- `ProviderConfig`: provider/base URL/model/credential reference.

Boundaries:

- `cli.py`: Typer/Click only.
- `app/`: orchestration.
- `services/`: IO and domain operations.
- `renderers/`: terminal/JSON/Markdown.
- `config.py`: config discovery and precedence.
- `errors.py`: domain exceptions and exit mapping.

## Phase 4: Configuration

Implement precedence:

1. flags
2. env vars
3. project config
4. user config
5. defaults

Provide commands:

```text
my-cli config show
my-cli config path
my-cli config set KEY VALUE
my-cli config reset
```

For credentials:

- mask values in output
- prefer keychain or env refs for secrets
- never commit real `.env`

## Phase 5: Rendering And Output

Create a single console factory.

Human modes:

- tables for rows
- panels for summaries
- progress for long-running work
- Markdown for long generated text

Machine modes:

- JSON without Rich markup
- stable schema
- documented exit codes

## Phase 6: Cache, Logs, And Diagnostics

Add cache only with clear semantics:

- cache key includes query/input/config/schema/source
- cache status distinguishes failures from valid empty results
- `--refresh` bypasses or varies cache
- `cache clear` exists

Add `doctor` when the CLI has config, network, credentials, optional tools, model providers, or generated entry points.

## Phase 7: Interactive Or LLM Workflows

For interactive flows:

- one question at a time
- state object
- non-TTY fallback
- remembered profile with `profile show` and `profile clear`

For LLM flows:

- verify provider before workflow
- validate structured output
- separate facts from model inference
- retain evidence and prompt/model metadata

## Phase 8: Tests

Minimum tests:

- package import
- `--help`
- top-level command help
- config precedence
- errors and exit codes
- JSON validity
- cache hit/miss/refresh
- clean install smoke test

Use subprocess tests for installed command confidence.

## Phase 9: Release

Checklist:

- `README.md` has real install and usage commands
- `CHANGELOG.md` updated
- `pyproject.toml` metadata complete
- wheel/sdist build succeeds
- clean venv install succeeds
- no secrets in repo
- CI runs lint and tests

Use tag-driven releases when publishing to PyPI. Keep sensitive release setup out of public docs.
