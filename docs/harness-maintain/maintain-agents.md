# Maintaining `AGENTS.md` for the Common Harness

## Purpose of this document

This document explains how to maintain `AGENTS.md` as the **direct execution contract** for an agent operating inside the harness.

It defines:

- what `AGENTS.md` is for,
- what goals it should achieve,
- what principles should shape its content,
- how to verify that it is doing its job,
- and how to evolve it without collapsing it into the `README.md`, the operational playbook, or the workflow files.

This is a maintenance guide for `AGENTS.md`, not a replacement for:

- the top-level `README.md`,
- the layer concept documents,
- `concepts/operational-playbook.md`,
- the workflow loop documents,
- the routing policy,
- or the artifact templates.

---

## Core position

`AGENTS.md` should be treated as the **direct operating instruction layer for the agent**.

The top-level `README.md` explains how to enter the harness and what the harness is for.

`AGENTS.md` explains how an agent should behave once inside it.

Its role is therefore narrower than the playbook, but more prescriptive than the README:

> `AGENTS.md` should convert the harness operating model into explicit agent behavior.

A correctly maintained `AGENTS.md` should let an agent determine, with minimal improvisation:

1. what sources of authority apply,
2. how to handle new work,
3. how to continue existing work,
4. how to behave at review, approval, checkpoint, and blocker boundaries,
5. how to keep operational artifacts trustworthy,
6. and how to stop or hand off work without breaking resumability.

If an agent still needs to invent basic operating behavior after reading `AGENTS.md`, the document is under-specified.

---

## Why `AGENTS.md` matters

The harness contains many concept documents, workflow loops, templates, policies, and live artifacts.

Those materials are necessary, but they do not by themselves guarantee that an agent will behave consistently.

`AGENTS.md` matters because it turns the harness from a collection of documents into a usable operating discipline.

It provides five kinds of operational clarity:

1. **authority clarity** — what document or artifact is authoritative when sources differ,
2. **behavior clarity** — how the agent should act in common situations,
3. **routing clarity** — how to choose one current mode and when to reslice,
4. **control clarity** — how to respect Layer D boundaries and stop conditions,
5. **artifact clarity** — what minimum fields and updates keep the harness trustworthy.

Without a strong `AGENTS.md`, the harness tends to fail in predictable ways:

- the agent improvises its own routing rules,
- handoff notes become more accurate than task cards,
- Layer D stops being authoritative,
- workstreams get created too early,
- blended modes appear,
- and resumability degrades.

That makes `AGENTS.md` a control document, not just a convenience note.

---

## Primary goals of `AGENTS.md`

The file should achieve the following goals.

### 1. Convert the abstract harness model into executable agent behavior

The harness architecture is distributed across layers, workflows, templates, and policies.

`AGENTS.md` should convert that structure into direct instructions the agent can follow while working.

At minimum, the file should tell the agent to:

- work on the **current slice**,
- choose exactly **one current Layer B mode**,
- apply Layer C only when justified,
- treat Layer D as the current control truth,
- maintain authoritative artifacts,
- and leave one concrete `next_step`.

This is the bridge from conceptual architecture to actual operation.

### 2. Establish authority and precedence

`AGENTS.md` should make it clear what the agent must trust first.

A healthy version should explicitly define precedence among:

- the top-level harness `README.md`,
- `AGENTS.md` itself,
- the relevant workflow file,
- the relevant template,
- the routing policy,
- and the current live task/workstream artifacts.

It should also clarify that:

- task cards and workstream cards are authoritative operational records,
- handoff notes are secondary resumability aids,
- and chat memory is not the operational source of truth.

### 3. Force disciplined routing behavior

`AGENTS.md` should require the agent to choose one current mode based on the current slice and current `next_step`.

It should make clear that:

- blended modes are not allowed,
- route choice should follow the canonical routing policy,
- and when no single mode fits, the correct response is usually to **reslice**, not to invent a hybrid label.

### 4. Force disciplined control behavior

