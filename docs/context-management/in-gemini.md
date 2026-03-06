This goal--making agents "liable" (accountable, reliable, and verifiable)--is the exact reason a layered operations stack is necessary. In systems engineering, you cannot hold a non-deterministic actor (an LLM) accountable for a vague instruction. Liability requires a strict contract.

When we talk about making an agent "liable to do the work," we are really talking about shifting from **probabilistic prompting** to **contract-driven execution**. The Agentic Execution Harness achieves this by using the layers to box the agent in, making success measurable and failure loudly observable.

### Assumptions and Constraints

- **Orchestrator Authority Constraint:** The LLM does not manage the stack. A deterministic orchestration engine (the Harness) holds the state of Layers A, B, C, and D and dictates them to the agent.
- **Validation Assumption:** Liability requires an objective function. The agent is only "liable" if the orchestrator has a programmatic way to verify the output (e.g., tests, linters, schema validation) before allowing a state change in Layer D.

Here is how the Agentic Execution Harness enforces liability at each level of the stack.

### 1. Layer A & B: Enforcing Epistemic Liability (No Hallucinated Scope)

Agents fail most frequently when they guess their operational boundaries. By feeding the Layer A classification and Layer B mode directly into the system prompt, you hold the agent strictly liable to a specific posture.

- **Eliminating Scope Creep:** If Layer A defines the `scope_topology` as `local` and `dependency_complexity` as `self_contained`, the agent is explicitly forbidden from rewriting an upstream service. If it attempts to touch files outside the local boundary, the Harness rejects the action.
- **Role-Specific Output Contracts:** A `Research Scout` (Layer B) is liable for producing an evidence summary or an option comparison. If it attempts to write implementation code, the Harness intercepts the artifact type mismatch and fails the run.

### 2. Layer C: Enforcing Governance Liability (No Silent Failures)

Without Layer C, agents often confidently commit broken code because they don't know when to ask for help. Layer C overlays enforce liability by defining the exact conditions under which the agent is _required_ to stop and wait.

- **Forced Checkpoints:** If a `review_gatekeeper` overlay is applied, the agent is liable for producing a specific, reviewable packet (e.g., findings summary, architecture note). It cannot silently transition itself to implementation.
- **Blast Radius Protection:** If `governance_escalation` is active due to a `cross_service` migration, the agent is liable for producing rollback evidence. The Harness will not allow the workstream to proceed until that specific artifact is generated and verified.

### 3. Layer D: Enforcing Execution Liability (Deterministic Stopping)

Agents are notorious for entering infinite ReAct (Reason+Act) loops when they encounter an error. Layer D prevents this by giving the Harness a strict control plane to freeze the agent.

- **The "Blocked" Contract:** If an agent is in the `active` state but encounters an environment failure, it is liable for explicitly diagnosing the block. It must transition the state to `blocked` and provide a `blocking_reason` and an `unblock_condition`. This prevents the agent from spinning its wheels and burning tokens.
- **Evidence-Based Completion:** An agent cannot simply declare it is `complete`. To transition to `complete`, it must satisfy the validation burden established in Layer A (e.g., `tests_strong_confidence` or `offline_eval_required`). The Harness runs the test; if it fails, the agent remains `active` or moves to `blocked`.

### The Mechanism of Liability: The "Work Slice Payload"

To make the agent liable, the Harness must compile the ABCD stack into a single, immutable JSON payload that is injected into the agent's context window at the start of every session.

If the agent knows:

1. Exactly what the problem is (Layer A)
2. Exactly how it is expected to behave (Layer B)
3. Exactly what rules it must follow (Layer C)
4. Exactly what state it is currently in (Layer D)

...then any deviation from that payload is an objective failure of the contract, which the orchestration engine can catch, log, and either retry or escalate to a human.

Would you like to design the JSON Schema for this "Work Slice Payload"--the actual data object the orchestrator would pass to the agent to bind it to these rules?