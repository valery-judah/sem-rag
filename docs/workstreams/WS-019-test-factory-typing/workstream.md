# Test Factory Typing Refactoring

## Overview
This workstream tracks the refactoring of pytest fixtures used as test factories. It replaces generic `Callable[..., Model]` type hints with strongly typed `Protocol` and `Unpack[TypedDict]` combinations to restore full IDE autocomplete and static type safety when creating test data.

## Problem Statement
Previously, our test factories in `tests/persistence/conftest.py` used `**overrides: Any` alongside a return type of `Callable[..., Model]`. While this approach is flexible and avoids duplicating parameter lists, it completely defeats static type checking and IDE autocomplete. Developers calling `chunk_factory(txet="foo")` would not receive any warnings about the misspelling, and IDEs could not suggest valid fields.

## Solution: Protocol + Unpack[TypedDict]
We adopted a modern Python typing pattern (introduced in PEP 692, supported in Python 3.11+ via type checkers like Pyright):

1. **`TypedDict`**: Define a `[Model]Overrides` dictionary (`total=False`) that precisely maps all optional keyword arguments the factory accepts.
2. **`Protocol`**: Define a `[Model]Factory` protocol with a `__call__` method. The `**overrides` parameter is typed as `Unpack[[Model]Overrides]`.

### Example
```python
from typing import Protocol, TypedDict, Unpack, Any

class ChunkOverrides(TypedDict, total=False):
    text: str
    ordinal: int
    # ... other optional fields

class ChunkFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: Unpack[ChunkOverrides],
    ) -> Chunk: ...

@pytest.fixture
def chunk_factory() -> ChunkFactory:
    def make(
        doc_id: DocId = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: Unpack[ChunkOverrides],
    ) -> Chunk:
        base: dict[str, Any] = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            # ... defaults
        }
        base.update(overrides)
        return Chunk(**base)
    return make
```

## Scope of Work Completed
1. **Fixtures Refactored**:
   - `chunk_factory` -> `ChunkFactory`
   - `section_factory` -> `SectionFactory`
   - `document_factory` -> `DocumentFactory`
   - `persisted_document_factory` -> `PersistedDocumentFactory`
   - `lifecycle_event_factory` -> `LifecycleEventFactory`
   - `document_job_factory` -> `DocumentJobFactory`

2. **Test Files Updated**:
   - Replaced all `Callable[..., Model]` type hints with the new Factory Protocols across `tests/`.
   - Removed unused `Callable` imports.

## Impact
- **Type Safety**: Invalid kwargs passed to factories now trigger Pyright errors immediately.
- **Developer Experience**: IDEs now provide rich autocomplete for factory overrides, making it significantly easier to author and maintain tests without jumping to model definitions.
- **Maintainability**: The `TypedDict` acts as a clear contract for what can be overridden, documenting the factory's capabilities.