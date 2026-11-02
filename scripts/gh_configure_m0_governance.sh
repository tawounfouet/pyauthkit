#!/usr/bin/env bash
# PyAuthKit M0 repository administration via gh CLI. Dry run by default.
set -Eeuo pipefail

REPO="${REPO:-tawounfouet/pyauthkit}"
RULESET_ID="${RULESET_ID:-26350656}"
REQUIRED_APPROVALS="${REQUIRED_APPROVALS:-0}"
MODE="${1:---plan}"

if [[ "$MODE" != "--plan" && "$MODE" != "--apply" ]]; then
  echo "Usage: $0 [--plan|--apply]" >&2
  exit 2
fi
if [[ ! "$REQUIRED_APPROVALS" =~ ^[0-9]+$ ]] || (( REQUIRED_APPROVALS > 10 )); then
  echo "REQUIRED_APPROVALS must be an integer from 0 to 10" >&2
  exit 2
fi

for binary in gh jq; do
  command -v "$binary" >/dev/null || { echo "Missing: $binary" >&2; exit 1; }
done
gh auth status >/dev/null

current="$(gh api "repos/$REPO/rulesets/$RULESET_ID")"
jq -e --arg repo "$REPO" '
  .name == "PYAUTHKIT_PROTECT_MAIN"
  and .target == "branch"
  and .source == $repo
' <<<"$current" >/dev/null || { echo "Unexpected ruleset: no changes applied" >&2; exit 1; }

for rule in deletion non_fast_forward pull_request required_status_checks; do
  jq -e --arg rule "$rule" 'any(.rules[]; .type == $rule)' <<<"$current" >/dev/null ||
    { echo "Missing existing rule: $rule" >&2; exit 1; }
done

checks="$(jq -n '[
  "Lint, types, unit and architecture",
  "Dependency, source and secret scans",
  "Wheel / sdist / smoke (ubuntu-latest Py3.12)",
  "Wheel / sdist / smoke (ubuntu-latest Py3.13)",
  "Wheel / sdist / smoke (ubuntu-latest Py3.14)",
  "Wheel / sdist / smoke (macos-latest Py3.12)",
  "Wheel / sdist / smoke (windows-latest Py3.12)"
] | map({context: .})')"

# Preserve existing rules and bypass list; update target and CI requirements only.
payload="$(jq --argjson checks "$checks" --argjson approvals "$REQUIRED_APPROVALS" '
  {name, target, enforcement, bypass_actors, conditions, rules}
  | .enforcement = "active"
  | .conditions.ref_name.include = ["refs/heads/main"]
  | .conditions.ref_name.exclude = []
  | .rules |= map(
      if .type == "required_status_checks" then
        .parameters.required_status_checks = $checks
        | .parameters.strict_required_status_checks_policy = true
        | .parameters.do_not_enforce_on_create = false
      elif .type == "pull_request" then
        .parameters.required_approving_review_count = $approvals
        | .parameters.required_review_thread_resolution = true
      else . end
    )
' <<<"$current")"

echo "Ruleset configuration to apply:"
jq '{name, enforcement, conditions, bypass_actors,
  review_count: (.rules[] | select(.type == "pull_request") | .parameters.required_approving_review_count),
  checks: [.rules[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context]
}' <<<"$payload"

if [[ "$MODE" == "--plan" ]]; then
  echo "DRY RUN: no settings changed. Run with --apply to configure GitHub."
  exit 0
fi

file="$(mktemp)"
trap 'rm -f "$file"' EXIT
printf '%s\n' "$payload" >"$file"

# This operation requires GitHub repository Administration:write permission.
gh api --method PUT "repos/$REPO/rulesets/$RULESET_ID" --input "$file" >/dev/null

verified="$(gh api "repos/$REPO/rulesets/$RULESET_ID")"
jq -e --argjson checks "$checks" '
  .enforcement == "active"
  and .conditions.ref_name.include == ["refs/heads/main"]
  and .conditions.ref_name.exclude == []
  and (.rules | any(.type == "required_status_checks"
    and .parameters.strict_required_status_checks_policy == true
    and .parameters.required_status_checks == $checks))
' <<<"$verified" >/dev/null || { echo "Ruleset readback mismatch!" >&2; exit 1; }
echo "Ruleset verified on main with 7 required checks."

gh api --method PUT "repos/$REPO/private-vulnerability-reporting" >/dev/null
enabled="$(gh api "repos/$REPO/private-vulnerability-reporting" --jq '.enabled')"
[[ "$enabled" == "true" ]] || { echo "Private reporting readback failed" >&2; exit 1; }
echo "Private vulnerability reporting enabled and verified."
echo "Review Issue #59 and M0 evidence before signing GATE27-01."
