#!/bin/sh
set -e

if [ "${DEBUGPY_ENABLE:-false}" = "true" ]; then
  WAIT=""
  [ "${DEBUGPY_WAIT:-false}" = "true" ] && WAIT="--wait-for-client"
  echo "[entrypoint] debugpy on :${DEBUGPY_PORT:-5678} ${WAIT}"
  [ "$1" = "jira-metrics" ] && shift
  exec python -m debugpy --listen 0.0.0.0:"${DEBUGPY_PORT:-5678}" $WAIT -m jira_metrics "$@"
fi

exec "$@"
