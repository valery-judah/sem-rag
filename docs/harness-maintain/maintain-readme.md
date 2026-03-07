# Maintaining `README.md` for the Common Harness

## Purpose of this document

This document explains how to maintain the top-level harness `README.md` as the **entry contract** for the operational harness.

It defines:

- what the common `README.md` is for,
- what goals it should achieve,
- what principles should shape its content,
- how to verify that it is doing its job,
- and how to maintain it without letting it drift into either under-specification or duplicated architecture detail.

This is a maintenance guide for the common harness `README.md`, not a full replacement for:

- `AGENTS.md`,
- the layer concept documents,
- the operational playbook,
- the workflow loop files,
- or the artifact templates.

---

## Core position

The common harness `README.md` should be treated as the **top-level operational entry point** into the harness.

It should not try to become:

- the full architecture specification,
- the full operational playbook,
- the full agent instruction set,
- or a giant restatement of every layer, workflow, and artifact in the harness.

Its role is narrower and more important:

> the `README.md` should make the harness legible, bounded, navigable, and operable at first contact.

A reader should be able to open the top-level `README.md` and quickly understand:

1. what this harness is for,
2. what conceptual model it uses,
3. what the minimum operating discipline is,
4. what artifacts matter,
5. where to go next,
6. and what failure modes to avoid.

If it succeeds at that, it is doing its job.

---

## Why the common `README.md` matters

The harness has many files:

- layer concept documents,
- per-mode references,
- workflow loops,
- policies,
- templates,
- schemas,
- prompts,
- live indexes,
- and live artifacts.

Without a strong top-level entry document, the harness becomes harder to enter, harder to route through, and easier to misuse.

The common `README.md` is therefore responsible for three kinds of first-order clarity:

1. **orientation clarity** — what this system is and how it is organized,
2. **operational clarity** — how work should move through it,
3. **routing clarity** — which document or loop to open next.

That makes the `README.md` an operational control surface, not just introductory prose.

---

## Primary goals of the common `README.md`

The top-level harness `README.md` should achieve the following goals.

### 1. Establish harness scope and boundaries

The file should explain what the harness is intended to do and what it is explicitly not intended to do.

It should make clear that the harness exists to make work:

- classifiable,
- routable,
- control-legible,
- resumable,
- reviewable,
- and maintainable across sessions.

It should also make clear that the harness is not:

- a giant workflow engine,
- a universal state machine,
- a replacement for judgment,
- a guarantee that every task needs a workstream,
- or a heavy project-management stack.

This boundary-setting is critical because it protects the harness from process inflation and conceptual drift.

### 2. Teach the core operating model in one pass

A reader should be able to understand the minimum layered operating model from the `README.md` alone.

At minimum, the file should orient the reader to:

- **Layer A** as classification of the current work slice,
- **Layer B** as the one current operating mode,
- **Layer C** as `feature_cell` / `control_profile` context applied only when justified,
- **Layer D** as lifecycle/control status.

It should also explain the default operational flow:

1. normalize work into a bounded slice,
2. classify the slice,
3. choose one current mode,
4. apply Layer C only when needed,
5. record Layer D plus `next_step`,
6. continue, pause, review, hand off, reroute, or close as required.

This is the minimum shared mental model required to operate inside the harness.

### 3. Route the reader to the correct next document

The top-level `README.md` should function as a router.

It should tell a reader where to go next depending on context, for example:

- new/raw work → intake loop,
- fresh agent with no selected task → active executable-task queue, then authoritative task card,
- existing actionable task → task execution loop,
- multi-slice coordinated effort → workstream loop,
- review/approval boundary → checkpoint-review loop,
- pause or transfer → handoff-resume loop,
- agent entering fresh → `AGENTS.md`.

The maintainer should treat this routing function as one of the most important jobs of the file.

### 4. Define the minimum operational surface

The `README.md` should name the smallest artifact set that makes the harness usable.

It should make clear:

