from __future__ import annotations

import importlib
import inspect
from functools import lru_cache
from types import ModuleType
from typing import Any, Iterable, Sequence


class MissingImplementationError(AssertionError):
    pass


def _normalize_candidates(candidates: Sequence[Any]) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    for candidate in candidates:
        if isinstance(candidate, str):
            out.append((candidate, None))
        else:
            module_path, attr = candidate
            out.append((module_path, attr))
    return out


@lru_cache(maxsize=None)
def import_module_any(*module_paths: str) -> ModuleType:
    last_error: BaseException | None = None
    for module_path in module_paths:
        try:
            return importlib.import_module(module_path)
        except Exception as exc:  # pragma: no cover - exercised by missing-module scenarios
            last_error = exc
    raise MissingImplementationError(
        "Could not import any of the candidate modules: "
        + ", ".join(module_paths)
        + (f" | last error: {last_error!r}" if last_error else "")
    )


def import_attr_any(candidates: Sequence[tuple[str, str]]) -> Any:
    last_error: BaseException | None = None
    for module_path, attr_name in candidates:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, attr_name):
                return getattr(module, attr_name)
        except Exception as exc:  # pragma: no cover - exercised by missing-module scenarios
            last_error = exc
    rendered = ", ".join([f"{m}:{a}" for m, a in candidates])
    raise MissingImplementationError(
        "Could not resolve any of the candidate attributes: "
        + rendered
        + (f" | last error: {last_error!r}" if last_error else "")
    )


def maybe_import_attr_any(candidates: Sequence[tuple[str, str]]) -> Any | None:
    try:
        return import_attr_any(candidates)
    except MissingImplementationError:
        return None


def construct_with_supported_kwargs(target: Any, **kwargs: Any) -> Any:
    sig = inspect.signature(target)
    accepted = {}
    for name, param in sig.parameters.items():
        if name in kwargs:
            accepted[name] = kwargs[name]
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            accepted.update(kwargs)
            break
    return target(**accepted)


