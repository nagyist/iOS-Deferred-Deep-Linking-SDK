# L1 wire-validation scripts

`validate_l1_logs.py` is the Layer-1 PR gate that asserts the iOS SDK is
putting the right device/SDK fields on the wire. It is run by
`.github/workflows/layer1-logger-tests.yml` against a `branchlogs.txt`
produced by the L1 instrumented test, and can be run locally against any
captured log.

## Running locally

After capturing a `branchlogs.txt` (from a CI artifact, or by running
`scripts/run_l1_instrumented.sh` against a local simulator), point the
validator at it:

```bash
python3 scripts/validate_l1_logs.py path/to/branchlogs.txt
```

To run the validator's own test suite:

```bash
python3 -m unittest scripts.test_validate_l1_logs -v
```

The tests use fixtures in `scripts/fixtures/` and exercise: the happy
path, a missing-field failure, the v2-`user_data` nested shape (iOS
nests device fields under `user_data` on `/v2/event/*`), and the
install-must-be-captured guard.

## What gets validated

Presence-only. A required field is either there (pass) or absent (fail).
No type checks, no value-format checks — those are intentionally left to
the backend ingestion gate.

The required field list lives at the top of `validate_l1_logs.py`:

- `REQUIRED_COMMON` — fields the SDK must put on every `/v1/*` request.
- `REQUIRED_PER_ENDPOINT` — additional fields per endpoint (e.g.
  `is_hardware_id_real` and `first_install_time` on `/v1/install`).

Lookups tolerate `user_data` nesting so `/v2/event/*` payloads (where iOS
moves device fields under `user_data`) still validate using the same code
path.

## What gets printed on success

For every captured request: the full payload (with sensitive values
masked) plus a per-field check table showing the actual value that went
over the wire. This is the answer to the reviewer feedback on PR #1590 —
silent passes are no longer possible because every field's value is
visible in the CI log.

## Adding a new required field

1. Add the field name to `REQUIRED_COMMON` (every request) or
   `REQUIRED_PER_ENDPOINT[<path>]` (endpoint-scoped).
2. If the field carries a secret/PII, add it to `SENSITIVE_FIELDS` so the
   value is masked in both the per-field table and the full-payload dump.
3. Add a fixture to `scripts/fixtures/` and a test in
   `scripts/test_validate_l1_logs.py` covering the missing-field case.
4. Update the sanitization step in
   `.github/workflows/layer1-logger-tests.yml` so the value is also
   stripped from any uploaded artifact.

## Platform parity

The Android sibling validator lives in
`android-branch-deep-linking-attribution` and uses the same architecture
with two extra fields (`wifi` and `ui_mode`) that iOS does not emit on the
wire. Cross-platform alignment of those device-context fields is tracked
under the v4 Conversion API workstream, not this gate.