- that the **task card** is the default authoritative operational artifact,
- that the **workstream card** is conditional and justified only when task-only tracking is no longer enough,
- that the **handoff note** is secondary and not authoritative,
- and that the workflow loops are the main operational procedures.

Without this, the harness becomes easy to misread as a loose note system rather than a small operational system.

### 5. Encode the minimum operating discipline

The `README.md` should define the high-level behavioral discipline that all other files assume.

This includes at least the following:

- always work on a bounded current slice,
- always choose exactly one current Layer B mode,
- keep Layer C sparse,
- treat Layer D as authoritative control status,
- always leave a concrete `next_step`,
- keep authoritative artifacts current.

This discipline should appear at the top-level because it is the behavioral contract for anyone entering the harness.

### 6. Protect the harness from predictable misuse

The `README.md` should explicitly warn against anti-patterns such as:

- turning the harness into a giant process layer,
- creating workstreams too early,
- allowing authoritative task cards to go stale,
- letting handoff notes replace primary artifacts,
- using custom states or blended modes,
- silently abandoning completed or cancelled work.

These warnings matter because the common failure modes of the harness are already known.

### 7. Support both human and agent entry

The file should help two kinds of readers:

- a human maintainer or operator,
- an agent entering the harness fresh.

That means the `README.md` should remain readable and compact enough for humans, while also being explicit enough to serve as the first file in the agent reading sequence.

---

## What the common `README.md` should not do

To keep the file healthy, maintainers should protect it from role drift.

The common `README.md` should not become any of the following.

### 1. A full restatement of every concept document

It should summarize the layered model, not duplicate the detailed specs for Layers A, B, C, and D.

### 2. A full operational playbook

It should define the minimum discipline and point to the workflow documents and playbook, not restate every procedure in detail.

### 3. A per-mode manual

It should explain that one current Layer B mode must be chosen and point to routing and per-mode documents when needed.

### 4. A policy dump

It should reference policies and constraints, but detailed routing logic and governance specifics should remain in the proper policy and concept files.

### 5. A duplicate of `AGENTS.md`

`README.md` is the entry contract. `AGENTS.md` is the direct operating instruction layer for the agent. The two should be aligned but not collapsed into one document.

### 6. A giant directory manifest with no operating guidance

A directory tree is useful, but only if it supports actual orientation and routing.

---

## Basic principles for maintaining the common `README.md`

The following principles should guide all changes to the file.

### 1. Entry-contract first

Maintain the `README.md` as the first-contact contract for operating the harness.

Ask:

- What does a fresh reader need to understand first?
- What is the smallest correct mental model?
- What is the next file they should open?

If a section does not help answer those questions, it may not belong in the `README.md`.

### 2. Slice-first orientation

The file should reinforce that the harness operates on **current slices of work**, not vague initiatives.

This is one of the central disciplines of the harness, and the `README.md` should keep it visible.

### 3. Exactly-one-mode discipline

The `README.md` should maintain the rule that a task slice has one current Layer B mode.

If a change to the README makes blended modes seem acceptable, that is a regression.

### 4. Sparse Layer C

The `README.md` should keep Layer C constrained to real control or organizational need.

It should not normalize the idea that every task should be wrapped in workstream or control-profile machinery.

### 5. Layer separation

The `README.md` should preserve the separation between:

- Layer A classification,
- Layer B current operating posture,
- Layer C `feature_cell` / `control_profile` context,
- Layer D control status.

Any wording that causes these layers to collapse into one another should be corrected.

### 6. Authoritative artifact discipline

The `README.md` should keep the task card and workstream card visibly authoritative.

It should not allow the operational truth to drift toward chat history, summaries, or handoff notes.

### 7. Concrete-next-step discipline

The `README.md` should reinforce that an active non-terminal item must expose one concrete next step.

This is essential for resumability and operational clarity.

### 8. Minimal viable process

The file should keep the harness lightweight.

