from src.models.what_if_session import WhatIfSession
from tests.test_configuration import make_valid_config


def test_session_edits_are_isolated_and_discard_restores_baseline():
    source = make_valid_config()
    original_limit = source.limit
    session = WhatIfSession(source, "source config")

    session.configuration.limit = 25

    assert session.has_changes
    assert source.limit == original_limit

    session.discard()

    assert not session.has_changes
    assert session.configuration.limit == original_limit


def test_generation_snapshot_is_independent_from_later_edits():
    session = WhatIfSession(make_valid_config(), "source config")
    snapshot = session.generation_snapshot()

    snapshot.limit += 1

    assert session.configuration.limit != snapshot.limit
