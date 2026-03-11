# MVP document lifecycle test bundle

This bundle is intentionally written as a **single split-ready text artifact**.
Each section begins with:

    /// relative/path/to/file.py

The code is designed around the constraints in the lifecycle architecture, MVP framing,
and PR1 lifecycle-contract brief.

What is concrete here:

- state-machine and readiness tests are fully specified
- stage, persistence, artifact, and pipeline tests are written against the interfaces and package layout described in the docs
- helper import/constructor adapters make the suite tolerant of minor module and signature drift
- the suite is split by concern so you can decouple it into real files with minimal editing

What you will likely need to adapt after splitting:

- exact class names for concrete runners and repositories if they differ from the documented package layout
- your repo's DB/session fixture wiring
- your artifact-store API details
- the small PDF fixture generation step if you want binary fixtures committed rather than generated

The suite is intentionally biased toward invariant assertions:
status correctness, persisted evidence, retry safety, provenance, and retrieval-smoke honesty.

Adoption status in repo truth:

- absorbed into concrete `tests/`: readiness predicate breadth, multi-document readiness scope, ready-chunk traceability, explicit unsupported PNG rejection, extract failure operator detail, and stale index-publication cleanup
- intentionally not adopted: helper import adapters, fake repositories, compatibility constructors, and duplicate lower-fidelity contract/persistence/stage tests already covered by the DB-backed suite
- bundle remains reference-only so future work can inspect the original invariant framing without coupling the active suite to its compatibility harness
