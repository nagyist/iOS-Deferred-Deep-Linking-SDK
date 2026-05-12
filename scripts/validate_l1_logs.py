import json
import re
import sys
import os

def parse_ios_logs(file_path):
    """
    Parses the xcodebuild output and extracts Branch SDK request/response pairs.
    iOS logs often use BNCLog or print statements.
    """
    if not os.path.exists(file_path):
        print(f"Error: Log file not found at {file_path}")
        return []

    with open(file_path, 'r') as f:
        content = f.read()

    # iOS logging pattern might differ slightly from Android
    # We look for the JSON blocks in the console output
    entries = []
    
    # Looking for request patterns in the logs
    # Example: [BranchSDK] Body: { ... }
    blocks = re.split(r'\[BranchSDK\] Body:', content)
    
    for block in blocks[1:]: # Skip first block
        entry = {}
        
        # Extract JSON body
        # Matches the first balanced { } or until a new log tag starts
        json_match = re.search(r'(\{.*?\})', block, re.DOTALL)
        if json_match:
            try:
                # Clean up potential log prefixes in each line
                json_str = json_match.group(1)
                entry['request'] = json.loads(json_str)
                entries.append(entry)
            except json.JSONDecodeError:
                continue
                
    return entries

def validate_entries(entries):
    errors = []
    if not entries:
        errors.append("No Branch SDK requests were captured in the iOS logs.")
        return errors

    # Check for mandatory events (iOS often uses different labels, but we check common patterns)
    # This ensures we didn't just capture an empty session
    has_install_or_open = any('device_fingerprint_id' in e.get('request', {}) for e in entries)
    if not has_install_or_open:
        errors.append("No critical event (Install/Open) with device_fingerprint_id was found.")

    print(f"Captured {len(entries)} Branch requests. Starting validation...")
    
    for i, entry in enumerate(entries):
        req = entry.get('request', {})
        # iOS uses different keys for some fields, adjust as needed
        required_base = ['branch_key', 'device_fingerprint_id']
        
        for field in required_base:
            if field not in req:
                errors.append(f"Request {i+1}: Missing required field '{field}'")
                
    return errors

if __name__ == "__main__":
    log_file_path = sys.argv[1] if len(sys.argv) > 1 else "ios_test_output.log"
    found_entries = parse_ios_logs(log_file_path)
    validation_errors = validate_entries(found_entries)
    
    if validation_errors:
        print("\n--- VALIDATION FAILED ---")
        for err in validation_errors:
            print(f"FAILED: {err}")
        sys.exit(1)
    else:
        print("\n--- VALIDATION PASSED ---")
        sys.exit(0)
