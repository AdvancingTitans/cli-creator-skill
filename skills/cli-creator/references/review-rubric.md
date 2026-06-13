# CLI Audit Checklist

Use this checklist to review an existing CLI. Score each area from 0 to 3 and mark findings as P0/P1/P2.

## Scoring

- 0: missing or harmful
- 1: present but fragile
- 2: usable with clear improvements
- 3: strong and tested

## Severity

- P0: install broken, data loss, secret leak, or core command unusable
- P1: major correctness, UX, performance, or maintainability risk
- P2: improvement that reduces friction or future risk

## 1. Product And Command Surface

Check:

- Does the CLI have a clear product promise?
- Are commands named after user intent?
- Is help concise and example-driven?
- Are mutating commands obvious?
- Are global flags consistent?

Red flags:

- internal mode names
- overlapping commands
- README command differs from installed command

## 2. First Run And Setup

Check:

- Does `--help` work without config?
- Is there a setup/init path when config is required?
- Are missing dependencies diagnosed?
- Can users recover from invalid config?

Red flags:

- first run crashes
- setup hidden in docs only
- no `doctor` for complex tools

## 3. Configuration

Check:

- Is precedence documented?
- Are config paths discoverable?
- Are secrets masked?
- Are env vars and project config handled deliberately?

Red flags:

- conflicting config sources
- full API keys printed
- provider/model/base URL collapsed into one field

## 4. Architecture

Check:

- Is CLI routing thin?
- Are services, renderers, settings, and domain logic separated?
- Are models typed?
- Are integrations behind adapters?

Red flags:

- monolithic `cli.py`
- SQL/HTTP/Rich/prompt text mixed together

## 5. Output And UX

Check:

- Is human output readable?
- Is JSON/plain output available for automation?
- Are colors disabled when needed?
- Are progress indicators honest?

Red flags:

- scripts must scrape Rich tables
- color codes in JSON
- long operations appear frozen

## 6. Error Handling And Exit Codes

Check:

- Are errors actionable?
- Are exit codes meaningful?
- Is `--debug` available?
- Are cancellations graceful?

Red flags:

- raw tracebacks in normal mode
- every failure exits 1 with no hint

## 7. Performance

Check:

- Is `--help` fast?
- Are heavy imports lazy?
- Are network calls timed out?
- Are large inputs streamed or chunked?
- Is cache useful and explainable?

Red flags:

- network probes during import
- no timeout
- cache hides stale or failed data

## 8. Data And LLM Correctness

Check:

- Are claims backed by source objects?
- Are LLM outputs validated?
- Are provider capabilities verified?
- Are facts separated from inference?

Red flags:

- empty output hides model failure
- no evidence retention
- unsupported provider mode silently used

## 9. Packaging And Distribution

Check:

- Does `[project.scripts]` match README?
- Does clean venv install work?
- Is Python version realistic?
- Are optional dependencies optional?
- Does wheel include required assets?
- Is release-copy sync verified when publishing bundled skills, templates, or generated resources?

Red flags:

- command not found after install
- package data missing from wheel
- public docs include sensitive release setup details

## 10. Tests And CI

Check:

- Help commands tested?
- Config precedence tested?
- JSON output tested?
- Error paths tested?
- Smoke test uses installed command?
- Package data tested in wheel/sdist?

Red flags:

- only pure functions tested
- no package build test
- required assets missing from package tests

## 11. Documentation

Check:

- 30-second demo
- install commands
- config examples
- troubleshooting
- output schema
- extension docs if plugin-based

Red flags:

- docs describe architecture but not use
- examples are stale

## 12. Maintenance

Check:

- changelog
- deprecation policy
- config migrations
- plugin API versioning
- security policy for credentials

Red flags:

- breaking changes with no migration
- user state format has no version

## Audit Output Template

```markdown
**Findings**

- [P1] `--help` imports network providers and fails without credentials
  - Evidence: `src/my_cli/cli.py:12`
  - Impact: first-run UX and shell completion break.
  - Fix: lazy-load provider client inside command body.

**Scores**

| Area | Score | Notes |
|---|---:|---|
| Command surface | 2/3 | Good verbs, missing examples |
| Config | 1/3 | No documented precedence |
| Packaging | 0/3 | README command does not install |

**Repair Order**

1. Fix install/entry point.
2. Make help work without config.
3. Add config precedence and doctor.
4. Add JSON mode and smoke tests.
```
