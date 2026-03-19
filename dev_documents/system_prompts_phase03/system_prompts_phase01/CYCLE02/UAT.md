# CYCLE 02 UAT: Architect Self-Critic Node Integration

## Test Scenarios
- **Scenario ID 02-01:** Successful Critic Evaluation Loop
  - Priority: Critical
  - The Architect graph evaluates specs correctly and passes if no vulnerabilities are found in the output.
  - This verifies that a perfectly generated spec does not get incorrectly blocked by the Self-Critic.

- **Scenario ID 02-02:** Vulnerable Spec Regeneration
  - Priority: Critical
  - If a spec misses an explicit DB constraint (simulated vulnerability), the Self-Critic must return a rejected state, looping back to the Architect to fix the issue.
  - This validates the core feature of the Red Teaming intra-cycle concept.

- **Scenario ID 02-03:** Critic Max Retries Limit
  - Priority: Medium
  - If the Self-Critic continually finds vulnerabilities, the system must forcefully approve the spec or fail gracefully after a defined limit (e.g., 3 retries) to prevent infinite loops.

## Behavior Definitions
- **GIVEN** an architect session has generated a spec
  **WHEN** the Self-Critic evaluator runs and parses `CriticResult` as `is_approved=True`
  **THEN** the graph routes to `END` and finalizes the architecture documentation.

- **GIVEN** an architect session has generated a spec
  **WHEN** the Self-Critic evaluator runs and parses `CriticResult` as `is_approved=False` with a list of `vulnerabilities`
  **THEN** the graph routes back to the architect session, prepending the `vulnerabilities` to the next prompt, incrementing a retry counter.

- **GIVEN** the retry counter for the Self-Critic has reached its maximum (e.g., 3)
  **WHEN** the Self-Critic evaluator runs and parses `CriticResult` as `is_approved=False`
  **THEN** the graph must either log a critical warning and force approval, or fail the entire `gen-cycles` operation cleanly.
