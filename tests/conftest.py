from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast

import pytest
from pydantic import BaseModel, TypeAdapter

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import configure_logging, reset_logging
from tests.persistence.conftest import *  # noqa: F401,F403


class StructuredLogCapture:
    def __init__(self, caplog: pytest.LogCaptureFixture) -> None:
        self._caplog = caplog

    @property
    def events(self) -> list[dict[str, Any]]:
        return [
            cast(dict[str, Any], record.msg)  # type: ignore
            for record in self._caplog.records
            if isinstance(record.msg, dict)
        ]

    def has_event(self, event_name: str | LogEvent, **kwargs: Any) -> bool:
        for event in self.events:
            if event.get("event") != event_name:
                continue

            match = True
            for k, v in kwargs.items():
                if event.get(k) != v:
                    match = False
                    break

            if match:
                return True
        return False

    def _find_raw_event(self, event_name: str | LogEvent) -> dict[str, Any]:
        for event in self.events:
            if event.get("event") == event_name:
                return event
        raise AssertionError(f"Event {event_name!r} not found in captured logs")

    def assert_event_matches(self, event_name: str | LogEvent, schema: Any) -> None:
        raw_event = self._find_raw_event(event_name)
        try:
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                schema.model_validate(raw_event)
            else:
                TypeAdapter(schema).validate_python(raw_event)  # type: ignore
        except Exception as e:
            raise AssertionError(f"Event {event_name!r} failed schema validation: {e}") from e


@pytest.fixture
def structured_caplog(caplog: pytest.LogCaptureFixture) -> StructuredLogCapture:
    return StructuredLogCapture(caplog)


@pytest.fixture
def configured_logging() -> Generator[None, None, None]:
    reset_logging()
    configure_logging(service="test-service", environment="test", level="INFO")
    yield
    reset_logging()
