from __future__ import annotations

import pytest

from tests.helpers.imports import (
    IN_FLIGHT_STATUS_CANDIDATES,
    PROCESSING_STATUS_CANDIDATES,
    TERMINAL_STATUS_CANDIDATES,
    enum_member_names,
    import_attr_any,
)


pytestmark = pytest.mark.contract


def _render_names(values) -> set[str]:
    out = set()
    for item in values:
        if hasattr(item, "name"):
            out.add(item.name)
        else:
            out.add(str(item))
    return out


def test_processing_status_enum_has_expected_members():
    enum_cls = import_attr_any(PROCESSING_STATUS_CANDIDATES)
    assert enum_member_names(enum_cls) == {
        "UPLOADED",
        "REGISTERED",
        "EXTRACTING",
        "NORMALIZED",
        "CHUNKED",
        "INDEXED",
        "READY",
        "FAILED",
    }


def test_in_flight_processing_statuses_match_contract():
    statuses = import_attr_any(IN_FLIGHT_STATUS_CANDIDATES)
    assert _render_names(statuses) == {
        "REGISTERED",
        "EXTRACTING",
        "NORMALIZED",
        "CHUNKED",
        "INDEXED",
    }


def test_terminal_processing_statuses_match_contract():
    statuses = import_attr_any(TERMINAL_STATUS_CANDIDATES)
    assert _render_names(statuses) == {"READY", "FAILED"}


def test_in_flight_and_terminal_sets_are_disjoint():
    in_flight = _render_names(import_attr_any(IN_FLIGHT_STATUS_CANDIDATES))
    terminal = _render_names(import_attr_any(TERMINAL_STATUS_CANDIDATES))
    assert in_flight.isdisjoint(terminal)


def test_uploaded_is_neither_in_flight_nor_terminal():
    in_flight = _render_names(import_attr_any(IN_FLIGHT_STATUS_CANDIDATES))
    terminal = _render_names(import_attr_any(TERMINAL_STATUS_CANDIDATES))
    assert "UPLOADED" not in in_flight
    assert "UPLOADED" not in terminal
