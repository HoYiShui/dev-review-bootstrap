#!/usr/bin/env bash
set -euo pipefail

if [[ "${DEV_REVIEW_HOOK_ACTIVE:-}" == "1" ]]; then
  exit 0
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$ROOT/__WORKFLOW_DIR__"
ENV_FILE="$WORKFLOW_DIR/workflow.env"
HANDOFF_FILE="$WORKFLOW_DIR/state/dev_handoff.yaml"

if [[ ! -f "$ENV_FILE" || ! -f "$HANDOFF_FILE" ]]; then
  exit 0
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

if [[ "${TRIGGER_MODE:-stop}" != "stop" ]]; then
  exit 0
fi

TURN_ID="$(awk -F': *' '/^turn_id:/{print $2; exit}' "$HANDOFF_FILE" | tr -d '\"')"

if [[ -z "$TURN_ID" || "$TURN_ID" == "pending" ]]; then
  exit 0
fi

REPORT_FILE="$ROOT/reviews/${TURN_ID}.json"

if [[ -f "$REPORT_FILE" ]]; then
  exit 0
fi

export DEV_REVIEW_HOOK_ACTIVE=1
"$WORKFLOW_DIR/hooks/run_reviewer.sh" "$REPORT_FILE"
python3 "$WORKFLOW_DIR/hooks/update_memory.py" \
  --workflow-dir "$WORKFLOW_DIR" \
  --review-file "$REPORT_FILE"
