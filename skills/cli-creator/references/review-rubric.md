# CLI Review Rubric

Use this rubric to audit an existing CLI. Score each category from 0 to 3 and mark urgent issues as P0/P1/P2.

## Scoring

- 0: Missing or actively harmful.
- 1: Present but fragile or confusing.
- 2: Mostly solid with clear improvement areas.
- 3: Strong, tested, and user-friendly.

## Severity

- P0: Prevents normal use, risks data loss, leaks secrets, or breaks installation.
- P1: Major UX, correctness, reliability, or maintainability issue.
- P2: Improvement that reduces friction or future risk.

## 1. Command Surface And First Run

Check:

- Does the installed command match the README?
- Does `--help` work before config exists?
- Is there a guided `setup`?
- Is the main command obvious?
- Are expert flags available for automation?

Red flags:

- Command not found after successful install.
- First run immediately fails on missing config.
- Users must read source code to configure providers.

## 2. Interactive UX

Check:

- Does the CLI ask one natural question at a time?
- Does it support free text, correction, refresh, and cancel?
- Does refresh produce genuinely new options?
- Does it avoid repeating questions?
- Does it summarize before committing to a recommendation?

Red flags:

- Menus expose internal architecture.
- All choices lead to the same output.
- Profile collection feels like a form.

## 3. Architecture And Modularity

Check:

- Is `cli.py` thin?
- Are flows, services, LLM, persistence, rendering, and integrations separated?
- Are Pydantic models used for structured data?
- Can integrations be added without editing core flows?

Red flags:

- One large file owns everything.
- Prompt strings, SQL, Rich rendering, and HTTP calls are mixed.

## 4. Configuration And Secrets

Check:

- Are provider, base URL, model, and API key represented separately?
- Are secrets masked in `config show`?
- Are config paths documented?
- Can users reset config safely?

Red flags:

- Full API keys printed to terminal.
- Provider setup silently falls back to a wrong default.

## 5. LLM Integration

Check:

- Is configuration verified with the actual model?
- Are provider compatibility differences handled?
- Is structured output validated?
- Is there a fallback when instructor/tool mode is unsupported?
- Are validation errors retried or explained?

Red flags:

- Empty user-facing results hide model failures.
- All OpenAI-compatible providers are treated as identical.

## 6. Data Fetching And Evidence

Check:

- Are recommendations grounded in source objects?
- Are source URLs, dates, and metrics preserved?
- Are fetch failures distinguishable from no results?
- Are rate limits and timeouts handled?

Red flags:

- "Hot" topics have no evidence.
- Social buzz is treated as fact without corroboration.

## 7. Cache And Persistence

Check:

- Is cache keyed by query, window, source, filters, and schema version?
- Are failed calls excluded from normal cache hits?
- Can users clear cache?
- Is profile memory separate from fetch cache?

Red flags:

- Refresh returns identical cached results.
- Empty failures are cached as valid.
- No clear profile command.

## 8. Error Handling

Check:

- Are errors actionable?
- Is `--debug` available?
- Are likely causes and suggested commands shown?
- Are cancellations graceful?

Red flags:

- Raw tracebacks in normal mode.
- Generic "failed" messages.

## 9. Performance

Check:

- Is startup fast?
- Are heavy imports lazy?
- Are network calls bounded by timeouts?
- Are progress indicators used for slow operations?

Red flags:

- `--help` imports LLM/browser modules or probes network.
- No timeout on HTTP calls.

## 10. Testing

Check:

- Are help commands tested?
- Is first-run empty config tested?
- Are cache and profile operations tested?
- Is there an offline smoke flow?
- Is package metadata/entry point tested?

Red flags:

- Only utility functions are tested.
- No installed-command test.

## 11. Documentation

Check:

- Does README explain the product promise?
- Are install, setup, run, config, doctor, and troubleshooting documented?
- Are model provider examples included?
- Are extension points documented?

Red flags:

- README examples do not match real commands.
- No explanation of required model fields.

## 12. Release And Maintenance

Check:

- Is Python version realistic for target users?
- Are optional integrations optional dependencies?
- Is release automation documented?
- Are migrations handled for SQLite/config schema?

Red flags:

- Package requires a Python version unavailable on target machines without guidance.
- Breaking config changes lack migrations.

## Audit Output Format

Use this format:

```markdown
**Findings**

- [P0] Installed command does not match README
  - Evidence: `pyproject.toml` defines `x`, README says `y`.
  - Impact: users cannot start the CLI after install.
  - Fix: change `[project.scripts]` or README and test clean install.

**Scores**

| Area | Score | Notes |
|---|---:|---|
| First run | 1/3 | Missing setup |
| LLM config | 0/3 | Provider/base_url/model collapsed |

**Recommended Repair Order**

1. Fix entry point and first-run help.
2. Add model setup verification.
3. Separate cache failures from empty results.
```
