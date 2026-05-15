"""
Validates Branch iOS SDK L1 wire payloads captured from branchlogs.txt.

Source of truth: the Branch-TestBed AppDelegate registers a
`BranchAdvancedLogCallback` (see Branch-TestBed/Branch-TestBed/AppDelegate.m,
lines 49-69). For every outbound request the callback emits a line of the
form:

    [BranchLog] Got <URL> Request: <jsonBody>

and for every response:

    [BranchLog] Got Response for request (<requestId>): <data>

The L1 instrumentation runs the TestBed under XCUITest, which causes Branch
to fire `/v1/install` (and on subsequent launches `/v1/open`). The AppDelegate
writes those lines into ~/Documents/branchlogs.txt via processLogMessage:.

This validator parses ONLY the "Got <URL> Request:" lines (request side) and
asserts the iOS SDK is sending what we expect on the wire. It is stdlib-only
and never logs payload contents (only field names) to avoid leaking secrets
into CI logs.

Key iOS field reference (Sources/BranchSDK/BNCRequestFactory.m):
  - branch_key        : line 490 - mandatory on every request
  - sdk               : line 502 - "ios<version>" on v1 endpoints,
                                    "ios" with separate sdk_version on v2
  - hardware_id       : present at Full attribution level
  - is_hardware_id_real : boolean, present at Full attribution level
  - first_install_time : numeric, /v1/install only

iOS differs from Android: Android uses a single `sdk` field that always
starts with "android"; iOS may emit `sdk = "ios<ver>"` (v1 endpoints) or
`sdk = "ios"` + `sdk_version = "<ver>"` (v2 endpoints). Both shapes are valid.
"""

import json
import os
import re
import sys
from urllib.parse import urlparse


# Pattern matches the AppDelegate's NSLog format for the request line.
# Example:
#   [BranchLog] Got https://api2.branch.io/v1/install Request: {"branch_key":"key_test_xxx","sdk":"ios3.14.0",...}
#
# Notes on robustness:
#   * Newlines may appear inside the JSON if NSLog re-wraps long strings,
#     so we do a non-greedy capture up to the next "[BranchLog] " marker or
#     EOF when parsing line-by-line. We greedy-match to end-of-line first
#     since AppDelegate emits a single NSLog call per request.
#   * The URL may contain query params; we strip to path only for routing.
REQUEST_LINE_RE = re.compile(
    r"\[BranchLog\]\s+Got\s+(?P<url>https?://[^\s]+)\s+Request:\s*(?P<body>\{.*\})\s*$"
)


def parse_branch_logs(file_path):
    """
    Reads branchlogs.txt and returns a list of {"uri", "url", "request"} dicts.
    Returns None if the file is missing; returns [] if no entries matched.
    """
    if not os.path.exists(file_path):
        print(f"Error: Log file not found at {file_path}")
        return None

    entries = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        # We read line-by-line. AppDelegate writes one NSLog call per request
        # so the JSON body should be on the same logical line.
        for line_no, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            match = REQUEST_LINE_RE.search(line)
            if not match:
                continue

            url = match.group("url")
            body_str = match.group("body")

            try:
                request = json.loads(body_str)
            except json.JSONDecodeError as e:
                # Don't echo the body itself (may contain branch_key etc.);
                # only the parse failure reason.
                print(f"Warning: line {line_no}: failed to parse request JSON: {e}")
                continue

            try:
                path = urlparse(url).path or url
            except Exception:
                path = url

            entries.append({"uri": path, "url": url, "request": request})

    return entries


def _is_str(v):
    return isinstance(v, str) and len(v) > 0


def _is_bool(v):
    return isinstance(v, bool)


def _is_number(v):
    # Exclude bool (which is a subclass of int in Python).
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validate_sdk_field(req):
    """
    iOS may emit one of two valid shapes:
      A) v1 endpoints: `sdk = "ios<version>"` (no separate sdk_version)
      B) v2 endpoints: `sdk = "ios"` and `sdk_version = "<version>"`
    Returns an error string or None.
    """
    sdk = req.get("sdk")
    if not _is_str(sdk):
        return f"missing or invalid 'sdk' (got {type(sdk).__name__})"

    if sdk == "ios":
        sdk_version = req.get("sdk_version")
        if not _is_str(sdk_version):
            return (
                "'sdk' is 'ios' but 'sdk_version' is missing/invalid "
                "(v2 shape requires both)"
            )
        return None

    if sdk.startswith("ios"):
        return None

    return f"'sdk' should start with 'ios' (got prefix {sdk[:6]!r})"


