# CLI Pitfalls And Solutions

Use this reference when creating or auditing a Python CLI, especially an interactive Typer + Rich + questionary application with data fetching, LLM integration, and local persistence.

## 1. Menu-First Design

Problem: The CLI opens with a rigid menu instead of helping the user express intent.

Typical signs:

- The first prompt asks users to choose between internal implementation modes.
- Users who do not know the domain cannot proceed confidently.
- Every branch produces similar results, so choices feel fake.

Solution:

- Start with a plain-language question about the user's goal.
- Offer 2-4 examples, but always allow free text.
- Route free text through intent detection, not a generic default branch.

Anti-pattern:

```text
? Choose mode: [Domain mode, Autonomous mode, Config mode]
```

Better:

```text
? 你最近想研究什么？可以说一个领域，也可以说“我没思路，帮我找机会”。
```

## 2. Questionnaire-Like Profile Collection

Problem: The CLI asks a stack of formal questions and makes the user feel they are filling out a grant application.

Typical signs:

- Five or more questions are shown at once.
- Questions use abstract labels such as "风险偏好" or "输出形式偏好".
- The CLI repeats similar questions after the user already answered.

Solution:

- Ask one natural question at a time.
- Maintain a profile state with field confidence.
- Infer missing fields when confidence is good enough.
- Allow "没有", "不知道", "跳过", and continue with defaults.

Better:

```text
先聊聊你的背景吧，你之前主要在哪些方向做过研究、写作或项目？
```

## 3. No Persistent Profile Memory

Problem: The CLI asks the same background questions every run.

Typical signs:

- Returning users must re-enter goals and constraints.
- There is no command to inspect or clear memory.
- Profile data is mixed with cache data.

Solution:

- Store profile memory in SQLite or a dedicated config file.
- Provide `profile show`, `profile edit`, and `profile clear`.
- Store timestamps and confidence per field.
- Ask only for missing or stale information.

## 4. Hidden Model Configuration

Problem: The CLI asks only for an API key, but the provider also requires provider name, base URL, and model name.

Typical signs:

- OpenAI-compatible providers fail silently.
- Users paste a base URL such as an Ark endpoint but the CLI still calls the OpenAI default.
- Empty recommendations appear when the real cause is model failure.

Solution:

- Treat provider, base URL, model, API key, timeout, and structured-output mode as explicit settings.
- Provide presets, then verify with a small call.
- Display the active provider summary before expensive workflows.

Better commands:

```bash
my-cli setup model
my-cli config model show
my-cli config model verify
my-cli config model presets
```

## 5. Provider Compatibility Assumptions

Problem: The CLI assumes all OpenAI-compatible endpoints support the same schema, tool calls, streaming, and JSON mode.

Typical signs:

- Instructor fails on one provider but works on another.
- `base_url` path is wrong, for example using a coding endpoint for chat completions.
- Model names require provider-specific IDs.

Solution:

- Implement provider presets with known base URL shape and model examples.
- Run a capability probe: plain chat, JSON mode, instructor/tool mode.
- Store capability flags and choose the safest response mode.
- Provide a manual override.

## 6. Caching Failed Or Empty Results

Problem: A failed fetch or bad LLM response is cached as a valid empty result.

Typical signs:

- Refresh still returns no results.
- The CLI says "no reliable topics" even after config is fixed.
- Cache has no status field.

Solution:

- Store cache entries with status: `ok`, `empty-valid`, `error`, `partial`.
- Do not reuse `error` cache entries unless explicitly requested.
- Include cache age and source in debug output.
- Provide `cache clear` and `run --refresh`.

## 7. Refresh Shows The Same Items

Problem: Refresh reuses the same query, same cache key, and same ranking without exclusions.

Typical signs:

- Users see identical suggestions across refreshes.
- The code only bypasses cache but does not alter the search strategy.

Solution:

- Track shown item IDs, titles, URLs, and embeddings or normalized titles.
- Add exclusions to ranking.
- Vary query expansions and time windows.
- Display "new since last batch" and "hidden duplicates" counts.

## 8. Evidence-Free Recommendations

Problem: The CLI generates attractive topic names without verifiable sources.

Typical signs:

- Tables have no source URLs.
- "Hot" means the model thinks it is hot.
- Social chatter is treated as equal to papers, policy, market data, or code activity.