The file should make Layer D operationally binding.

It should require the agent to ask before acting:

- what the current Layer D state is,
- whether that state permits the intended action,
- whether the item is actually blocked, at checkpoint, awaiting approval, validating, or active,
- and what concrete `next_step` should remain afterward.

This is the core mechanism that prevents agents from pushing through real boundaries.

### 5. Standardize agent behavior at operational boundaries

`AGENTS.md` should define required behavior for common harness situations, including:

- new work,
- active tasks,
- workstreams,
- review or approval boundaries,
- handoff,
- and resume.

This matters because the harness is designed for long-lived and interruptible work.

The agent should not need to invent its own lifecycle logic for these situations.

### 6. Define the minimum quality bar for live artifacts

`AGENTS.md` should make it explicit when a task or workstream artifact is not good enough to operate from.

For tasks, the minimum bar should include at least:

- meaningful title,
- current slice summary,
- Layer A core,
- exactly one current mode,
- truthful Layer D state,
- concrete `next_step`,
- relevant references,
- and current work log when progress has occurred.

For workstreams, the minimum bar should include at least:

- workstream title,
- clear goal,
- scope boundary,
- promotion reason,
- child task structure,
- truthful workstream state,
- workstream-level `next_step`,
- and current shared references or decisions when relevant.

### 7. Protect the harness from predictable agent failure modes

`AGENTS.md` should explicitly guard against known operational failures such as:

- stale authoritative cards,
- premature workstream creation,
- blended modes,
- custom lifecycle states,
- continuing through blocked/checkpoint/approval boundaries,
- leaving terminal work unclosed,
- and letting note piles replace structured artifacts.

The file should treat these as first-class anti-patterns, not as incidental warnings.

### 8. Preserve resumability under interruption

The harness assumes work may pause, transfer, or resume later.

`AGENTS.md` should therefore make resumability a direct behavioral requirement by forcing the agent to:

- update authoritative cards before stopping,
- preserve the exact current control condition,
- expose the smallest useful set of linked artifacts,
- and leave one concrete next move for the next operator.

---

## Relationship of `AGENTS.md` to the rest of the harness

Maintainers should preserve a clean division of labor across the harness.

### `README.md`

The `README.md` explains the harness as a system:

- purpose,
- boundaries,
- layer model,
- minimum artifacts,
- and where to go next.

### `AGENTS.md`

`AGENTS.md` tells the agent how to behave inside that system.

### `operational-playbook.md`

The playbook explains the durable operational logic behind slicing, classification, routing, control handling, workstream use, validation handling, review handling, and maintenance rhythm.

### Workflow files

Workflow files define the step-by-step procedures for concrete operational situations.

### Templates

Templates define the structure of the artifacts being created or updated.

### Policies

Policies, especially routing rules, define canonical decision logic that the agent should use instead of improvising local conventions.

A healthy `AGENTS.md` should sit in the middle of those materials:

- more specific than the README,
- less expansive than the playbook,
- more behavioral than the templates,
- and more general than any single workflow file.

---

## What `AGENTS.md` should not do

To keep the file healthy, maintainers should actively protect it from role drift.

### 1. It should not become a second `README.md`

It should not re-explain the entire harness from first principles.

It should assume the reader has already been routed in through the top-level README.

### 2. It should not become a full operational playbook

It should define direct operating rules, not restate every conceptual argument and procedure from the playbook.

### 3. It should not become a full routing manual

It should instruct the agent to use the routing policy and the mode references rather than embedding detailed routing theory inline.

### 4. It should not duplicate every workflow file

It should define behavioral expectations for key situations, but detailed step sequences should remain in the workflow documents.

### 5. It should not become a policy graveyard

Long policy reasoning, edge-case governance detail, and special-case exceptions should remain in policy and concept documents unless they materially change agent behavior everywhere.

### 6. It should not carry local ontology experiments

Do not add ad hoc state names, blended modes, special pseudo-layers, or one-off universal concepts into `AGENTS.md` because a single task felt awkward.

