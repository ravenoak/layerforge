#!/bin/sh
# Run `allium check` on every spec. Fail on an error diagnostic or a finding.
# Warnings and infos are accepted (see "Spec checks" in docs/development.md).
# The exit code of `allium check` is 1 on warnings, so it is not the signal.
set -eu

failed=0
for spec in specs/*.allium; do
    code=0
    out=$(allium check "$spec") || code=$?
    if [ "$code" -gt 1 ]; then
        echo "$spec: allium check exited with $code" >&2
        exit 1
    fi
    bad=$(printf '%s' "$out" | jq '([.diagnostics[] | select(.severity == "error")] | length) + (.findings | length)')
    counts=$(printf '%s' "$out" | jq -r '[.diagnostics[].severity] | group_by(.) | map("\(length) \(.[0])") | join(", ")')
    echo "$spec: ${counts:-no diagnostics}; errors and findings: ${bad:-unknown}"
    if [ "${bad:-1}" -ne 0 ]; then
        printf '%s' "$out" | jq '(.diagnostics[] | select(.severity == "error")), .findings[]' >&2
        failed=1
    fi
done
exit "$failed"