It should encourage enough structure to preserve routing, resumability, and control truth, but not so much structure that the harness becomes ceremony-heavy.

### 9. Router-over-repetition

Whenever possible, the `README.md` should route to a more detailed file rather than duplicate it.

This keeps the document durable and reduces maintenance drift.

### 10. Operational truth over literary completeness

The `README.md` does not need to be exhaustive.

It needs to be correct, stable, and operationally useful.

---

## The practical role split between `README.md` and nearby documents

Maintainers should keep the role boundaries between files explicit.

### `README.md`

Use for:

- harness purpose,
- non-goals,
- top-level model,
- minimum artifact model,
- default operating sequence,
- entry routing,
- anti-patterns,
- reading paths.

### `AGENTS.md`

Use for:

- direct agent instructions,
- authoritative file order,
- required behavior when creating or updating artifacts,
- operating constraints,
- minimum field discipline,
- stopping and handoff behavior.

### `concepts/operational-playbook.md`

Use for:

- operational usage rules,
- maintenance cadence,
- review and approval handling,
- validation handling,
- reroute triggers,
- anti-patterns in actual operation.

### Layer concept documents

Use for:

- stable conceptual specification,
- scope and non-scope,
- separation between layers,
- schema-level or ontology-level details.

### Workflow files

Use for:

- procedural execution guidance for a specific operating loop.

### Templates and schemas

Use for:

- artifact structure and field-level requirements.

If the common `README.md` starts absorbing content from these files in detail, it is likely drifting past its role.

---

## How to tell whether the `README.md` is achieving its goals

The quality of the common `README.md` should not be judged only by prose quality.

It should be judged by whether it improves actual harness operation.

The following checks are the most important.

## 1. Orientation test

A fresh reader should be able to answer all of the following after reading only the top-level `README.md`:

- What is this harness for?
- What is it explicitly not for?
- What are Layers A, B, C, and D at a high level?
- What is the default flow for handling a work item?
- What are the minimum important artifacts?
- Which artifact is authoritative by default?
- When is a workstream justified?
- What document should I open next?

If the reader cannot answer these questions reliably, the `README.md` is not doing enough.

## 2. Routing test

A fresh reader should be able to choose the next correct file for common situations.

At minimum, they should be able to map:

- new task → intake loop,
- active task → task execution loop,
- coordinated multi-slice effort → workstream loop,
- review/approval pause → checkpoint-review loop,
- pause/transfer/resume → handoff-resume loop,
- fresh agent entry → `AGENTS.md`.

If they cannot route correctly from the `README.md`, the file is failing one of its core jobs.

## 3. Discipline test

After reading the `README.md`, a reader should understand these operational rules:

- work on a bounded slice,
- use one current mode,
- keep Layer C sparse,
- keep Layer D truthful,
- leave a concrete next step,
- keep authoritative artifacts current.

If those rules are not clear, the `README.md` is underspecified.

## 4. Artifact-authority test

A reader should clearly understand from the `README.md` that:

- task cards are the default authoritative operating artifact,
- workstream cards are conditional and justified only when needed,
- handoff notes are secondary resumability aids.

If the file leaves this ambiguous, the harness will drift.

## 5. Anti-pattern test

A reader should be able to tell which behaviors are explicitly wrong.

At minimum, the file should make the following clearly undesirable:

- stale authoritative cards,
- over-promotion into workstreams,
- local custom states,
- blended modes,
- vague `next_step`,
- silent abandonment of closed work,
- replacing cards with notes.

If a new maintainer can read the `README.md` and still think these are acceptable, the file is not protective enough.

## 6. Downstream artifact-health test

This is the strongest real-world test.

The `README.md` is healthy only if downstream operational artifacts tend to reflect its discipline.

A random sample of live task cards should usually show:

- a clear title,
- a bounded current slice,
- Layer A core present,
- exactly one `current_mode`,
- a truthful Layer D state,
- a concrete `next_step`,
- relevant references,
- current work log when appropriate.

