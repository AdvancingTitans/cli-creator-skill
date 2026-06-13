# CLI Pitfalls And Solutions

Use this reference when creating or auditing Python CLIs. It covers command-first tools, configuration-driven tools, interactive assistants, data/LLM CLIs, and performance-oriented utilities.

## 1. Starting From Framework Instead Of User Job

Problem: The tool is organized around internal modes instead of user goals.

Typical signs:

- Commands are named after implementation details.
- The first screen asks users to choose between abstract modes.
- README explains architecture before showing value.

Solution:

- Name commands after user verbs: `check`, `format`, `fetch`, `run`, `export`, `sync`.
- Put implementation modes behind flags or config.
- Start README with a 30-second demo.

Anti-pattern:

```text
my-cli agent-mode --pipeline backend-a
```

Better:

```text
my-cli fetch "AI safety" --since 30d --json
```

## 2. Over-Interactive Design For Scriptable Work

Problem: A command-first task is forced through prompts.

Typical signs:

- CI or cron cannot run the tool.
- questionary crashes in non-TTY contexts.
- Required inputs have no flags.

Solution:

- Provide flags for every prompt.
- Detect non-TTY and fail with missing arguments or use documented defaults.
- Keep `--json`, `--yes`, and `--no-input` for automation.

## 3. Under-Interactive Setup For Complex Config

Problem: A config-heavy tool expects users to manually edit files before first use.

Typical signs:

- Users do not know where config lives.
- Model/API setup fails silently.
- README has long setup prose but no command.

Solution:

- Add `setup` for guided configuration.
- Add `config show`, `config path`, `config reset`.
- Add `doctor` to verify credentials, paths, optional CLIs, and network.

## 4. Undefined Config Precedence

Problem: Flags, env vars, project config, and global config conflict.

Typical signs:

- Same command behaves differently across directories.
- Users cannot tell which config value was used.
- Tests patch environment variables unpredictably.

Solution:

- Document precedence: flags > env > project config > user config > defaults.
- Show effective config with masked secrets.
- Include config source in debug output.

Ruff-style lesson: support both config files and CLI overrides; make defaults useful but explicit.

## 5. Slow Help And Startup

Problem: Importing the CLI loads large libraries, probes network, or opens databases.

Typical signs:

- `my-cli --help` feels slow.
- Running help fails without credentials.
- Import side effects create files.

Solution:

- Lazy-load heavy modules inside command bodies.
- Never perform network or auth checks during import/help.
- Keep console/settings creation lightweight.

uv-style lesson: startup speed is part of UX.

## 6. Command Surface Sprawl

Problem: The CLI grows many overlapping commands.

Typical signs:

- `run`, `generate`, `create`, and `build` do similar things.
- Users rely on tribal knowledge.
- Help output becomes a wall of commands.

Solution:

- Group commands by resource or action.
- Keep aliases rare and documented.
- Deprecate old commands with clear warnings.
- Add command examples in help text.

## 7. Pretty Output Without Machine Output

Problem: Rich tables look good but cannot be consumed by scripts.

Typical signs:

- Users scrape terminal text.
- Color codes leak into pipes.
- CI logs are noisy.

Solution:

- Add `--json` or `--format`.
- Disable Rich markup for machine output.
- Respect `NO_COLOR`, `--no-color`, `--quiet`.

HTTPie-style lesson: human output can be beautiful, but syntax and output must remain predictable.

## 8. Weak Error Messages

Problem: Errors say "failed" without a next action.

Typical signs:

- Raw tracebacks in normal mode.
- No distinction between config, network, auth, and data failures.
- Users retry blindly.

Solution:

- Define domain errors.
- Include likely cause and repair command.
- Show traceback only with `--debug`.

Better:

```text
配置无效：model 缺失。
建议：运行 my-cli setup model 或 my-cli config set model <name>。
```

## 9. Bad Exit Codes

Problem: The CLI always exits 0 or 1.

Typical signs:

- CI cannot distinguish "issues found" from "tool crashed".
- Shell scripts need text matching.

Solution:

- Define exit code contracts.
- Use separate codes for usage/config errors, found violations, auth, network, and internal bugs.
- Document them.

## 10. Cache Semantics Are Invisible

Problem: Users cannot tell whether output is fresh.

Typical signs:

- `refresh` returns the same items.
- Failed requests are cached as empty results.
- Cache cannot be inspected or cleared.

Solution:

- Store cache status: `ok`, `empty-valid`, `partial`, `error`.
- Include source, query, time window, schema version, and cache age in metadata.
- Provide `cache stats`, `cache clear`, and `--refresh`.

uv-style lesson: cache is a product feature and should be deterministic, efficient, and inspectable.

## 11. Data Claims Without Evidence

Problem: A research/data CLI reports conclusions without source objects.

Typical signs:

- No URL, timestamp, metric, or query is retained.
- LLM synthesis is mixed with facts.

Solution:

- Preserve evidence objects.
- Separate facts, inference, and recommendation.
- Save evidence beside generated reports.

## 12. LLM Provider Configuration Collapsed Into One Field

Problem: The CLI asks only for an API key.

Typical signs:

- OpenAI-compatible providers fail.
- Wrong base URL or model name returns empty content.
- Instructor/tool mode works for one provider but not another.

Solution:

- Store provider, base URL, model, API key reference, timeout, and response mode separately.
- Verify with the actual configured model.
- Probe capabilities: plain chat, JSON mode, tool/instructor mode.

## 13. Monolithic CLI Module

Problem: `cli.py` contains routing, prompts, SQL, HTTP, rendering, and business rules.

Typical signs:

- Unit tests require huge mocks.
- Adding one command breaks another.
- Prompt copy is hard to review.

Solution:

- Keep `cli.py` thin.
- Move workflows to `app/`.
- Move external calls to `services/`.
- Move output to `renderers/`.
- Move config to `settings.py` or `config.py`.

## 14. No Project Root Or File Discovery Policy

Problem: Configuration and file targets are discovered inconsistently.

Typical signs:

- Running from a subdirectory changes behavior.
- Hidden directories are scanned.
- Large repos become slow.

Solution:

- Define root discovery.
- Respect `.gitignore` or documented include/exclude rules when relevant.
- Provide `--config`, `--isolated`, and `--exclude`.

Ruff-style lesson: file discovery and defaults are core CLI behavior.

## 15. Packaging Entry Point Drift

Problem: README says one command, installed package provides another.

Typical signs:

- `pip install` succeeds, command not found.
- Users must manually create symlinks.

Solution:

- Test `[project.scripts]`.
- Verify clean venv install.
- Keep README examples synchronized with real commands.

## 16. Secrets In Logs, Docs, Or Git History

Problem: Tokens or release setup details leak into public files.

Typical signs:

- `config show` prints full keys.
- README contains operational credentials or sensitive setup values.
- Remote URL contains a token.

Solution:

- Mask secrets.
- Keep release credentials and private operational details out of public docs.
- Scan before publishing.
- Prefer trusted publishing or secret managers without documenting sensitive internals publicly.

## 17. Tests Skip The Real CLI

Problem: Tests cover functions but not the installed command.

Typical signs:

- Parser regressions ship.
- Entry points break.
- JSON mode is invalid.

Solution:

- Test `--help`.
- Test each top-level command help.
- Test clean install in CI when feasible.
- Test JSON output with `json.loads`.
- Test representative success and failure paths.

## 18. No Maintenance Story

Problem: The CLI works today but cannot evolve safely.

Typical signs:

- No changelog.
- No deprecation policy.
- Config schema changes break users.
- Plugins have no version contract.

Solution:

- Add `CHANGELOG.md`.
- Version config schemas.
- Warn before removing commands/options.
- Keep migration helpers for user state.

## 19. Diagnostics Are Human-Only Or Mutate State

Problem: `doctor` prints friendly prose but cannot be parsed by scripts, or it changes user files while diagnosing.

Typical signs:

- Support cannot ask for one safe JSON diagnostic output.
- `doctor` creates config/cache/shims unless users opt in.
- Health checks hide cache availability or config source.

Solution:

- Add `doctor --json`.
- Keep default doctor read-only.
- Put repair behind explicit flags such as `--fix-entrypoint`.
- Include command path, Python executable, config path, model/provider, cache path, cache status, optional CLI status, and auth status.
- Mask all secrets.

## 20. Release Copy Drift

Problem: A local skill/template and its published package copy diverge.

Typical signs:

- The package contains stale docs or missing reference files.
- Copying a directory into an existing directory creates nested duplicate folders.
- GitHub and local behavior differ.

Solution:

- Treat the published copy as a build artifact or sync target.
- Use explicit file sync, clean destination directories, or package-data tests.
- Run `diff -qr` between source and release copy before publishing.
- Inspect wheel/sdist contents for required assets.