When a slice is awkward, the first fixes should usually be:

- improve slicing,
- improve the workflow file,
- improve the template,
- improve the routing note,
- or improve the explanatory concept document.

---

## Basic principles for maintaining `AGENTS.md`

The following principles should guide all changes to the file.

### 1. Behavior-first, not explanation-first

Every major section should answer the question:

> What should the agent do?

Explanatory context is useful, but only insofar as it sharpens operational behavior.

### 2. Preserve authority discipline

The file should help the agent know which source to trust and when.

That means preserving clear statements about:

- authority order,
- artifact primacy,
- and the secondary status of handoff notes.

### 3. Preserve slice-first operation

The file should continue to reinforce that the harness operates on **current slices**, not on vague entire initiatives.

Any edits that make it easier for agents to operate on broad, ambiguous scopes should be treated as regressions.

### 4. Preserve one-current-mode discipline

The file should keep the rule that exactly one Layer B mode is current for a task slice.

When this becomes difficult, the default correction should remain reslicing or rerouting.

### 5. Preserve sparse Layer C usage

`AGENTS.md` should continue to make Layer C exceptional rather than default.

Use `feature_cell` only when workstream coordination is actually needed.

Use non-baseline `control_profile` only when explicit control obligations differ from the default regime.

### 6. Preserve Layer D as binding control truth

The file should make it hard for the agent to ignore blockers, checkpoints, approvals, and validation boundaries.

Any edits that weaken Layer D discipline should be treated as serious regressions.

### 7. Preserve concrete next-step quality

The file should continue to reject vague continuation language.

A strong `next_step` is one of the harness's primary mechanisms for resumability and operability.

### 8. Preserve artifact truthfulness

The file should keep authoritative cards more current than chat or handoff notes.

If edits make it easier to work from stale cards, the harness becomes untrustworthy.

### 9. Preserve minimality

`AGENTS.md` should stay compact enough that an agent can actually use it as a live operating instruction document.

If it becomes a giant essay, it stops working as an execution contract.

### 10. Prefer stable behavioral rules over proliferating exceptions

When new complexity appears, prefer a small number of robust operational rules over a growing set of special-case carve-outs.

---

## How to verify that `AGENTS.md` is doing its job

Verification should happen at three levels:

1. **document-level verification**,
2. **artifact-level verification**,
3. **behavior-level verification**.

### 1. Document-level verification

A fresh agent should be able to read `README.md`, then `AGENTS.md`, and determine without major guessing:

- what the authority order is,
- how to start new work,
- how to continue existing work,
- when to create a workstream,
- how to behave at review or approval boundaries,
- how to stop or hand off cleanly,
- what makes a task usable,
- and what makes a workstream usable.

If those answers are not explicit, `AGENTS.md` is incomplete.

#### Document-level acceptance questions

Use these questions as a check.

1. Does the file clearly define what the agent should trust first?
2. Does it clearly define how new work enters the harness?
3. Does it clearly define how an existing task should be continued?
4. Does it clearly define when workstream-level handling is justified?
5. Does it clearly define how Layer D boundaries affect action?
6. Does it clearly define handoff and resume behavior?
7. Does it clearly define minimum task quality?
8. Does it clearly define minimum workstream quality?
9. Does it clearly define anti-patterns?
10. Does it clearly define what to do when uncertain?

If several of these questions require inference from other files rather than direct reading, the document likely needs tightening.

### 2. Artifact-level verification

The strongest proof that `AGENTS.md` works is that live artifacts actually follow it.

A healthy sample of active task cards should show:

- one bounded current slice,
- exactly one current mode,
- truthful Layer D state,
- concrete `next_step`,
- current references,
- and a meaningful current work log when progress happened.

A healthy sample of workstream cards should show:

- a coherent shared goal,
- clear scope boundary,
- explicit promotion reason,
- current child structure,
- truthful workstream state,
- current workstream-level `next_step`,
- and current shared references or decisions.

