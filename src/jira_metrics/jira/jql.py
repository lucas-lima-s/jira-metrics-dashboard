from __future__ import annotations

import re
from collections.abc import Iterable

_PROJECT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,29}$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,49}$")


def build_jql(project: str, labels: Iterable[str] = ()) -> str:
    if not _PROJECT_RE.fullmatch(project):
        raise ValueError(f"invalid Jira project key: {project!r}")

    clean = sorted({lbl.strip() for lbl in labels if lbl.strip()})
    for lbl in clean:
        if not _LABEL_RE.fullmatch(lbl):
            raise ValueError(f"invalid Jira label: {lbl!r}")

    clauses = [f'project = "{project}"']
    if clean:
        clauses.append("labels IN (" + ", ".join(f'"{lbl}"' for lbl in clean) + ")")

    return " AND ".join(clauses) + " ORDER BY created DESC"