A random sample of workstream cards should usually show:

- clear goal,
- scope boundary,
- promotion reason,
- current child-task structure,
- truthful workstream-level state,
- workstream-level `next_step`,
- current shared references or decisions.

If the artifacts are routinely missing these properties, the top-level `README.md` is not successfully establishing operational discipline.

---

## A compact acceptance rubric for the common `README.md`

Use the following rubric when reviewing or refactoring the file.

### A. Scope and identity

The file should clearly state:

- harness purpose,
- harness non-goals,
- why the harness exists,
- why it remains intentionally small.

### B. Layered model clarity

The file should clearly explain:

- what Layer A means,
- what Layer B means,
- what Layer C means,
- what Layer D means,
- how they relate in operation.

### C. Entry routing quality

The file should clearly tell the reader:

- where to start,
- what to read next,
- how to route based on operational situation.

### D. Artifact model clarity

The file should clearly identify:

- task card as default authoritative artifact,
- workstream card as conditional,
- handoff note as secondary,
- workflow loops as the main operating procedures.

### E. Discipline clarity

The file should clearly reinforce:

- slice-first work,
- one current mode,
- sparse Layer C,
- truthful Layer D,
- concrete `next_step`,
- current authoritative artifacts.

### F. Anti-pattern coverage

The file should clearly reject:

- giant-process drift,
- workstreams too early,
- stale cards,
- handoff-note primacy,
- blended modes,
- custom states,
- closure neglect.

### G. Maintainability of the README itself

The file should:

- avoid duplicating detailed concept specs,
- avoid duplicating detailed workflows,
- avoid duplicating the full agent instruction layer,
- prefer routing to deeper documents,
- remain compact enough to read first.

---

## Verification method for maintainers

When maintaining the common `README.md`, use the following verification sequence.

## Step 1. Read for first-contact usability

Pretend you are a fresh human or agent entering the harness.

Ask:

- Can I tell what this harness is?
- Can I tell what it is not?
- Can I tell what to do next?
- Can I tell what artifact matters?
- Can I tell how work flows through the harness?

If not, improve entry clarity before doing anything else.

## Step 2. Read for role drift

Ask whether sections have drifted into content that belongs elsewhere.

Typical signs of drift:

- long detailed policy logic,
- per-mode operational nuance,
- schema-heavy detail,
- full workflow procedures,
- repeated content copied from `AGENTS.md` or the playbook.

If the content is detailed enough that a deeper file should own it, compress it and route to the deeper file instead.

## Step 3. Read for layer integrity

Check whether the wording preserves the separation between:

- classification,
- current posture,
- `feature_cell` / `control_profile` context,
- lifecycle/control state.

If the wording collapses those together, fix it.

## Step 4. Read for operational discipline

Check whether the top-level rules are visible enough.

A maintainer should be able to point directly to the part of the `README.md` that teaches:

- work on a slice,
- choose one mode,
- apply Layer C only if justified,
- keep Layer D truthful,
- leave a concrete next step,
- keep the authoritative card current.

## Step 5. Run the routing scenarios

Test the README against these scenario prompts:

- “I just received a raw task.”
- “A task card already exists and work can continue.”
- “This effort now spans multiple coherent slices.”
- “Work paused at review or approval.”
- “I am resuming after a pause.”
- “I am an agent entering this harness fresh.”

The `README.md` should make the next document obvious in each case.

## Step 6. Sample live artifacts

Review a small sample of active task cards and workstream cards.

Ask whether the operational artifacts reflect the discipline the `README.md` claims to establish.

If not, either:

- the `README.md` is not clear enough,
- nearby documents are inconsistent,
- or enforcement is missing.

## Step 7. Check anti-pattern resistance

Inspect whether actual harness usage is showing the known failure modes.

If those failure modes appear repeatedly, strengthen the relevant top-level warnings or routing guidance.

---

## Observable signs that the `README.md` is working

The common `README.md` is probably healthy when most of the following are true:

