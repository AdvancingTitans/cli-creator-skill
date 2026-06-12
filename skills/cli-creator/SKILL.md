---
name: cli-creator
description: Use when designing, scaffolding, refactoring, or auditing a Python CLI tool, especially Typer + Rich + questionary CLIs with interactive flows, data fetching, caching, LLM integration, structured output, local memory, and multi-channel delivery.
---

# CLI Creator

Use this skill to create a high-quality CLI from zero, or to review an existing CLI and produce actionable fixes. Prefer it for interactive, data-driven, LLM-assisted, multi-turn command line products.

## Trigger Conditions

Use this skill when the user asks to:

- Create a Python CLI, command line app, interactive assistant, research assistant, data tool, or automation CLI.
- Improve a CLI's UX, command surface, onboarding, config flow, model setup, caching, or release process.
- Audit an existing CLI for maintainability, reliability, packaging, PyPI installability, or user experience.
- Add Typer, Rich, questionary, litellm, instructor, Pydantic, SQLite, config, profile memory, or provider setup to a CLI.
- Diagnose symptoms such as "command not found", "model returns empty", "refresh shows same results", "users do not know how to configure", "interactive flow feels rigid", or "report quality is shallow".

## Core Philosophy

Build the CLI as a product, not as a thin script.

1. Start from the user's job, not the command list. The first screen must help users decide what to do next.
2. Separate command routing, conversation flow, data access, LLM reasoning, persistence, and delivery channels.
3. Make every external dependency visible and diagnosable: model provider, base URL, model name, auth state, cache age, and output path.
4. Prefer progressive interaction. Ask one natural question at a time, summarize what you learned, and allow correction.
5. Ground data-driven recommendations in evidence. Show source, time window, freshness, and confidence.
6. Treat local memory as a user-controlled feature. Provide inspect, update, export, and clear commands.
7. Optimize for recovery. Every error should explain what happened, why it likely happened, and what command fixes it.

Balance UX and functionality by making the default path friendly and the expert path scriptable. Interactive commands should guide; non-interactive flags should reproduce the same workflow for automation.

## First Response Pattern

When starting a CLI creation task:

1. Restate the target user, core workflow, and delivery format in one short paragraph.
2. Identify whether this is a new CLI, a refactor, or an audit.
3. Inspect the repository before proposing architecture when code already exists.
4. Create or update files directly unless the user explicitly asks for a plan only.
5. Verify the installed command, the help output, and at least one end-to-end smoke path.

When starting a CLI review task:

1. Run a quick structure scan: `rg --files`, `pyproject.toml`, entry points, package layout, tests, README.
2. Run the CLI help and one representative command when safe.
3. Report findings by severity first, with file and line references.
4. Suggest fixes that preserve the existing architecture unless the structure itself is the problem.

## Creation Workflow

Follow this workflow for a new CLI.

### 1. Define The Product Surface

Clarify:

- Primary job: what valuable outcome should the user get in one session?
- First-run path: what does a brand-new user see before any config exists?
- Expert path: what command can be scripted in CI, cron, or automations?
- State model: what is ephemeral, cached, remembered, or user-owned?
- External integrations: models, APIs, browser tools, Feishu/Lark, GitHub, file outputs.

Design no more than 5 top-level commands for v1. Prefer:

- `run` for the main interactive flow.
- `setup` for guided first-run configuration.
- `config` for inspect/update/reset.
- `doctor` for diagnostics and auto-fixes.
- `history` or `profile` only when persistent memory is a core feature.

### 2. Choose The Stack

Use this default stack unless the repo has a strong existing convention:

- Typer for command routing, type hints, and shell completion.
- Rich for panels, tables, markdown rendering, progress, and friendly errors.
- questionary for interactive prompts, with non-TTY fallbacks.
- Pydantic v2 for domain models and validation.
- pydantic-settings plus `.env` for config.
- SQLite for cache, history, and user profile memory.
- httpx for HTTP clients with timeouts, retries, and clear user-agent.
- litellm for multi-provider model calls.
- instructor for structured LLM output when compatible; provide a JSON-schema fallback.

### 3. Design Modules Before Files

Keep these boundaries:

- `cli`: parse commands and flags only.
- `app` or `flows`: orchestrate user journeys.
- `models`: define Pydantic request, result, profile, and report schemas.
- `settings`: load env/config and validate provider setup.
- `store`: own SQLite schema, cache, history, and profile memory.
- `services`: fetch data from external sources.
- `llm`: call models and normalize structured output.
- `renderers`: terminal, markdown, JSON, or file rendering.
- `integrations`: Feishu/Lark, DingTalk, WeChat, GitHub, email, etc.

Do not let prompt strings, HTTP calls, database SQL, and Rich tables live in the same module.

### 4. Build The Interaction Loop

For conversational CLIs, model the flow as stages:

1. Explore intent with one open question.
2. Build a lightweight user profile through natural conversation.
3. Run data-driven opportunity scanning.
4. Rank and refine options with the user.
5. Generate a durable output artifact.
6. Offer one useful next action.

Use state objects, not scattered booleans. Track:

- Current stage.
- User goal and constraints.
- Known profile fields and confidence.
- Evidence queries already used.
- Candidate items already shown.
- User rejections and "do not ask again" preferences.

