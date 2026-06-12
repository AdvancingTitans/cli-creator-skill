# CLI Creation Playbook

Use this playbook to build a modern Python CLI that is friendly for first-time users, scriptable for power users, and maintainable for future contributors.

## Phase 0: Product Framing

Define:

- Target user: who uses this CLI and in what context?
- Job to be done: what useful artifact or decision should the CLI produce?
- First-run success: what can a user achieve within five minutes?
- Repeat-run success: what should the CLI remember or automate?
- Failure model: what can fail, and how should the CLI recover?

Write a one-paragraph product promise before writing code.

## Phase 1: Command Surface

Keep v1 small:

```text
my-cli run                 # main interactive flow
my-cli setup               # guided first-run setup
my-cli config show         # inspect config safely
my-cli config set          # update config
my-cli config reset        # reset config
my-cli doctor              # diagnose environment
```

Add optional commands only when they expose real user value:

```text
my-cli profile show
my-cli profile clear
my-cli cache clear
my-cli history list
my-cli export
```

Rules:

- Prefer verbs users understand.
- Keep aliases only when they reduce friction.
- Ensure every interactive prompt has an equivalent flag for automation.

## Phase 2: Project Bootstrap

Recommended tooling:

- `uv` for project and lock management when available.
- `src/` layout to prevent import confusion.
- `pytest` for tests.
- `ruff` for linting and formatting.
- `typer`, `rich`, `questionary`, `pydantic`, `pydantic-settings`, `python-dotenv`, `httpx`, `litellm`, `instructor`.

Minimal `pyproject.toml` shape:

```toml
[project]
name = "my-cli"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "typer>=0.12",
  "rich>=13",
  "questionary>=2",
  "pydantic>=2",
  "pydantic-settings>=2",
  "python-dotenv>=1",
  "httpx>=0.27",
]

[project.scripts]
my-cli = "my_cli.cli:main"
```

## Phase 3: Domain Models

Define Pydantic models before implementing long flows.

Common models:

- `UserProfile`: background, goals, resources, constraints, risk preference, output preference, updated_at, confidence.
- `ConversationState`: current stage, known facts, pending question, rejected items, shown candidates.
- `EvidenceItem`: source, title, url, published_at, metric, snippet, reliability.
- `Candidate`: title, summary, evidence, scores, novelty, user_fit.
- `Brief`: final structured artifact.
- `ModelConfig`: provider, base_url, model, api_key_ref, mode, timeout.
- `CacheEntry`: key, status, payload, created_at, expires_at, error_summary.

Keep fields explicit enough that invalid LLM output fails early.

## Phase 4: Interaction Design

For multi-turn assistant CLIs:

1. Ask one open question.
2. Interpret intent.
3. Ask the next most useful missing question.
4. Summarize the profile.
5. Confirm or let the user correct.
6. Fetch evidence.
7. Show a ranked table.
8. Allow selection, refresh, refinement, or free-text challenge.
9. Generate an output file.
10. Offer delivery or next analysis.

State machine fields:

```python
class Stage(str, Enum):
    EXPLORE = "explore"
    PROFILE = "profile"
    SCAN = "scan"
    REFINE = "refine"
    OUTPUT = "output"
```

Do not hard-code long question chains. Decide the next prompt from missing fields and the user's latest answer.

## Phase 5: Persistence And Cache

Use SQLite for:

- Query cache.
- Evidence cache.
- LLM structured output cache.
- User profile memory.
- Run history.

Cache key should include:

- Normalized query.
- Time window.
- Source or provider.
- Filters.
- Schema version.

Cache entry should include:

- Status.
- Created time.
- Expiry time.
- Payload hash.
- Error summary for failed calls.

Commands:

```text
my-cli cache stats
my-cli cache clear
my-cli profile show
my-cli profile clear
```

Do not cache failed empty results as valid recommendations.

## Phase 6: LLM Integration

Support model providers through a normalized client:

- OpenAI.
- Anthropic.
- OpenAI-compatible providers.
- Ark or other provider-specific endpoints.
- Local Ollama when useful.

Configuration rules:

- Provider, base URL, model name, and API key must be separate.
- Presets should help, not hide fields.
- Verification must call the configured model.
- Store capability probes: plain chat, JSON mode, instructor/tool mode.

Structured output strategy:

1. Try instructor with provider-compatible mode.
2. Fall back to JSON mode.
3. Fall back to plain text with strict JSON extraction.
4. Validate with Pydantic.
5. Retry once with validation errors summarized.
6. Fail clearly with a diagnostic command.

## Phase 7: External Integrations

Use adapter interfaces:

```python
class DeliveryChannel(Protocol):
    name: str
    def is_configured(self) -> bool: ...
    def verify(self) -> VerificationResult: ...
    def send_file(self, file_path: Path, message: str) -> DeliveryResult: ...
```

Keep integration-specific auth, CLI calls, and error mapping inside adapters.

For Feishu/Lark:

- Detect whether `lark-cli` exists.
- Check `auth status` for user or bot.
- Check configured chat ID.
- Guide users to install/auth only when missing.
- Do not block report generation if delivery is not configured.

## Phase 8: Error Handling

Define user-facing exceptions:

- `ConfigError`
- `ModelVerificationError`
- `DataFetchError`
- `CacheError`
- `DeliveryError`
- `UserCancelled`

Each error should include:

- Message.
- Likely cause.
- Suggested command.
- Whether retry is safe.

Show tracebacks only with `--debug`.

## Phase 9: Testing

Minimum tests:

- Import package.
- Run `--help`.
- Run every command's `--help`.
- Load default settings with temp home.
- Save, show, and clear profile.
- Cache hit, miss, refresh, and expired behavior.
- Model config validation without real network.
- One offline smoke flow using fixture evidence.

Useful commands:

```bash
python -m pytest
python -m my_cli --help
my-cli doctor --json
```

## Phase 10: Documentation And Release

README must include:

- What the CLI is for.
- Install command.
- First-run setup.
- Main workflow with screenshots or terminal examples.
- Model provider configuration examples.
- Config paths.
- Troubleshooting.
- Extension guide.

Release checklist:

- Clean venv install works.
- Console script name matches README.
- `--help` works without config.
- Package metadata includes Python version.
- No secrets in repo.
- PyPI page renders README.
