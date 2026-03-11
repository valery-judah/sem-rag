from __future__ import annotations

import pytest

from tests.helpers.imports import (
    IN_FLIGHT_STATUS_CANDIDATES,
    INVALID_TRANSITION_ERROR_CANDIDATES,
    PROCESSING_STATUS_CANDIDATES,
    SOURCE_TYPE_CANDIDATES,
    TERMINAL_STATUS_CANDIDATES,
    VALIDATE_TRANSITION_CANDIDATES,
    enum_member_names,
    import_attr_any,
    import_module_any,
)


pytestmark = pytest.mark.contract


def test_contract_seam_module_imports_cleanly():
    module = import_module_any("parity._contracts.lifecycle")
    assert module is not None


def test_contract_processing_status_matches_runtime_processing_status():
    runtime = import_attr_any([("parity.lifecycle.status", "ProcessingStatus")])
    compat = import_attr_any([("parity._contracts.lifecycle", "ProcessingStatus")])
    assert enum_member_names(runtime) == enum_member_names(compat)


def test_contract_in_flight_statuses_match_runtime():
    runtime = import_attr_any([("parity.lifecycle.status", "IN_FLIGHT_PROCESSING_STATUSES")])
    compat = import_attr_any([("parity._contracts.lifecycle", "IN_FLIGHT_PROCESSING_STATUSES")])
    runtime_names = {item.name if hasattr(item, "name") else str(item) for item in runtime}
    compat_names = {item.name if hasattr(item, "name") else str(item) for item in compat}
    assert runtime_names == compat_names


def test_contract_terminal_statuses_match_runtime():
    runtime = import_attr_any([("parity.lifecycle.status", "TERMINAL_PROCESSING_STATUSES")])
    compat = import_attr_any([("parity._contracts.lifecycle", "TERMINAL_PROCESSING_STATUSES")])
    runtime_names = {item.name if hasattr(item, "name") else str(item) for item in runtime}
    compat_names = {item.name if hasattr(item, "name") else str(item) for item in compat}
    assert runtime_names == compat_names


def test_contract_validate_transition_reexports_runtime_helper():
    runtime = import_attr_any([("parity.lifecycle.state_machine", "validate_transition")])
    compat = import_attr_any([("parity._contracts.lifecycle", "validate_transition")])
    assert runtime is compat or runtime.__name__ == compat.__name__


def test_contract_invalid_transition_error_reexports_runtime_error():
    runtime = import_attr_any([("parity.lifecycle.errors", "InvalidLifecycleTransitionError")])
    compat = import_attr_any([("parity._contracts.lifecycle", "InvalidLifecycleTransitionError")])
    assert runtime is compat or runtime.__name__ == compat.__name__


def test_document_section_chunk_source_type_models_stay_in_contracts_module():
    module = import_module_any("parity._contracts.models")
    for attr_name in ("Document", "Section", "Chunk", "SourceType"):
        assert hasattr(module, attr_name), f"missing compatibility model: {attr_name}"