def call_with_supported_kwargs(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    sig = inspect.signature(func)
    accepted = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name in kwargs:
            accepted[name] = kwargs[name]
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            accepted.update(kwargs)
            break
    return func(*args, **accepted)


def class_from_module_any(
    module_candidates: Sequence[str],
    class_names: Sequence[str],
) -> type:
    last_error: BaseException | None = None
    for module_path in module_candidates:
        try:
            module = importlib.import_module(module_path)
        except Exception as exc:
            last_error = exc
            continue
        for class_name in class_names:
            if hasattr(module, class_name):
                value = getattr(module, class_name)
                if inspect.isclass(value):
                    return value
    raise MissingImplementationError(
        f"Could not resolve any class from modules={module_candidates} names={class_names}; "
        f"last_error={last_error!r}"
    )


def build_instance(
    module_candidates: Sequence[str],
    class_names: Sequence[str],
    **kwargs: Any,
) -> Any:
    cls = class_from_module_any(module_candidates, class_names)
    return construct_with_supported_kwargs(cls, **kwargs)


def enum_member_names(enum_cls: Any) -> set[str]:
    if hasattr(enum_cls, "__members__"):
        return set(enum_cls.__members__.keys())
    return {item.name for item in enum_cls}


def enum_member(enum_cls: Any, name: str) -> Any:
    if hasattr(enum_cls, "__members__"):
        return enum_cls.__members__[name]
    for item in enum_cls:
        if item.name == name:
            return item
    raise KeyError(name)


def filter_kwargs_for_callable(target: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    sig = inspect.signature(target)
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values()):
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def is_dataclass_instance(obj: Any) -> bool:
    return hasattr(obj, "__dataclass_fields__")


def get_attr(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
        if isinstance(obj, dict) and name in obj:
            return obj[name]
    return default


def assert_has_attrs(obj: Any, names: Iterable[str]) -> None:
    missing = [name for name in names if get_attr(obj, name, default=None) is None and not hasattr(obj, name)]
    if missing:
        raise AssertionError(f"Object is missing expected attributes: {missing}; object={obj!r}")


PROCESSING_STATUS_CANDIDATES = [
    ("parity.lifecycle.status", "ProcessingStatus"),
    ("parity._contracts.lifecycle", "ProcessingStatus"),
    ("parity._contracts.models", "ProcessingStatus"),
]

IN_FLIGHT_STATUS_CANDIDATES = [
    ("parity.lifecycle.status", "IN_FLIGHT_PROCESSING_STATUSES"),
    ("parity._contracts.lifecycle", "IN_FLIGHT_PROCESSING_STATUSES"),
]

TERMINAL_STATUS_CANDIDATES = [
    ("parity.lifecycle.status", "TERMINAL_PROCESSING_STATUSES"),
    ("parity._contracts.lifecycle", "TERMINAL_PROCESSING_STATUSES"),
]

VALIDATE_TRANSITION_CANDIDATES = [
    ("parity.lifecycle.state_machine", "validate_transition"),
    ("parity.lifecycle.state_machine", "assert_transition_allowed"),
    ("parity._contracts.lifecycle", "validate_transition"),
]

IS_VALID_TRANSITION_CANDIDATES = [
    ("parity.lifecycle.state_machine", "is_valid_transition"),
    ("parity.lifecycle.state_machine", "transition_is_valid"),
    ("parity._contracts.lifecycle", "is_valid_transition"),
]

INVALID_TRANSITION_ERROR_CANDIDATES = [
    ("parity.lifecycle.errors", "InvalidLifecycleTransitionError"),
    ("parity._contracts.lifecycle", "InvalidLifecycleTransitionError"),
]

LIFECYCLE_INVARIANT_ERROR_CANDIDATES = [
    ("parity.lifecycle.errors", "LifecycleInvariantError"),
    ("parity._contracts.lifecycle", "LifecycleInvariantError"),
]

LIFECYCLE_EVENT_CANDIDATES = [
    ("parity.lifecycle.models", "LifecycleEvent"),
]

LIFECYCLE_STAGE_CANDIDATES = [
    ("parity.lifecycle.models", "LifecycleStage"),
]

FAILURE_CATEGORY_CANDIDATES = [
    ("parity.lifecycle.models", "FailureCategory"),
]

READINESS_PREDICATE_CANDIDATES = [
    ("parity.lifecycle.readiness", "is_ready"),
    ("parity.lifecycle.readiness", "evaluate_readiness"),
]

DOCUMENT_MODEL_CANDIDATES = [
    ("parity._contracts.models", "Document"),
]

SECTION_MODEL_CANDIDATES = [
    ("parity._contracts.models", "Section"),
]

CHUNK_MODEL_CANDIDATES = [
    ("parity._contracts.models", "Chunk"),
]

SOURCE_TYPE_CANDIDATES = [
    ("parity._contracts.models", "SourceType"),
]

INDEX_ENTRY_MODEL_CANDIDATES = [
    ("parity.persistence.models", "IndexEntry"),
    ("parity.indexing.models", "IndexEntry"),
    ("parity.lifecycle.models", "IndexEntry"),
]

NORMALIZED_BLOCK_CANDIDATES = [
    ("parity.artifacts.schemas", "NormalizedBlock"),
    ("parity.normalizers.base", "NormalizedBlock"),
]

NORMALIZED_PAYLOAD_CANDIDATES = [
    ("parity.artifacts.schemas", "NormalizedPayload"),
    ("parity.normalizers.base", "NormalizedPayload"),
]

EXTRACTED_ARTIFACT_CANDIDATES = [
    ("parity.artifacts.schemas", "ExtractedArtifact"),
    ("parity.extractors.base", "ExtractedArtifact"),
]

DOCUMENT_JOB_CANDIDATES = [
    ("parity.persistence.models", "DocumentJob"),
    ("parity.lifecycle.models", "DocumentJob"),
]
