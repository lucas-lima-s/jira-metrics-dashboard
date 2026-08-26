import logging

from jira_metrics.logging_setup import configure_logging


def test_configure_logging_sets_level():
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG

    configure_logging("INFO")
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_falls_back_to_info_on_unknown_level():
    configure_logging("NOT-A-LEVEL")
    assert logging.getLogger().level == logging.INFO
