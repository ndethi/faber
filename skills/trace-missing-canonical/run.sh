#!/usr/bin/env bash
# trace-missing-canonical run script
# Detects drift between _inbox/ canonical files and repo locations

set -euo pipefail

echo "=== trace-missing-canonical: Checking for drift ==="

# Files to check (from _inbox/ CHECKSUMS.txt and build.00)
CHECK_FILES=(
    "FRAMEWORK.md"
    "INTERFACE.md"
    "IDENTITY.md"
    "RUNBOOK.md"
    "prompts/"
    "build-plan/"
)

DRIFT_FOUND=0

for path in "${CHECK_FILES[@]}"; do
    if [ -e "_inbox/$path" ] && [ -e "$path" ]; then
        if ! diff -r "_inbox/$path" "$path" >/dev/null 2>&1; then
            echo "DRIFT DETECTED: $path"
            diff -r "_inbox/$path" "$path" || true
            DRIFT_FOUND=1
        else
            echo "OK: $path matches _inbox"
        fi
    elif [ -e "_inbox/$path" ]; then
        echo "MISSING IN REPO: $path (exists in _inbox but not in repo)"
        DRIFT_FOUND=1
    elif [ -e "$path" ]; then
        echo "EXTRA IN REPO: $path (exists in repo but not in _inbox)"
        # This might be OK for evolved files like FRAMEWORK.md
        # Just warn, don't fail
        echo "  (warning only - file may have evolved)"
    fi
done

# Also verify CHECKSUMS.txt if it exists
if [ -f "_inbox/CHECKSUMS.txt" ]; then
    echo ""
    echo "=== Verifying CHECKSUMS.txt ==="
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            expected_hash=$(echo "$line" | awk '{print $1}')
            file_path=$(echo "$line" | awk '{print $2}')
            if [ -f "_inbox/$file_path" ]; then
                actual_hash=$(shasum -a 256 "_inbox/$file_path" | awk '{print $1}')
                if [ "$expected_hash" != "$actual_hash" ]; then
                    echo "CHECKSUM MISMATCH: _inbox/$file_path"
                    echo "  Expected: $expected_hash"
                    echo "  Actual:   $actual_hash"
                    DRIFT_FOUND=1
                fi
            fi
        fi
    done < "_inbox/CHECKSUMS.txt"
fi

if [ $DRIFT_FOUND -eq 0 ]; then
    echo ""
    echo "OK: no drift detected"
    exit 0
else
    echo ""
    echo "FAIL: drift detected"
    exit 1
fi