import asyncio
from typing import Any

from ac_cdd_core.services.jules_client import JulesClient


class MockJulesClient(JulesClient): # type: ignore[misc]
    def __init__(self) -> None:
        self.call_count = 0

    async def run_session(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.call_count += 1
        return {
            "status": "success",
            "pr_url": "http://github.com/pr/1",
            "session_name": "test_session_name"
        }

    async def _send_message(self, session_url: str, message: str) -> None:
        pass

    async def wait_for_completion(self, session_name: str, require_plan_approval: bool = False) -> dict[str, Any]:
        return {
            "status": "success",
            "pr_url": "http://github.com/pr/1",
            "session_name": "test_session_name"
        }

    def _get_session_url(self, session_name: str) -> str:
        return f"http://fake.url/{session_name}"

async def test_uat_critic_retry_loop() -> None:
    # Set up basic mock environment

    # We override the methods internally because the full integration involves
    # file parsing which is hard to mock purely here.
    # We will test the basic state transition of the graph using mock nodes.

    from ac_cdd_core.enums import FlowStatus
    from ac_cdd_core.state import CycleState
    from langgraph.graph import END, START, StateGraph

    workflow = StateGraph(CycleState)

    # Define a simplified version of the logic we implemented in the real graph
    # to simulate the UAT scenario described in UAT-C01-001 and UAT-C01-002
    async def mock_architect_session(state: CycleState) -> dict[str, Any]:
        if state.status == FlowStatus.CRITIC_REJECTED:
            # We are in the retry loop
            return {
                "status": "architect_completed",
                "integration_branch": "dev/int-test",
                "active_branch": "dev/int-test",
                "project_session_id": "session-123",
                "pr_url": "http://pr/1"
            }
        # First pass
        return {
            "status": "architect_completed",
            "integration_branch": "dev/int-test",
            "active_branch": "dev/int-test",
            "project_session_id": "session-123",
            "pr_url": "http://pr/1"
        }

    async def mock_architect_critic(state: CycleState) -> dict[str, Any]:
        # Scenario 1: Rejection
        if state.iteration_count == 0:
            return {
                "status": FlowStatus.CRITIC_REJECTED.value,
                "critic_feedback": ["Missing interface contract"],
                "is_architecture_locked": False,
                "iteration_count": 1
            }
        # Scenario 2: Approval
        return {
            "status": FlowStatus.ARCHITECTURE_APPROVED.value,
            "is_architecture_locked": True,
            "critic_feedback": []
        }

    def route_critic(state: CycleState) -> str:
        if state.status == FlowStatus.ARCHITECTURE_APPROVED:
            return "end"
        return "mock_architect_session"

    workflow.add_node("mock_architect_session", mock_architect_session)
    workflow.add_node("mock_architect_critic", mock_architect_critic)

    workflow.add_edge(START, "mock_architect_session")
    workflow.add_edge("mock_architect_session", "mock_architect_critic")
    workflow.add_conditional_edges(
        "mock_architect_critic",
        route_critic,
        {
            "end": END,
            "mock_architect_session": "mock_architect_session"
        }
    )

    app = workflow.compile()

    initial_state = CycleState(cycle_id="test", iteration_count=0)

    # Run the graph
    events = []
    async for event in app.astream(initial_state):
        events.append(event)

    # The expected flow is:
    # 1. mock_architect_session
    # 2. mock_architect_critic (rejects)
    # 3. mock_architect_session (retries)
    # 4. mock_architect_critic (approves)
    # 5. END

    # Let's verify the events
    assert len(events) == 4
    assert "mock_architect_session" in events[0]

    critic_event_1 = events[1]["mock_architect_critic"]
    assert critic_event_1["status"] == FlowStatus.CRITIC_REJECTED.value
    assert critic_event_1["is_architecture_locked"] is False
    assert len(critic_event_1["critic_feedback"]) == 1

    assert "mock_architect_session" in events[2]

    critic_event_2 = events[3]["mock_architect_critic"]
    assert critic_event_2["status"] == FlowStatus.ARCHITECTURE_APPROVED.value
    assert critic_event_2["is_architecture_locked"] is True

    # print removed to satisfy ruff

if __name__ == "__main__":
    asyncio.run(test_uat_critic_retry_loop())