Solution:

- Require evidence objects with source, URL, date, metric, and snippet.
- Rank topics using transparent dimensions.
- Mark unsupported claims as hypotheses.
- Refuse or ask to broaden search when evidence is insufficient.

## 9. Monolithic CLI Modules

Problem: `cli.py` contains command definitions, prompts, HTTP calls, SQL, prompt templates, and rendering.

Typical signs:

- Adding a new command risks breaking the main flow.
- Tests must mock too much.
- LLM prompts are hard to reuse.

Solution:

- Keep `cli.py` thin.
- Move orchestration to `app.py` or `flows/`.
- Move integrations to `services/` or `integrations/`.
- Move terminal output to `renderers/terminal.py`.

## 10. Poor Non-TTY Behavior

Problem: The CLI only works interactively and crashes in automation.

Typical signs:

- questionary prompts appear in cron, CI, or piped usage.
- No flags exist for required inputs.
- The command cannot run with `--yes`, `--json`, or config values.

Solution:

- Detect `sys.stdin.isatty()`.
- Provide flags for every required prompt.
- In non-TTY mode, fail with a clear missing-argument message or use defaults.
- Keep JSON output free of Rich styling.

## 11. Friendly UI But Weak Errors

Problem: The CLI looks polished but gives vague failure messages.

Typical signs:

- "执行失败" without cause.
- Stack traces shown to normal users.
- No suggested command fixes the issue.

Solution:

- Define domain errors with human messages and repair hints.
- Add `--debug` for tracebacks.
- Include next commands, for example `my-cli config model verify`.

Error format:

```text
模型验证失败：Ark 返回 404，通常是 base_url 路径或模型名不匹配。
建议：运行 my-cli setup model --provider ark，然后选择一个可用模型。
```

## 12. Packaging Entry Point Drift

Problem: README says `hotspot-research`, package installs `hotspot-research-cli`, or stale scripts remain on PATH.

Typical signs:

- `command not found` after successful install.
- Help text shows old command names.
- User must manually create symlinks.

Solution:

- Define the final command in `[project.scripts]`.
- Add a `doctor --fix-entrypoint` command only for legacy installs.
- Test install into a clean venv.
- Keep README examples generated or verified from real commands.

## 13. Secrets In Logs And Config

Problem: API keys, tokens, or bot credentials appear in logs, snapshots, or Git history.

Typical signs:

- Config show prints full API keys.
- Debug logs include headers.
- `.env` is committed.

Solution:

- Mask secrets by default.
- Store keys in OS keychain when available, or protected config files.
- Keep `.env.example`, never `.env`.
- Add pre-commit or CI secret scanning when feasible.

## 14. Slow Startup

Problem: Heavy imports, network probes, or model discovery happen before help output.

Typical signs:

- `my-cli --help` is slow.
- Importing the package triggers HTTP calls.
- Rich progress starts before command validation.

Solution:

- Keep top-level imports lightweight.
- Lazy-load LLM, browser, data, and rendering-heavy modules inside commands.
- Never probe network during import.

## 15. Missing Smoke Tests

Problem: Unit tests pass but the installed CLI is broken.

Typical signs:

- No test runs `python -m package --help`.
- No test checks `console_scripts`.
- No test covers first run with empty config.

Solution:

- Test `--help` for all top-level commands.
- Test config load with temp directories.
- Test one dry-run or offline smoke flow.
- Test package build metadata.

## 16. Integration Hard-Coding

Problem: The CLI directly calls one delivery channel or one model provider throughout the app.

Typical signs:

- Feishu logic is embedded in report generation.
- Adding DingTalk requires editing core flow code.
- Provider-specific exceptions leak into UI.

Solution:

- Define integration interfaces.
- Keep provider adapters small.
- Return normalized result objects.
- Let the main app depend on abstractions, not concrete CLIs.

## 17. No Diagnostics Command

Problem: Users cannot tell whether the failure is config, network, dependency, auth, or code.

Typical signs:

- Support requests include screenshots instead of diagnostic output.
- The README has long manual troubleshooting sections.

Solution:

- Implement `doctor`.
- Check Python version, package version, command path, config path, model provider, cache DB, optional CLIs, auth state, network reachability, and write permissions.
- Provide `doctor --json` for bug reports.