- fresh readers route to the correct workflow file without confusion,
- agents reliably open `AGENTS.md` after the top-level `README.md`,
- task cards are usually present for non-trivial work,
- task cards generally remain the primary source of truth,
- workstreams are used selectively rather than by default,
- mode selection usually remains singular,
- custom states are rare or absent,
- active artifacts usually have specific `next_step` values,
- paused or transferred work is resumable without relying on chat memory,
- completed and cancelled items are explicitly closed.

---

## Observable signs that the `README.md` is failing

The common `README.md` likely needs refactoring when one or more of the following occur repeatedly:

### 1. Readers do not know where to start

This usually means routing guidance is too weak or too buried.

### 2. People treat the harness as a note pile

This usually means authoritative artifacts and minimum discipline are not stated strongly enough.

### 3. Workstreams appear by default

This usually means the README is not protecting task-first operation strongly enough.

### 4. Blended modes or custom states appear

This usually means the README is not clearly enough reinforcing layer separation and the one-mode rule.

### 5. Handoff notes become more accurate than cards

This usually means artifact authority has become ambiguous.

### 6. Active items have vague next steps

This usually means the operational discipline is not visible enough.

### 7. The README becomes long but less useful

This usually means it is duplicating deeper files instead of routing to them.

---

## Maintenance rules for future edits

When editing the common `README.md`, use these rules.

### Rule 1. Preserve the top-level operating contract

Do not remove or weaken the sections that define:

- purpose,
- non-goals,
- layer model,
- core operating idea,
- start-here routing,
- artifact model,
- operating discipline,
- anti-patterns.

### Rule 2. Prefer summary plus pointer over duplication

When deeper detail is needed, summarize it briefly and point to the owning file.

### Rule 3. Keep the file readable in one sitting

A maintainer or agent should be able to read the file at the start of a session without it feeling like a full manual.

### Rule 4. Keep operational language concrete

Avoid vague statements like:

- “manage work effectively,”
- “keep things organized,”
- “use the harness consistently.”

Prefer specific statements about:

- slices,
- modes,
- Layer C application,
- Layer D truth,
- authoritative artifacts,
- and concrete `next_step`.

### Rule 5. Do not hide core discipline in footnotes

The most important behavioral rules should be visible in the main body of the file.

### Rule 6. Keep reading paths current

If the harness tree or workflow structure changes, update the reading and routing sections immediately.

### Rule 7. Keep examples minimal and selective

The README may include small examples or scenario cues, but deeper examples should live elsewhere.

### Rule 8. Maintain alignment with `AGENTS.md`

The `README.md` and `AGENTS.md` should not contradict each other.

The top-level file should define the contract; `AGENTS.md` should operationalize it.

---

## Suggested review checklist for README maintenance

Use this checklist during review.

- Does the file still define the harness purpose and non-goals clearly?
- Does it still explain the layered model at the right level?
- Does it still teach the default operating sequence?
- Does it still identify the authoritative artifacts correctly?
- Does it still say when to create a workstream and when not to?
- Does it still route clearly to the workflow files?
- Does it still tell agents to read `AGENTS.md` next?
- Does it still reinforce slice-first work and exactly one mode?
- Does it still keep Layer C sparse and Layer D authoritative?
- Does it still require a concrete `next_step`?
- Does it still reject custom states and blended modes?
- Does it still reject stale cards and handoff-note primacy?
- Has it accidentally duplicated content that belongs in a deeper file?
- Can a fresh reader still use it quickly?

---

## Recommended periodic verification cadence

A lightweight cadence is enough.

### After structural harness changes

Review the `README.md` whenever one of the following changes materially:

- harness tree,
- workflow set,
- artifact model,
- layer boundaries,
- workstream justification rules,
- routing policy entry points,
- authoritative-file order.

### After repeated operator confusion

Review the `README.md` when you observe repeated confusion such as:

- wrong workflow opened first,
- workstream overuse,
- mode-selection mistakes,
- state misuse,
- stale cards,
- resumability failures.

