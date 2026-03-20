---
artifact_kind: workstream
id: WS-023
title: Api Docs Extract
work_type: refactor
status: completed
owner: Architect / Code Mode
created: 2026-03-20
updated: 2026-03-20
---

# Summary
Extracted large JSON dictionary examples and endpoint descriptions from `src/doc_forge/app/api.py` and `src/doc_forge/query/review.py` into companion Python modules (`api_examples.py` and `review_examples.py`) to keep the core Pydantic models clean and resolve `ruff` E501 line length limits.


## Current status
Workstream is fully implemented and validated. All targeted schemas have been refactored to use the extracted constants. All CI checks (`uv run poe verify`) have passed successfully.

## Next step
- Workstream complete. No further actions needed.