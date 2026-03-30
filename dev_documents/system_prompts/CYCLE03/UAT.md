# CYCLE 03 Specification: Integration Graph and Conflict Manager UAT

## Test Scenarios

### Scenario ID: 03-A (3-Way Diff Construction)
**Priority:** High
**Description:** The system must extract the base, local, and remote git file states correctly when a conflict occurs.

### Scenario ID: 03-B (Integration Routing)
**Priority:** High
**Description:** The Integration Graph must correctly route between the git merge node, the integrator node, and the global sandbox based on conflict states.

## Behavior Definitions

### Scenario 03-A: Constructing the Conflict Package
```gherkin
GIVEN a file `main.py` is in a conflicted state between Branch A and Branch B
WHEN build_conflict_package is called for `main.py`
THEN the resulting prompt string contains "### Base (元のコード)"
AND the string contains the base version of the file
AND the string contains "### Branch A の変更 (Local)"
AND the string contains "### Branch B の変更 (Remote)"
```

### Scenario 03-B: Routing Conflict Resolution
```gherkin
GIVEN the Integration Graph is executing
WHEN git_merge_node returns a status of "conflict"
THEN route_merge directs the flow to master_integrator_node

GIVEN the master_integrator_node completes
WHEN the state transitions out of the node
THEN the flow is directed back to git_merge_node to attempt the merge again
```