### During periodic harness hygiene

Use a small periodic review to sample whether the file is still producing the intended downstream behavior.

---

## Practical heuristic

A strong top-level `README.md` should let a fresh reader answer these questions quickly:

1. What is the current kind of system I am entering?
2. How is work represented here?
3. What is the minimum model I need to hold in my head?
4. Which artifact is authoritative?
5. Which workflow file should I open next?
6. What mistakes should I avoid?

If the file supports those answers, it is likely healthy.

---

## Bottom line

The common harness `README.md` should be maintained as the **entry contract and routing surface** for the harness.

Its job is not to contain everything.
Its job is to make the rest of the harness usable.

A good common `README.md`:

- defines the harness boundary,
- teaches the minimum operating model,
- names the key artifacts,
- routes the reader to the correct next file,
- encodes the basic discipline,
- and blocks the most common forms of harness drift.

The strongest verification is not literary elegance.
The strongest verification is whether readers and agents actually enter the harness correctly and whether live artifacts reflect the discipline the `README.md` claims to establish.

---

## Source anchors used for this maintenance reasoning

Primary source files in the harness:

- `README.md`
- `AGENTS.md`
- `concepts/operational-playbook.md`
- `concepts/layer-b-operating-modes.md`

These sources collectively establish:

- harness purpose and non-goals,
- top-level layer model,
- minimum operating sequence,
- artifact authority,
- task-first versus workstream-later behavior,
- anti-patterns,
- maintenance discipline,
- and the five-question harness-health heuristic.


# Specific structure and reasoning

Given the harness principles, I would structure `README.md` as an **entry-and-routing document**, not as a second playbook or a mini-spec for every layer. Its job is to make the harness easy to enter, easy to route through, and hard to misuse. The current docs already imply that separation: the README should explain the harness operationally, while deeper semantics live in `concepts/`, detailed agent behavior lives in `AGENTS.md`, and step-by-step execution logic lives in `workflows/`.   

I would outline it like this.

## 1. Title and one-paragraph purpose

Start with the name of the harness and a compact statement of what it is for. This section should answer: why does this directory exist, what problem does it solve, and what operating qualities it is trying to preserve. The current README already has the right framing: the harness exists to make work classifiable, routable, control-legible, resumable, reviewable, and maintainable across sessions, while remaining smaller than a full PM system. 

## 2. What this harness is

This should explain the operating surface at a high level: conceptual model, workflow loops, templates, policies, live state, prompts. It should also introduce the Layer A–D stack in one screen, but only at summary level. The purpose here is orientation, not full architecture teaching. 

## 3. What this harness is not

This section is important enough to keep near the top. It prevents drift into a giant workflow engine, universal state machine, or heavy PM framework. It also anchors the “small task, small harness” rule, which is one of the strongest design constraints in the current docs. 

## 4. Core operating idea

This is the conceptual center of the README. It should state the slice-first model and the minimal loop:

* normalize incoming work into a current slice,
* classify with Layer A,
* choose exactly one current Layer B mode,
* apply Layer C only if needed,
* set Layer D and `next_step`,
* execute or pause at the real boundary,
* reroute, reslice, hand off, or close as needed. 

I would keep this section concise, because the playbook already owns the full operational sequence. The README should expose the loop, not duplicate the whole loop spec. 

## 5. The five operating questions

This should probably become an explicit section rather than being buried near the end. It is the cleanest expression of the whole model:

1. What is the current slice?
2. How should the agent work now?
3. Does Layer C materially apply?
4. What is the current control status?
5. What is the next executable step?

The playbook says these five questions map directly to Layers A–D plus `next_step`, and both README and AGENTS use essentially the same shorthand. This is the best compact mental model for fresh entrants.   

## 6. Start here

This should remain early. It is the routing section for common entry paths:

* read `README.md`,
* read `AGENTS.md`,
* choose the relevant workflow based on whether the work is new, active, in workstream coordination, at checkpoint, or in handoff/resume. 