def validate_entries(entries):
    """
    Validates the captured wire payloads. Returns a list of error strings;
    empty list = success. Never echoes payload values to stdout.
    """
    errors = []

    if entries is None:
        errors.append("Log file could not be read.")
        return errors

    if not entries:
        errors.append("No Branch SDK wire requests were captured in the logs.")
        return errors

    print(f"Captured {len(entries)} Branch wire requests. Validating...")

    found_paths = [e["uri"] for e in entries]

    if "/v1/install" not in found_paths:
        errors.append("Mandatory endpoint '/v1/install' was not captured.")

    if "/v1/open" not in found_paths:
        # /v1/open requires a second launch/foreground cycle; warn only.
        print(
            "Note: '/v1/open' not present in capture. Expected after a "
            "second app launch, but not enforced here."
        )

    for i, entry in enumerate(entries, start=1):
        uri = entry["uri"]
        req = entry["request"]

        print(f"[{i}] Validating {uri}...")

        if not isinstance(req, dict):
            errors.append(f"Request {i} ({uri}): payload is not a JSON object")
            continue

        # Common: branch_key on every request.
        branch_key = req.get("branch_key")
        if not _is_str(branch_key):
            errors.append(
                f"Request {i} ({uri}): missing or invalid 'branch_key'"
            )
        elif not (
            branch_key.startswith("key_test_") or branch_key.startswith("key_live_")
        ):
            # We don't echo the key; just flag the prefix shape.
            errors.append(
                f"Request {i} ({uri}): 'branch_key' has unexpected prefix "
                "(expected 'key_test_' or 'key_live_')"
            )

        # Common: sdk identifier.
        sdk_err = _validate_sdk_field(req)
        if sdk_err is not None:
            errors.append(f"Request {i} ({uri}): {sdk_err}")

        # Endpoint-specific required fields.
        if uri == "/v1/install":
            # hardware_id is only sent at Full attribution level. TestBed
            # default is Full, so we expect it here. If a future test forces
            # attributionLevel=None, this assertion would have to relax.
            if not _is_str(req.get("hardware_id")):
                errors.append(
                    f"Request {i} (/v1/install): missing or invalid "
                    "'hardware_id' (TestBed runs at Full attribution)"
                )
            if not _is_bool(req.get("is_hardware_id_real")):
                errors.append(
                    f"Request {i} (/v1/install): missing or non-boolean "
                    "'is_hardware_id_real'"
                )
            # first_install_time is a wire-format string (ms epoch) per
            # BNCWireFormatFromDate. iOS encodes numerics as strings in some
            # paths, so accept either.
            fit = req.get("first_install_time")
            if not (_is_number(fit) or _is_str(fit)):
                errors.append(
                    f"Request {i} (/v1/install): missing 'first_install_time'"
                )

        if uri == "/v1/open":
            # After /v1/install completes, the SDK persists a
            # randomized_device_token; /v1/open should always carry it.
            if not _is_str(req.get("randomized_device_token")):
                errors.append(
                    f"Request {i} (/v1/open): missing or invalid "
                    "'randomized_device_token'"
                )

    return errors


def main():
    log_file_path = sys.argv[1] if len(sys.argv) > 1 else "branchlogs.txt"

    entries = parse_branch_logs(log_file_path)

    if entries is None:
        print("\n--- VALIDATION FAILED ---")
        print(f"FAILED: Log file not found at {log_file_path}")
        sys.exit(1)

    try:
        if os.path.getsize(log_file_path) == 0:
            print("\n--- VALIDATION FAILED ---")
            print(
                "FAILED: Log file is empty; no Branch SDK wire requests "
                "were captured."
            )
            sys.exit(1)
    except OSError:
        pass

    errors = validate_entries(entries)

    if errors:
        print("\n--- VALIDATION FAILED ---")
        for err in errors:
            print(f"FAILED: {err}")
        sys.exit(1)

    print("\n--- VALIDATION PASSED ---")
    print(f"Summary: {len(entries)} wire request(s) captured:")
    for entry in entries:
        print(f"  - {entry['uri']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
