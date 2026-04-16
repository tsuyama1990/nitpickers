import asyncio
from src.state import CycleState
from src.enums import FlowStatus
from src.nodes.coder_critic import CoderCriticNodes
from src.nodes.routers import route_final_critic

async def main():
    print("--- Simulating Final Critic Polish Phase ---")
    
    # 1. Provide a dummy state going into final_critic_node
    state = CycleState(
        cycle_id="01", 
        status=FlowStatus.READY_FOR_AUDIT,
        jules_session_name="sessions/fake_session"
    )
    
    # 2. Run the node (pass None for jules_client as it shouldn't need it anymore)
    nodes = CoderCriticNodes(jules_client=None)
    result = await nodes.coder_critic_node(state)
    print(f"Coder Critic Node Execution Result: {result}")
    
    # 3. Simulate LangGraph updating the state with the result
    state.status = result.get("status")
    
    # 4. Check what LangGraph will route to next
    next_node = route_final_critic(state)
    print(f"LangGraph Route Result: {next_node}")
    
    if next_node == "approve":
        print("SUCCESS! The node correctly bypasses the duplicate JSON check and approves the PR.")
    else:
        print("FAIL! The node rejected the PR and routed back to the Coder.")

if __name__ == "__main__":
    asyncio.run(main())