If the live artifacts repeatedly fail these checks, `AGENTS.md` is not succeeding operationally, even if the prose seems fine.

#### Artifact-quality audit checklist

For tasks, ask:

- Is the title meaningful?
- Is the current slice explicit?
- Is the Layer A core present?
- Is there exactly one current mode?
- Is the Layer D state believable?
- Is the `next_step` concrete?
- Are relevant refs discoverable?
- Does the work log reflect real progress?

For workstreams, ask:

- Is there a real shared goal?
- Is the scope boundary explicit?
- Is promotion actually justified?
- Are child tasks visible?
- Is workstream state truthful?
- Is the workstream next step concrete?
- Are shared refs and decisions current?

### 3. Behavior-level verification

The most important question is whether agent behavior improves after following the document.

A healthy `AGENTS.md` should reduce the frequency of:

- blended modes,
- custom states,
- stale cards,
- premature workstream promotion,
- continuing through real boundaries,
- vague `next_step` values,
- handoff notes that outstrip the authoritative cards,
- and terminal work left unclosed.

#### Behavioral anti-pattern audit

Use the following failure list as an operational audit.

- **Dumping-ground behavior** — vague notes accumulate but control fields are not maintained.
- **Premature workstream inflation** — `feature_cell` is created because work sounds important, not because coordination pressure exists.
- **Card staleness** — the authoritative card does not reflect the true current state.
- **Boundary violation** — implementation or migration continues through `blocked`, `checkpoint`, or `awaiting_approval`.
- **Ontology drift** — agents introduce new state names, blended modes, or ad hoc universal concepts.
- **Closure failure** — completed or cancelled work remains live without closure context.

If these failures persist, the maintainer should assume either:

- `AGENTS.md` is unclear,
- the related workflow files are insufficient,
- the templates are too weak,
- or the routing/control rules are not well aligned.

---

## The five-question health test

`AGENTS.md` should preserve a compact operational health rule.

For any live item, an agent or reviewer should be able to answer:

1. What is the current slice or effort?
2. What is the current control state?
3. What is the one current mode?
4. Is there a real review, approval, or workstream-control boundary?
5. What is the concrete next step?

If those five answers are clear from the artifacts, the harness is healthy.

This is the best compact acceptance test for `AGENTS.md` because it captures the file's real job:

- preserve slice clarity,
- preserve control clarity,
- preserve routing clarity,
- preserve boundary clarity,
- and preserve action clarity.

---

## Practical maintenance checklist for `AGENTS.md`

When editing or reviewing the file, use this checklist.

### Structure and role

- Does the file still read like a direct operating contract?
- Is it clearly distinct from the top-level `README.md`?
- Is it clearly distinct from the operational playbook?
- Does it remain compact enough to be read early in an agent session?

### Authority and artifacts

- Does the authority order remain explicit?
- Does the file preserve the primacy of task/workstream cards?
- Does it keep handoff notes secondary?
- Does it require authoritative artifacts to be updated before stopping?

### Routing discipline

- Does the file still require one current mode?
- Does it still direct the agent to use routing rules rather than local improvisation?
- Does it still push awkward slices toward reslicing rather than hybrid labels?

### Control discipline

- Does the file still make Layer D binding?
- Does it still prevent work through real blockers, checkpoints, and approval gates?
- Does it keep `next_step` quality concrete and action-oriented?

### Workstream discipline

- Does it still prevent premature workstream creation?
- Does it still keep `feature_cell` as a workstream wrapper rather than a mode or state?
- Does it still treat workstream cards as coordination wrappers rather than mega-tasks?

### Resumability

- Does it still require strong handoff behavior?
- Does it still preserve exact current control condition?
- Does it still require the smallest useful linked artifact set?
- Does it still leave one concrete next step for the next operator?

### Anti-pattern resistance

- Does the file still name the main known failure modes?
- Are the anti-patterns still aligned with current harness structure?
- Did any new concept accidentally weaken the anti-pattern barriers?

---

