I have reviewed the current API DTO and internal model construction patterns. Here is the architectural decision and handoff for the next implementation step.

### 1. Problem Framing
- **What problem is being solved**: App-layer services (`src/doc_forge/app/services/*.py`) are currently cluttered with mapping and construction logic. They either manually extract fields to build API DTOs (e.g., `DocumentDetailResponse(doc_id=..., ...)`) or rely on implicit `Pydantic.model_validate(result, from_attributes=True)`. This violates the principle of keeping application services purely focused on orchestration, logging, and error translation. Furthermore, implicit attribute validation is brittle: if an internal model renames a field, the DTO mapping might silently fail at runtime instead of being caught by static analysis.
- **What is in scope**: Extracting mapping logic out of `src/doc_forge/app/services/` and pushing it into explicit builder/factory methods owned by the DTO classes in `src/doc_forge/app/schemas.py`.
- **What is out of scope**: Changing the structure of the internal domain models (e.g., `src/doc_forge/lifecycle/models.py`), altering the public API shape, or modifying route definitions.
- **Success conditions**: `app/services/*.py` no longer contain `from_attributes=True` calls or inline DTO instantiation. DTO schemas own their own mapping logic via explicit methods.

### 2. Constraints and Assumptions
- **Confirmed constraints**: The dependency direction must remain pure: the API/App layer depends on the internal Domain layer, never the reverse. Internal domain models must **not** import or contain logic that produces API DTOs.
- **Confirmed constraints**: The API contract defined in `docs/evergreen/api-contracts.md` is stable and must be preserved exactly.

### 3. Current-System Context
- Currently, `DocumentsAppService`, `QueriesAppService`, and `InternalAppService` handle mapping inline.
- Example from `documents.py`:
  ```python
  return UploadDocumentResponse.model_validate(result, from_attributes=True)
  ```
- `docs/engineering/python-domain-modeling.md` requires separating domain logic from transport representations. The app layer acts as the adapter between these representations.

### 4. Options Considered
- **Option 1: Add mapping methods directly to DTOs in `schemas.py` (Recommended).** DTOs use `@classmethod def from_domain(cls, domain_model)` and `def to_domain(self) -> DomainRequest`. This centralizes the contract shape and its mapping logic in one file, keeping the service clean and statically verifiable.
- **Option 2: Create a separate `mappers.py` file.** Introduces another file/concept (Mapper functions). Unnecessary indirection given that DTOs in Pydantic are functionally data bags that naturally support factory methods.
- **Option 3: Add `to_dto()` to internal domain models.** Violates the architectural dependency rule by leaking transport/app concerns into the core domain.

### 5. Recommended Design
- **Adopt Option 1.** The DTO classes in `src/doc_forge/app/schemas.py` should become the explicit owners of the mapping boundary.
- **Responsibilities**:
  - `schemas.py`: Owns the exact shape of the API payload AND explicit, type-checked conversion from/to internal domain models (e.g., `DocumentDetailResponse.from_document(...)` or `SubmitQueryRequest.to_domain()`).
  - `services/*.py`: Coordinates operations, logs business events, maps domain errors to `HTTPException`, and delegates purely to DTO factories for result formatting.

### 6. Boundaries, Interfaces, and Invariants
- **Ownership boundaries**: DTOs own the boundary translation. Application Services own the workflow.
- **Invariants to preserve**: The HTTP JSON response shapes must remain absolutely identical. The internal domain models must not change.

### 7. Change Strategy and Migration Plan
- This is an incremental refactoring localized to `src/doc_forge/app/`.
- Iterate through `src/doc_forge/app/schemas.py`, adding explicit factory methods (`from_domain` or contextual names like `from_document`, `from_query_state`) to response DTOs, and conversion methods (`to_domain`) to request DTOs.
- Update `src/doc_forge/app/services/*.py` to replace `model_validate(..., from_attributes=True)` and manual instantiation with calls to these new factory methods.

### 8. Risks and Open Questions
- **Technical risks**: Since we are replacing `from_attributes=True` with explicit mappings, care must be taken to not drop any fields or unintentionally alter type conversions (like `datetime.isoformat()`).
- **Validation Focus**: Existing tests in `tests/app/` must still pass exactly as they do now to verify no API contract changes occurred.

### 9. Code Mode Handoff
- **Implementation objective**: Remove all inline DTO construction and `from_attributes=True` calls from `src/doc_forge/app/services/*.py`.
- **First safe increment**: Add `to_domain()` and `from_domain(...)` (or similarly named) methods to the schemas in `src/doc_forge/app/schemas.py`.
- **Next increment**: Update the services in `src/doc_forge/app/services/` to invoke these factory methods.
- **Explicitly out-of-scope items**: Modifying `src/doc_forge/lifecycle/` or `src/doc_forge/query/` internal models; adding or changing API endpoints.

I am ready to hand off execution to Code mode to implement these explicit builders.