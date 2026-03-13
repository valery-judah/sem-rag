# Current Plan

## Summary
Use the query-centric context bundle as the canonical operator / eval reopening
surface, then close the highest-value gaps exposed by live bundle analysis.

## What Was Proven
- Existing `e2e` and `eval` bundles are sufficient to reconstruct a query run
  from indexed assets rather than raw service logs.
- Eval bundles are especially useful because `query-response.json`,
  `eval-result.json`, and `execution-metadata.json` sit next to trace, replay,
  citations, and filtered logs.
- A fresh compose query can also be collected into a usable bundle under
  `data/context/queries/<query_id>/`.

## Current Findings To Act On
- The fresh compose query
  `qry-f5fac35f6862463986d8ea7dc74bd3a3` shows a retrieval / selection /
  support-quality issue:
  the run marked support as sufficient and answered directly, but the answer
  focused on fixed-window fallback guidance instead of the asked citation-format
  preference.
- The collector gap is closed:
  non-eval bundles now reconstruct `query-response.json` from persisted final
  artifacts.
- Compose defaults are now safer for local experiments because the default
  answer generator is `deterministic`; Ollama use is now an explicit override.

## Implementation Priorities
1. Use the collected compose bundle for
   `qry-f5fac35f6862463986d8ea7dc74bd3a3` to debug why retrieval and selection
   let unrelated answer content dominate despite the correct citation-format
   sentence being present in the same evidence.
2. Decide whether the wrong-answer case is primarily a retrieval, context
   selection, support-assessment, or answer-generation failure, then turn that
   into a bounded code change and regression test.
3. If local Ollama use becomes a maintained workflow, add explicit preflight
   validation for the configured model instead of relying only on deterministic
   defaults.

## Acceptance Signal
- The wrong-answer compose case can be explained from the bundle and converted
  into a concrete fix target in retrieval, selection, support assessment, or
  generation.
- Non-eval bundles continue to expose the final public answer directly through
  `query-response.json`.
- A local compose experiment no longer fails by default just because the
  configured Ollama model is absent.
