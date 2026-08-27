#!/usr/bin/env bash
set -euo pipefail

writer="${1:-}"
mode="${2:-}"

if [ -z "$writer" ]; then
  echo "::error::writer name is required"
  exit 2
fi

case "$writer" in
  FG1|FG2-HARVEST|FG2-CLEANSING|FG2-ENRICHMENT|FG2-SYNC|FG2-AUDIT|FG3|DB-SYNC|PRODUCTION-CANARY) ;;
  *)
    echo "::error::unsupported production writer: $writer"
    exit 2
    ;;
esac

event_name="${GITHUB_EVENT_NAME:-}"
ref_name="${GITHUB_REF_NAME:-}"
automation_enabled="${AUTOMATION_ENABLED:-}"
writers_paused="${PRODUCTION_WRITERS_PAUSED:-}"
allow_writer="false"
reason="unsupported_ref"

if [ "$writer" = "DB-SYNC" ]; then
  if [ "$event_name" != "workflow_dispatch" ]; then
    reason="db_sync_requires_manual_dispatch"
  elif [ "$writers_paused" != "true" ]; then
    reason="production_writers_not_paused_for_db_sync"
  else
    allow_writer="true"
    reason="production_db_sync_allowed"
  fi
else
case "$ref_name" in
  main)
    if [ "$writer" = "PRODUCTION-CANARY" ]; then
      if [ "$event_name" != "workflow_dispatch" ]; then
        reason="production_canary_requires_manual_dispatch"
      elif [ "$automation_enabled" != "false" ]; then
        reason="production_canary_automation_not_disabled"
      elif [ "$writers_paused" != "true" ]; then
        reason="production_canary_writers_not_paused"
      else
        allow_writer="true"
        reason="production_canary_allowed"
      fi
    elif [ "$event_name" = "schedule" ] && [ "$automation_enabled" != "true" ]; then
      reason="automation_disabled"
    elif [ "$writers_paused" != "false" ]; then
      reason="production_writers_paused_or_unset"
    else
      allow_writer="true"
      reason="production_writer_allowed"
    fi
    ;;
  certificacion|desarrollo)
    if [ "$event_name" = "schedule" ]; then
      reason="non_main_schedule_blocked"
    else
      allow_writer="true"
      reason="non_production_manual_allowed"
    fi
    ;;
esac
fi

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "writer=$writer"
    echo "allow_writer=$allow_writer"
    echo "automation_enabled=${automation_enabled:-unset}"
    echo "writers_paused=${writers_paused:-unset}"
    echo "reason=$reason"
  } >> "$GITHUB_OUTPUT"
fi

echo "PRODUCTION_CONTROL writer=$writer ref=$ref_name event=$event_name allow_writer=$allow_writer reason=$reason"

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "### Production Control Preflight"
    echo ""
    echo "| Field | Value |"
    echo "|---|---|"
    echo "| Writer | $writer |"
    echo "| Ref | $ref_name |"
    echo "| Event | $event_name |"
    echo "| Allow writer | $allow_writer |"
    echo "| Reason | $reason |"
  } >> "$GITHUB_STEP_SUMMARY"
fi

if [ "$mode" = "--enforce" ] && [ "$allow_writer" != "true" ]; then
  echo "::error::production control preflight blocked writer=$writer reason=$reason"
  exit 1
fi

if [ "$allow_writer" != "true" ] && [ "$reason" != "automation_disabled" ] && [ "$reason" != "non_main_schedule_blocked" ]; then
  echo "::error::production control preflight blocked writer=$writer reason=$reason"
  exit 1
fi
