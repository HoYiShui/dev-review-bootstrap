#!/usr/bin/env bash
set -euo pipefail

REPORT_FILE="${1:?report path required}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$ROOT/__WORKFLOW_DIR__"
ENV_FILE="$WORKFLOW_DIR/workflow.env"
HANDOFF_FILE="$WORKFLOW_DIR/state/dev_handoff.yaml"
SCHEMA_FILE="$WORKFLOW_DIR/review_schema.json"
SCHEDULE_FILE="$WORKFLOW_DIR/schedule.yaml"
ACTIVE_CONTEXT_FILE="$WORKFLOW_DIR/state/active_context.yaml"
OPEN_FINDINGS_FILE="$WORKFLOW_DIR/state/open_findings.yaml"

if [[ ! -f "$ENV_FILE" || ! -f "$HANDOFF_FILE" || ! -f "$SCHEMA_FILE" ]]; then
  echo "workflow files are incomplete" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

TASK_ID="$(awk -F': *' '/^task_id:/{print $2; exit}' "$HANDOFF_FILE" | tr -d '\"')"
TURN_ID="$(awk -F': *' '/^turn_id:/{print $2; exit}' "$HANDOFF_FILE" | tr -d '\"')"

mkdir -p "$(dirname "$REPORT_FILE")"

PROMPT_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE"' EXIT

cat >"$PROMPT_FILE" <<EOF
Review the current uncommitted changes for task ${TASK_ID:-unknown}.

Read these files before reviewing:
- $SCHEDULE_FILE
- $ACTIVE_CONTEXT_FILE
- $HANDOFF_FILE
- $OPEN_FINDINGS_FILE

Review focus:
- correctness bugs
- behavioral regressions
- missing tests
- risky assumptions
- whether open findings were actually resolved

Return a structured object that satisfies the provided schema.

If there are no blocking findings, use verdict "accepted".
If there are unresolved bugs or regressions that should send work back to dev, use verdict "changes_requested".
If the task cannot proceed without user input or an external dependency, use verdict "blocked".

Keep finding ids stable when you are clearly referring to an existing unresolved finding.
Use concise evidence grounded in the current diff or the workflow files.
EOF

if [[ -n "${TEST_COMMAND:-}" ]]; then
  cat >>"$PROMPT_FILE" <<EOF

The project test command is:
$TEST_COMMAND

If the diff suggests tests should have been run or updated, factor that into the review.
EOF
fi

CMD=(codex exec -s read-only --output-schema "$SCHEMA_FILE" -o "$REPORT_FILE")
if [[ -n "${REVIEWER_PROFILE:-}" ]]; then
  CMD+=(-p "$REVIEWER_PROFILE")
fi
CMD+=(review --uncommitted -)

"${CMD[@]}" <"$PROMPT_FILE"
