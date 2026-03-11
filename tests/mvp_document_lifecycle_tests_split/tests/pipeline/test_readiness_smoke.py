from __future__ import annotations

import pytest

from tests.helpers.fakes import FakeReadinessService


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


def test_indexed_chunks_are_queryable(ready_document_bundle, readiness_service):
    assert readiness_service.evaluate(doc_id="doc_ready") is True