This is one of the main reasons the README exists at all. A reader should be able to enter the harness without guessing which doc to open next.

## 7. Minimum operational artifacts

This section should stay prominent and fairly concrete. It should define the minimal artifact set and their authority:

* task card as the default authoritative record,
* workstream card only when a `feature_cell` is justified,
* handoff note as secondary resumability aid, never the source of truth. 

This matters because context management for agents depends on artifact authority, not on chat memory. `AGENTS.md` reinforces that authoritative cards must stay current and more accurate than handoff notes. 

## 8. Default operating sequence for new work

Include a compact operational sequence for first contact with a task:

* inbox if needed,
* intake loop,
* create task card,
* fill Layer A core,
* choose one Layer B mode,
* apply Layer C only if justified,
* set Layer D and `next_step`,
* continue via the next appropriate loop.  

This section should be brief and procedural. The playbook owns the detailed version.

## 9. When to create a workstream

This deserves its own section because it is one of the main places where harnesses overcomplicate themselves. The README should say clearly that task-level tracking is the default and that `feature_cell` is only for real long-horizon multi-slice coordination, such as multiple child tasks, high handoff pressure, milestone needs, or likely mode changes across time.   

## 10. Routing guidance

This should explain the routing discipline in summary form:

* use one current atomic mode,
* use routing rules rather than improvised labels,
* do not use blended modes,
* when no mode clearly dominates, reslice.   

The README should not restate every mode in depth. The detailed semantics belong in `layer-b-operating-modes.md` and `policies/routing-rules.md`. 

## 11. Control and state guidance

A short section should explain two things:

* Layer C modifies or wraps work; it is not a status model.
* Layer D is the authoritative control plane; it answers whether work can proceed, is blocked, paused for review, awaiting approval, validating, or done.  

This is a high-value section because context drift often happens when people mix mode, control profile, and state into one blob.

## 12. Reading paths

Keep separate reading paths for humans and agents. The current README already has the correct idea:

* humans maintaining the harness should go README → playbook → concepts → workflows → templates → routing rules,
* agents entering fresh should go README → AGENTS → relevant workflow → relevant template → routing rules when mode selection is needed. 

This is directly about context building and management. It gives different consumers the smallest sufficient context rather than dumping the entire tree on them.

## 13. Anti-patterns

This should stay in the README. It is part of entry discipline, not just maintenance guidance. The current anti-pattern set is strong and should likely remain:

* treating the harness as ceremony,
* creating workstreams too early,
* letting the task card go stale,
* letting handoff notes replace authoritative cards,
* using custom states or blended modes,
* forgetting closure. 

These are exactly the failure modes that degrade agent context quality over time.

## 14. Practical rule of thumb

End with the five-question check. It is the best operational health heuristic in the current material. If the artifacts make those answers obvious, the harness is working. 

## 15. Current status and maintenance guidance

I would keep this at the end. It should say the harness is intentionally minimal, what it currently does not require yet, and how to evolve it without ontology bloat: improve slicing, tighten templates and workflow docs, prefer explicit rules over new abstract categories, and keep the artifact set small and maintained. 

---

If I compress that into a recommended final outline, it would look like this:

1. `# Operational Harness`
2. Purpose
3. What this harness is
4. What this harness is not
5. Core operating idea
6. Five operating questions
7. Start here
8. Minimum operational artifacts
9. Default operating sequence for new work
10. When to create a workstream
11. Routing guidance
12. Control and state guidance
13. Reading path for humans
14. Reading path for agents
15. Anti-patterns
16. Practical rule of thumb
17. Current status of the harness
18. Maintenance guidance

My main recommendation is structural: move the **five operating questions** much earlier and make them part of the README’s central framing. They are the cleanest bridge between context modeling and operational use. Right now they are effectively the best summary of the harness, and they deserve to function as the README’s backbone rather than as a closing note.  