## Signals that `AGENTS.md` needs refactoring

The file should be revised when one or more of the following happens.

### 1. Agents repeatedly mis-handle the same boundary

Examples:

- pushing through checkpoint,
- treating approval-bearing controls as equivalent to `awaiting_approval`,
- or continuing work when the true state is blocked.

This usually means the control instructions need sharpening.

### 2. Agents repeatedly choose blended or unstable modes

This usually means either:

- the routing guidance is not clear enough,
- the file does not emphasize reslicing strongly enough,
- or the relevant workflow files need better links.

### 3. Workstreams are being over-created or under-used

If agents frequently create workstreams too early, or fail to create them when coordination pressure is real, the workstream instructions need to be revised.

### 4. Handoff quality is weak even when agents follow the file

If resumability remains poor, the handoff rules or minimum artifact expectations probably need refinement.

### 5. The document starts duplicating other documents

If `AGENTS.md` begins to absorb too much of the playbook, templates, or README, it should be cut back to its core behavioral role.

### 6. New harness structure changes agent behavior materially

When the harness evolves in ways that alter actual agent behavior, `AGENTS.md` should be updated.

Examples:

- a new workflow loop becomes standard,
- a template changes what is minimally required,
- routing rules change materially,
- or workstream/control semantics are tightened.

---

## Recommended maintenance rhythm

`AGENTS.md` should be reviewed whenever one of the following occurs:

- the top-level `README.md` changes its operating model,
- the operational playbook changes core discipline,
- the routing rules change materially,
- a workflow loop is added or heavily revised,
- the task/workstream templates change required fields,
- or repeated agent errors reveal an ambiguous instruction.

A light review can use these questions:

1. Are agents still entering the harness correctly?
2. Are fresh agents discovering work through the executable queue before execution?
3. Are they updating authoritative artifacts first?
4. Are they using one current mode reliably?
5. Are they respecting Layer D boundaries?
6. Are handoffs preserving resumability?
7. Are known anti-patterns increasing or decreasing?

The goal is not ceremony.

The goal is to ensure that `AGENTS.md` still changes behavior in the intended direction.

---

## Change policy for maintainers

When revising `AGENTS.md`, prefer the following order of correction.

### 1. Clarify behavior before adding concepts

If agents are confused, first try to sharpen the instruction.

Do not immediately add new ontology.

### 2. Improve references before adding duplication

If the file depends on routing rules, templates, or workflows, strengthen the reference path rather than copying those files into `AGENTS.md`.

### 3. Fix common failure points explicitly

If one operational mistake keeps recurring, it is usually worth naming directly.

### 4. Keep examples short and behavioral

If examples are added, they should sharpen action quality, not bloat the file.

### 5. Favor stable cross-task rules

A rule belongs in `AGENTS.md` only if it should guide behavior across many tasks, not just one awkward case.

---

## Summary

`AGENTS.md` should be maintained as the **direct execution contract** for agents operating inside the harness.

It is doing its job when it makes agent behavior more:

- disciplined,
- predictable,
- resumable,
- boundary-aware,
- and artifact-driven.

It is failing when agents still need to improvise the basics of:

- what to trust,
- how to route,
- when to stop,
- how to record state,
- how to hand off,
- and how to keep the harness trustworthy.

In practical terms:

- the top-level `README.md` should make the harness easy to enter,
- `AGENTS.md` should make the harness hard to misuse.

That is the standard to maintain.


# Principles

Yes. I’d design `AGENTS.md` as the **agent execution contract** for the harness: short, prescriptive, and operational. It should tell an agent how to behave inside the harness, not re-explain the full architecture. That boundary is already implicit in the docs: `README.md` is the entry/orientation surface, while the playbook owns the full operational model and loops. `AGENTS.md` should sit between them and translate the model into direct agent behavior.  

## Design principles for `AGENTS.md`

The first principle is **execution over explanation**.
`AGENTS.md` should answer “what must the agent do now?” not “what does the architecture mean in theory?” The playbook already carries the fuller explanations, design goals, and layer semantics. 

