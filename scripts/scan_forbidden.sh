#!/usr/bin/env bash
set -uo pipefail

PATTERN='e-?[dD]eploy|edeploy\.atlassian|iFood|IFOOD|\bRBI\b|systools|\bAPED\b|\bOXAP\b|POS ?- ?TS|POS-WTC|Sacola|ATATT[0-9A-Za-z]|customfield_10041|customfield_10008|drythz|C:[\\/]Users|D:[\\/]Projects|OneDrive|ALBERT DAVID|ANDRESSA|CLAUDINEI|JOAO\.RIBEIRO|PEDRO HENRIQUE|lucas\.lima@'

# This script and the dashboard-sanity test embed the pattern itself (and the
# tokens it hunts for, as negative-assertion literals) to define what "clean"
# means. Exclude them from the scan so the detector does not flag its own
# source as a violation.
EXCLUDE=(':(exclude)scripts/scan_forbidden.sh' ':(exclude)tests/test_dashboard_sanity.py')

if git grep -InE "$PATTERN" -- . "${EXCLUDE[@]}" ; then
  echo "FORBIDDEN TOKEN IN WORKING TREE"
  exit 1
fi

if git grep -InE "$PATTERN" $(git rev-list --all) -- . "${EXCLUDE[@]}" ; then
  echo "FORBIDDEN TOKEN IN HISTORY"
  exit 1
fi

git check-ignore -q .env || { echo ".env is not gitignored"; exit 1; }

echo "clean"
