from __future__ import annotations

import pytest

from tests.helpers.imports import (
    INVALID_TRANSITION_ERROR_CANDIDATES,
    IS_VALID_TRANSITION_CANDIDATES,
    PROCESSING_STATUS_CANDIDATES,
    VALIDATE_TRANSITION_CANDIDATES,
    enum_member,
    import_attr_any,
)


pytestmark = pytest.mark.contract


@pytest.fixture
def processing_status():
    return import_attr_any(PROCESSING_STATUS_CANDIDATES)


@pytest.fixture
def is_valid_transition():
    return import_attr_any(IS_VALID_TRANSITION_CANDIDATES)


@pytest.fixture
def validate_transition():
    return import_attr_any(VALIDATE_TRANSITION_CANDIDATES)


@pytest.fixture
def invalid_transition_error():
    return import_attr_any(INVALID_TRANSITION_ERROR_CANDIDATES)


@pytest.mark.parametrize(
    ("source_name", "dest_name"),
    [
        ("UPLOADED", "REGISTERED"),
        ("REGISTERED", "EXTRACTING"),
        ("EXTRACTING", "NORMALIZED"),
        ("NORMALIZED", "CHUNKED"),
        ("CHUNKED", "INDEXED"),
        ("INDEXED", "READY"),
    ],
)
def test_linear_happy_path_transitions_are_allowed(processing_status, is_valid_transition, validate_transition, source_name, dest_name):
    source = enum_member(processing_status, source_name)
    dest = enum_member(processing_status, dest_name)
    assert is_valid_transition(source, dest) is True
    validate_transition(source, dest)


@pytest.mark.parametrize(
    "source_name",
    ["REGISTERED", "EXTRACTING", "NORMALIZED", "CHUNKED", "INDEXED"],
)
def test_failed_is_reachable_from_all_in_flight_statuses(processing_status, is_valid_transition, validate_transition, source_name):
    source = enum_member(processing_status, source_name)
    failed = enum_member(processing_status, "FAILED")
    assert is_valid_transition(source, failed) is True
    validate_transition(source, failed)


@pytest.mark.parametrize(
    ("source_name", "dest_name"),
    [
        ("UPLOADED", "FAILED"),
        ("REGISTERED", "CHUNKED"),
        ("EXTRACTING", "INDEXED"),
        ("READY", "CHUNKED"),
        ("READY", "FAILED"),
        ("FAILED", "READY"),
        ("FAILED", "REGISTERED"),
    ],
)
def test_illegal_transitions_are_rejected(processing_status, validate_transition, invalid_transition_error, source_name, dest_name):
    source = enum_member(processing_status, source_name)
    dest = enum_member(processing_status, dest_name)
    with pytest.raises(invalid_transition_error):
        validate_transition(source, dest)


def test_uploaded_to_failed_is_rejected_explicitly(processing_status, validate_transition, invalid_transition_error):
    with pytest.raises(invalid_transition_error):
        validate_transition(
            enum_member(processing_status, "UPLOADED"),
            enum_member(processing_status, "FAILED"),
        )


def test_indexed_to_ready_is_only_happy_path_terminal_success(processing_status, is_valid_transition):
    indexed = enum_member(processing_status, "INDEXED")
    ready = enum_member(processing_status, "READY")
    failed = enum_member(processing_status, "FAILED")
    assert is_valid_transition(indexed, ready) is True
    assert is_valid_transition(indexed, failed) is True