The second is **artifact-first operation**.
The current AGENTS file is right to make authoritative artifacts primary and handoff notes secondary. That should remain central: the agent operates from the task/workstream card, not from memory or chat history. 

The third is **one stable operational invariant per rule**.
The strongest rules in the current file are the right backbone: current slice, one current mode, sparse Layer C, truthful Layer D, concrete `next_step`, current authoritative artifact. Those are the durable invariants the agent must preserve. 

The fourth is **minimal duplication of canonical vocabularies**.
The playbook already says routing policy is canonical in `routing-rules.md`, and it explicitly warns against turning the harness into a second taxonomy. So `AGENTS.md` should not try to become a duplicate mode manual, duplicate Layer D spec, or duplicate template schema. It should point to the canonical source when the full vocabulary matters.   

The fifth is **boundary fidelity**.
The agent must stop at real control boundaries. The current AGENTS file and playbook are aligned on this: do not continue through `blocked`, `checkpoint`, or `awaiting_approval`; repair the artifact or route into the correct loop instead.   

The sixth is **resumability as a first-class requirement**.
The playbook defines resumability and handoff as a main design goal, and the AGENTS file already reflects that. The final design should keep that strong: another agent should be able to resume from the maintained artifacts with minimal reconstruction.  

The seventh is **task-first, workstream-later**.
`feature_cell` should remain an escalation, not a default. The playbook and `feature-cell.md` are explicit that the workstream wrapper exists only when multi-slice coordination, resumability pressure, or workstream-level visibility/control is actually needed.  

## What `AGENTS.md` should contain

I would structure it like this.

### 1. Title and role

A short opening defining the file as the direct operating instructions for agents working inside the harness, read after `README.md` and before touching live artifacts. The current AGENTS opening is correct and should remain. 

### 2. What this file does and does not do

A compact boundary section:

* this file defines agent behavior inside the harness,
* it does not redefine the layers,
* it does not replace workflows, routing rules, registries, or schemas,
* it does not authorize inventing local ontology.

This is consistent with the current “do not improvise a new workflow ontology” rule and with the playbook’s non-goals.  

### 3. Authority order and context loading order

This should stay near the top. It is one of the most important parts of the file. The agent needs to know what to read first and what is authoritative when there is tension:

* `README.md`
* `AGENTS.md`
* relevant workflow
* relevant template
* routing rules when mode choice is involved
* current authoritative task/workstream artifact
* supporting notes and packets after that

The current AGENTS file already has the right idea, though it should be aligned to the current directory layout. 

### 4. Core invariants

This should be the conceptual backbone of the file, written as non-negotiable rules:

* operate on a current bounded slice,
* choose exactly one current Layer B mode,
* apply Layer C only when it materially changes organization or control,
* treat Layer D as authoritative control status,
* always leave one concrete `next_step`,
* keep authoritative artifacts current. 

I would keep these six as the center of the document.

### 5. Default agent loop

Instead of many prose sections, `AGENTS.md` should contain one short executable loop:

1. read current authoritative artifact, or intake the raw request if none exists;
2. bound the current slice;
3. verify Layer A core is present or repair it;
4. verify one current Layer B mode;
5. verify Layer C only where justified;
6. verify Layer D and `next_step`;
7. act only if the current state permits it;
8. update artifact at the boundary;
9. reroute, reslice, hand off, or close when needed.

That loop is directly derived from the playbook’s minimal operating loop. 

### 6. Workflow routing by situation

Then a short section that maps common situations to workflow files:

* new/raw work → intake loop,
* actionable task → task execution loop,
* coordinated multi-slice effort → workstream loop,
* review/approval boundary → checkpoint-review loop,
* pause/transfer/resume → handoff-resume loop.  

This section should be brief. It is a routing surface, not a workflow restatement.

### 7. Artifact rules

A short operational section should define:

