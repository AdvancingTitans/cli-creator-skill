# Output Eval Scorecard

- Status: PASS

- [PASS] `trigger-eval:cases` — found 3 trigger eval case(s)
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:positive-cli-design` — positive prompt expected True, got True
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:negative-email` — negative prompt expected False, got False
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:edge-skill-audit` — edge prompt expected True, got True
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:coverage:positive` — positive trigger coverage present
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:coverage:negative` — negative trigger coverage present
  - Evidence: evals/trigger_cases.json
- [PASS] `trigger-eval:coverage:edge` — edge trigger coverage present
  - Evidence: evals/trigger_cases.json
- [PASS] `output-eval:min-cases` — found 3 valid output eval case(s)
  - Evidence: evals/output_cases.json
- [PASS] `output-eval:required-sections-shape` — minimum output sections match required review headings
  - Evidence: evals/output_cases.json
- [PASS] `output-eval:audit-review-complete` — all required sections present
  - Evidence: evals/output_cases.json
- [PASS] `output-eval:new-cli-design-complete` — all required sections present
  - Evidence: evals/output_cases.json
- [PASS] `output-eval:skill-template-audit-complete` — all required sections present
  - Evidence: evals/output_cases.json
