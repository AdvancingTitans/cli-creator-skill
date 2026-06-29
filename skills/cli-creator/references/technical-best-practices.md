# CLI Technical Best Practices

Use this reference when implementing a Python CLI.

## Typer And Click Command Design

Prefer Typer when:

- Type annotations are the source of truth.
- You want automatic help and shell completion.
- The command tree is moderate and Python-native.
- Rich-styled errors and help are desirable.

Prefer Click when:

- You need mature context plumbing or custom command classes.
- You are extending an existing Click ecosystem.
- You need very fine-grained control over parsing behavior.

Rules:

- Keep callbacks thin. Use them for global options, shared context, and setup only.
- Put business logic in services or workflows.
- Use typed Enums for finite choices.
- Use `Path` parameters for files and directories.
- Use `Annotated` metadata for help strings, validation, and option behavior.
- Use `ctx.obj` or a small AppContext for shared console/settings/logger objects.
- Keep `--help` import-light; lazy-load heavy providers inside commands.

Good pattern:

```python
@app.callback()
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    ctx.obj = AppContext.from_cli(config_path=config, verbose=verbose)
```

## Command Semantics

Use consistent command names:

- `init`: create project files.
- `run`: execute the main workflow.
- `check`: analyze without mutation.
- `format` or `fix`: mutate local files.
- `sync`: reconcile local and remote state.
- `fetch`: retrieve data.
- `export`: write an artifact.
- `doctor`: diagnose environment.
- `config`: manage settings.
- `cache`: inspect and clear derived state.

Avoid:

- Internal names like `mode1`, `agent-flow`, `backend-refresh`.
- Mutating commands that sound read-only.
- Top-level commands that all do nearly the same thing.

For assistant and plugin CLIs, centralize command metadata instead of duplicating parser commands, slash commands, prompt suggestions, and docs. A descriptor should name the command, aliases, help text, source, visibility, feature gates, execution kind, machine-mode support, and permission needs. Use the descriptor to generate help, autocomplete, model-facing command lists, and tests.

Separate execution kinds:

- Pure command: returns text/JSON and is safe for scripts.
- Interactive command: renders prompts or TUI and is hidden from headless mode.
- Prompt command: expands into model instructions and declares allowed tools.
- Remote-safe command: has no local filesystem, shell, IDE, or TUI side effects.

Unknown or disabled commands should fail with a repair hint, not best-effort intent guessing.

## Configuration Precedence

Define and document precedence. Recommended:

1. Explicit CLI flags.
2. Environment variables.
3. Project config, such as `pyproject.toml`, `tool.my_cli`, or `my-cli.toml`.
4. User config under platformdirs config dir.
5. Built-in defaults.

Use pydantic-settings for env and model validation. Use TOML for project config. Use OS keychain or masked config for secrets when practical.

Commands to provide:

```text
my-cli config show
my-cli config path
my-cli config set KEY VALUE
my-cli config reset
my-cli doctor
```

For model providers, expose provider, base URL, model name, API key reference, timeout, and response mode separately.

## Rich Rendering

Create one shared `Console` factory. Do not instantiate ad hoc consoles across modules.

Use:

- `Table` for comparable records.
- `Panel` for summaries and warnings.
- `Progress` or `Status` for operations longer than one second.
- `Markdown` for generated reports or long explanations.
- Rich tracebacks only in debug/developer mode if normal users need concise errors.

Support:

- `--no-color`
- `--json`
- `--quiet`
- `--verbose`
- terminal width constraints
- non-TTY mode
- `NO_COLOR`
- CI logs

Never print Rich markup into JSON output.

## Errors And Exit Codes

Create domain errors:

- `UsageError`: wrong user input, exit 2.
- `ConfigError`: invalid or missing config, exit 2.
- `NetworkError`: request failed, exit 69 or 1.
- `AuthError`: missing/expired credentials, exit 77 or 1.
- `DataError`: invalid remote or local data, exit 65 or 1.
- `InternalError`: unexpected bug, exit 1.

Each error should include:

- What happened.
- Likely cause.
- Suggested command.
- Whether retry is safe.

Show tracebacks only with `--debug`.

## Logging

Rules:

- Human output goes through Rich console.
- Machine logs go through logging or loguru.
- Secrets are masked.
- Debug logs include config path, cache path, provider, timeout, and cache status, but not credentials.
- Logs should be optional unless the CLI is long-running or operational.

## Cache And Persistence

Use cache only when it improves speed, cost, or resilience.

Cache key should include:

- command or query
- normalized input
- version/schema
- relevant config
- time window
- source/provider

Cache entries should store status:

- `ok`
- `empty-valid`
- `partial`
- `error`

Do not let a failed request become a normal empty cache hit.

Provide:

```text
my-cli cache stats
my-cli cache clear
my-cli run --refresh
```

Expose cache state in diagnostics. A good `doctor --json` should distinguish unavailable cache, empty cache, valid empty result, stale data, and failed fetches that must not be reused.

## Performance

Measure:

- `my-cli --help`
- cold command startup
- hot cache path
- large input path
- network timeout path
- cancellation path
- non-TTY/scripted path

Patterns:

- Lazy import heavy libraries.
- Avoid network calls during import or help.
- Skip subcommand registration or plugin discovery on fast paths when the parsed mode cannot dispatch them.
- Use timeouts for all HTTP calls.
- Stream large files.
- Use concurrency only behind a clear service layer.
- Keep progress feedback honest; do not animate when nothing is happening.

## Security

Treat shell commands, config, plugins, and support bundles as trust boundaries.

Rules:

- Avoid `shell=True`; pass subprocess arguments as lists.
- Set timeouts for subprocesses, HTTP calls, provider probes, and plugin hooks.
- Normalize and validate paths before reading, writing, extracting, or caching.
- Reject path traversal outside intended roots.
- Use safe config parsers; never execute config files.
- Make untrusted plugins opt-in, versioned, and inspectable.
- Mask tokens in logs, config display, tracebacks, remote URLs, and support bundles.
- Keep telemetry opt-in or clearly disclosed with a working opt-out.
- Run dependency/supply-chain checks appropriate to the project before release.

For CLIs that can run tools, edit files, load plugins, or send remote mutations, define an explicit permission engine instead of scattering prompts through commands:

- Normalize paths before matching rules; handle symlinks, case-insensitive filesystems, `~`, glob patterns, and shell expansion syntax deliberately.
- Check deny rules before allow rules.
- Treat read, write, create, delete, shell, network, plugin install, and credential access as separate operation classes.
- Keep default diagnostics read-only; put repair behind explicit flags.
- Avoid broad "always allow" suggestions. Scope permission suggestions to the smallest command, path, plugin, or session that solves the task.
- Fail closed when a permission hook, classifier, plugin, or remote approval channel is unavailable.

## Cross-Platform Behavior

Design for macOS, Linux, Windows, CI, pipes, and narrow terminals when the tool is public.

Check:

- `pathlib` and platformdirs instead of hardcoded `/tmp`, home paths, or separators.
- PowerShell examples when docs claim Windows support.
- UTF-8 encoding and newline behavior for files, stdin, stdout, and stderr.
- TTY/non-TTY detection for prompts, progress, color, and paging.
- `NO_COLOR`, `--no-color`, `COLUMNS`, and CI terminal width.
- Shell completion for every supported shell, not just the author's shell.

Keep POSIX-only shortcuts acceptable for private/internal scripts, but name that constraint clearly.

## Packaging And Distribution

Use modern packaging:

```toml
[project]
name = "my-cli"
version = "0.1.0"
requires-python = ">=3.10"
readme = "README.md"

[project.scripts]
my-cli = "my_cli.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Verify:

- `python -m build` or `uv build`
- clean venv install
- installed command path
- `my-cli --help`
- `my-cli --version`
- each top-level command `--help`
- representative JSON output parsed with `python -m json.tool`
- PyPI README rendering
- required package data appears in wheel/sdist
- release copy matches source when publishing generated skills/templates

Use tag-driven CI releases for public packages. Keep release credentials out of docs and repository files.

## Testing

Minimum:

- import package
- command help
- command parser behavior
- config precedence
- errors and exit codes
- JSON output validity
- one success smoke test
- packaging metadata
- stdin/stdout/stderr separation
- invalid JSON/config and missing config paths
- non-TTY mode and color-disabled mode
- cancellation and timeout paths for long-running or networked commands
- installed-wheel smoke test from outside the repo

Use subprocess tests for installed-command confidence. Use Typer/Click runners for fast parser tests.

Avoid full snapshots of Rich output unless layout is the behavior under test. Prefer semantic assertions over parsed JSON, exit codes, stderr messages, and key table labels.

## LLM-Enabled CLIs

Only use LLMs where they add judgment or synthesis.

Rules:

- Verify provider config before a real workflow.
- Keep provider/base URL/model/API key separate.
- Validate structured outputs with Pydantic.
- Record model, response mode, prompt version, and validation errors.
- Provide deterministic fallback or clear failure.
- Never represent model guesses as sourced facts.
- Probe provider capabilities before selecting JSON mode, tool mode, streaming, or vision/audio features.
- Add structured-output fallback when provider support is partial.
- Log token and cost metadata when available.
- Apply retry/backoff for rate limits and transient network errors.
- Export an evidence bundle for research/data workflows: source objects, prompt/version metadata, provider/model, validation errors, and final outputs.