* task card is the default authoritative record,
* workstream card exists only when `feature_cell` is justified,
* handoff note is secondary,
* update authoritative card before stop/handoff/reroute,
* do not let notes become truer than cards.  

Because your current harness tree includes `indexes/`, `registries/`, and `schemas/`, I would also make AGENTS explicitly say:

* indexes are tracking surfaces, not substitutes for cards;
* registries define canonical vocabularies;
* schemas define structural validity;
* the card is still the operational source of truth for a specific item.

That part is a design recommendation based on your current tree.

### 8. Boundary and gate behavior

This should be explicit and compact:

* `blocked` means stop and name the blocker,
* `checkpoint` means stop normal execution and prepare the reviewable packet,
* `awaiting_approval` means stop until signoff condition is satisfied,
* `validating` means evidence collection/interpretation is now dominant,
* do not blur Layer C regime with Layer D gate.  

### 9. Reslice, reroute, and promote rules

This is one area where `AGENTS.md` should be explicit:

* reslice when one current mode no longer fits,
* reroute when the dominant work changes,
* promote to workstream only when coordination pressure is real,
* do not treat long horizon or review burden as a new mode.   

### 10. Required minimum quality bars

Keep the current “usable task” and “usable workstream” sections. They are strong because they convert abstract discipline into a checkable artifact standard. 

### 11. Behavior when uncertain

This should remain. It is one of the most useful parts of the current AGENTS file:

* reread the artifact,
* identify slice,
* identify state,
* identify one mode,
* check whether a real boundary exists,
* repair artifact if needed,
* continue only through the correct loop. 

### 12. Stop / handoff checklist

Also keep this. It operationalizes resumability. 

### 13. Anti-patterns

This should stay near the end and remain strict:

* vague note pile,
* premature workstreams,
* stale cards,
* continuing through blocked/review/approval state,
* invented ontology,
* unclosed terminal work. 

### 14. Practical shorthand

End with the five-question health test. It is the best compact closing section because it compresses the whole harness into an operational check.  

## What I would change from the current `AGENTS.md`

The current file is already structurally strong. The main design changes I would make are these.

First, **reduce duplicated canonical detail**.
The inline allowed-modes list and state list are okay, but the deeper semantics should live in routing rules, registries, and the Layer D spec. `AGENTS.md` should emphasize behavior and source-of-truth references rather than carry too much duplicated vocabulary. That is more aligned with the playbook’s “thin operational loop” rule.   

Second, **align all path references to the current harness tree**.
The current AGENTS still points to `docs/harness/active/...`, while your current tree is organized around `indexes/`, examples, registries, and schemas. So the new AGENTS should reference the actual current operating locations and should explain how cards, indexes, schemas, and registries relate. The existing file’s path assumptions are now stale.  

Third, **add explicit “what this file is not”**.
That will help prevent AGENTS from becoming a second playbook.

Fourth, **promote the default executable loop higher in the file**.
Right now the current AGENTS is good but somewhat section-heavy. Putting one short execution loop early would make it easier for agents to use in practice.

Fifth, **explicitly distinguish structural validity from operational truth**.
Since your current harness has `schemas/` and `registries/`, AGENTS should say: schema-valid is necessary but not sufficient; the card must also be operationally truthful. That follows from the existing emphasis on truthful Layer D and concrete `next_step`. 

## Recommended final outline

I would write the new `AGENTS.md` like this:

1. `# Harness Agent Instructions`
2. Purpose of this file
3. What this file does not do
4. Authority order and context loading
5. Core invariants
6. Default agent loop
7. Workflow routing by current situation
8. Artifact authority and update rules
9. Boundary and gate behavior
10. Reslice / reroute / promote rules
11. Minimum quality bars for task and workstream artifacts
12. Behavior when uncertain
13. Stop / handoff checklist
14. Anti-patterns
15. Practical shorthand

That gives you a document that is small, directive, and faithful to the rest of the harness.

The main design rule is this: **README orients, playbook explains, AGENTS executes**. The current docs already support that separation; the new AGENTS should lean into it harder.   
