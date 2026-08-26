#!/usr/bin/env bash
set -uo pipefail

PATTERN='e-?[dD]eploy|edeploy\.atlassian|iFood|IFOOD|\bRBI\b|systools|\bAPED\b|\bOXAP\b|POS ?- ?TS|POS-WTC|Sacola|ATATT[0-9A-Za-z]|customfield_10041|customfield_10008|drythz|C:[\\/]Users|D:[\\/]Projects|OneDrive|ALBERT DAVID|ANDRESSA|CLAUDINEI|JOAO\.RIBEIRO|PEDRO HENRIQUE|lucas\.lima@'

if git grep -InE "$PATTERN" -- . ; then
  echo "FORBIDDEN TOKEN IN WORKING TREE"
  exit 1
fi

if git grep -InE "$PATTERN" $(git rev-list --all) -- . ; then
  echo "FORBIDDEN TOKEN IN HISTORY"
  exit 1
fi

git check-ignore -q .env || { echo ".env is not gitignored"; exit 1; }

echo "clean"
