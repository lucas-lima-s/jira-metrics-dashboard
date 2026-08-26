from __future__ import annotations

TRACKED = {"IN PROGRESS", "DONE"}


def status_transition_dates(issue: dict) -> dict[str, str]:
    """Earliest date each tracked status was entered.

    Jira returns `changelog.histories` oldest-first, so keeping the first
    occurrence per status name (and skipping later repeats) yields the
    earliest transition into that status.
    """
    histories = (issue.get("changelog") or {}).get("histories") or []
    out: dict[str, str] = {}

    for history in histories:
        for item in history.get("items") or []:
            if item.get("fieldId") != "status":
                continue

            name = (item.get("toString") or "").strip().upper()
            if name in TRACKED and name not in out:
                out[name] = history.get("created")

    return out