### 5. Make Data And LLMs Observable

For every model-backed or web-backed recommendation, preserve:

- Query text.
- Time window.
- Source name and URL.
- Fetch timestamp.
- Cache key and cache age.
- Model provider, base URL, model name, and response mode.
- Structured validation errors.

Show concise evidence to the user, and save full evidence beside generated artifacts.

### 6. Ship The CLI As An Installable Product

Ensure:

- `pyproject.toml` defines a `console_scripts` entry point.
- The command name users type is the command that gets installed.
- `--help` works before config exists.
- `setup` guides users through provider, base URL, model name, API key, and verification.
- `doctor` detects stale entry points, Python version mismatch, missing optional tools, auth state, and config mistakes.
- README includes install, first run, config, examples, troubleshooting, and extension points.

## Review Workflow

Audit an existing CLI with this order:

1. Inspect package metadata, command entry points, Python version, dependencies, and README.
2. Run `--help`, `setup --help`, `config --help`, and the main command help.
3. Trace the main flow from CLI command to app orchestration, services, LLM, persistence, rendering, and output.
4. Check first-run behavior with no config.
5. Check invalid config behavior, especially model provider/base URL/model name/API key combinations.
6. Check cache refresh semantics and whether "refresh" can repeat stale results.
7. Check non-TTY behavior and scriptability.
8. Check tests for entry point, config, cache, LLM fallback, and smoke flows.
9. Score with `references/review-rubric.md`.
10. Return findings first, then a prioritized repair plan.

## Pitfalls To Watch

Before implementing or reviewing, read `references/pitfalls-and-solutions.md` when the task involves:

- Interactive flows.
- LLM provider setup.
- Data caching or refresh.
- Profile memory.
- Packaging and PyPI entry points.
- Feishu/Lark or other delivery channels.

High-frequency pitfalls include:

- Asking form-like questions instead of having a natural conversation.
- Hiding required model settings behind a single API key prompt.
- Treating OpenAI-compatible endpoints as interchangeable without checking path, model name, and response schema.
- Returning empty lists when the real problem is model/config failure.
- Letting refresh reuse identical cache keys.
- Saving user profile memory without inspect and clear commands.
- Publishing a package whose installed command differs from README examples.

## Project Structure Template

Use or adapt this structure:

```text
my-cli/
  pyproject.toml
  README.md
  .env.example
  src/my_cli/
    __init__.py
    __main__.py
    cli.py
    app.py
    console.py
    errors.py
    models.py
    settings.py
    store.py
    prompts.py
    renderers/
      __init__.py
      terminal.py
      markdown.py
      json.py
    services/
      __init__.py
      evidence.py
      search.py
    llm/
      __init__.py
      client.py
      schemas.py
    integrations/
      __init__.py
      base.py
      lark.py
      dingtalk.py
      wechat.py
  tests/
    test_cli_help.py
    test_config.py
    test_store.py
    test_flow_smoke.py
```

Read `references/creation-playbook.md` for a fuller scaffold and implementation sequence.

## Interactive Design Rules

Use these rules for conversational or assistant-like CLIs:

- Ask one question at a time.
- Make each question sound like a helpful collaborator, not an application form.
- Stop asking when enough signal exists; use defaults and say they can be changed later.
- Never repeat a question whose semantic field was already answered.
- Summarize the profile before using it for recommendations.
- Accept natural language commands such as "换一个方向", "再细一点", "这个太难", "保守一点", "直接生成".
- Treat refresh as a new search intent with exclusions from previously shown candidates.
- Always let the user inspect and clear remembered profile data.

For profile-building flows, internally collect background, goal, resources, constraints, risk preference, and output preference, but phrase questions naturally:

- "先聊聊你的背景吧，你之前主要在哪些方向做过研究、写作或项目？"
- "这次你更想得到什么结果？发论文、写长文、系统学习、职业准备，还是单纯好奇？"
- "你有没有别人不太容易有的视角、经历或资源？"
- "有没有什么方向你明确不想碰，或者现在比较顾虑？"

## LLM Integration Rules

When adding model support:

1. Require provider, base URL, model name, and API key as separate visible fields when using OpenAI-compatible third-party providers.
2. Provide presets for common providers, but let users override every field.
3. Verify configuration with a small structured-output call.
4. Detect and explain common failures: wrong endpoint path, unsupported JSON schema, invalid model name, expired key, proxy issue, timeout, and content filter.
5. Fall back from instructor tool/function mode to JSON mode or plain JSON parsing when provider compatibility is partial.
6. Cache only successful data fetches and validated LLM outputs. Do not cache empty results from failed calls as if they were valid.

## Output Standards

For a new CLI task, deliver:

- Project structure.
- Core Pydantic models.
- Main commands and help text.
- First-run setup flow.
- End-to-end smoke command.
- README updates.
- Known limitations and next steps.

For a review task, deliver:

- Findings ordered by severity.
- File and line references.
- Reproduction steps.
- Recommended fixes.
- Test gaps.
- A short implementation plan if changes are requested.

## References

- Read `references/pitfalls-and-solutions.md` for common failure modes and repairs.
- Read `references/creation-playbook.md` for the full build sequence.
- Read `references/review-rubric.md` for scoring and audit format.
