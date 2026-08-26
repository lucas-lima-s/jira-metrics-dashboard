import pytest

from jira_metrics.jira.jql import build_jql


def test_simple_project_only():
    assert build_jql("DEMO") == 'project = "DEMO" ORDER BY created DESC'


def test_labels_are_deduped_stripped_and_sorted():
    assert (
        build_jql("DEMO", ["b", " a ", "", "a"])
        == 'project = "DEMO" AND labels IN ("a", "b") ORDER BY created DESC'
    )


def test_empty_label_list_produces_no_and_clause():
    assert build_jql("DEMO", []) == 'project = "DEMO" ORDER BY created DESC'


def test_whitespace_only_labels_produce_no_and_clause():
    assert build_jql("DEMO", ["   ", ""]) == 'project = "DEMO" ORDER BY created DESC'


@pytest.mark.parametrize("project", ["DE MO", "1DEMO", "", "de-mo"])
def test_invalid_project_key_raises(project):
    with pytest.raises(ValueError):
        build_jql(project)


def test_invalid_label_raises():
    with pytest.raises(ValueError):
        build_jql("DEMO", ['a") OR 1=1--'])
