from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .enums import FlowStatus
from .graph_nodes import CycleNodes
from .interfaces import IGraphNodes
from .sandbox import SandboxRunner
from .service_container import ServiceContainer
from .services.jules_client import JulesClient
from .state import CycleState


class GraphBuilder:
    def __init__(
        self, services: ServiceContainer, sandbox: SandboxRunner, jules: JulesClient
    ) -> None:
        self.sandbox = sandbox
        self.jules = jules
        self.nodes: IGraphNodes = CycleNodes(self.sandbox, self.jules)

    async def cleanup(self) -> None:
        """Cleanup resources, specifically the sandbox."""
        if self.sandbox:
            await self.sandbox.cleanup()

    def _create_architect_graph(self) -> StateGraph[CycleState]:
        """Create the graph for the Architect phase (gen-cycles)."""
        if not self.nodes:
            msg = "Graph nodes are not initialized"
            raise ValueError(msg)
        if not getattr(self.nodes, "architect_session_node", None):
            msg = "architect_session_node is missing from Graph nodes"
            raise ValueError(msg)
        if not getattr(self.nodes, "architect_critic_node", None):
            msg = "architect_critic_node is missing from Graph nodes"
            raise ValueError(msg)

        workflow = StateGraph(CycleState)

        workflow.add_node("architect_session", self.nodes.architect_session_node)
        workflow.add_node("architect_critic", self.nodes.architect_critic_node)

        workflow.add_edge(START, "architect_session")

        # from architect_session to architect_critic instead of END
        workflow.add_edge("architect_session", "architect_critic")

        # from architect_critic to END or back to architect_critic
        workflow.add_conditional_edges(
            "architect_critic",
            self.nodes.route_architect_critic,
            {
                "architect_critic": "architect_critic",
                "end": END,
            },
        )

        return workflow

    def _create_coder_graph(self) -> StateGraph[CycleState]:
        """Create the graph for the Coder/Auditor phase (run-cycle)."""
        if not self.nodes:
            msg = "Graph nodes are not initialized"
            raise ValueError(msg)

        required_nodes = [
            "coder_session_node",
            "sandbox_evaluate_node",
            "auditor_node",
            "coder_critic_node",
            "global_refactor_node",
        ]
        for n in required_nodes:
            if not getattr(self.nodes, n, None):
                msg = f"{n} is missing from Graph nodes"
                raise ValueError(msg)

        workflow = StateGraph(CycleState)

        from src.config import settings

        workflow.add_node("coder_session", self.nodes.coder_session_node)
        workflow.add_node(settings.node_sandbox_evaluate, self.nodes.sandbox_evaluate_node)
        workflow.add_node("auditor", self.nodes.auditor_node)
        workflow.add_node("self_critic", self.nodes.coder_critic_node)
        workflow.add_node("refactor_node", self.nodes.global_refactor_node)
        workflow.add_node("final_critic", self.nodes.coder_critic_node)

        workflow.add_edge(START, "coder_session")

        # Conditional edge from coder_session
        workflow.add_conditional_edges(
            "coder_session",
            self.nodes.check_coder_outcome,
            {
                "self_critic": "self_critic",
                settings.node_sandbox_evaluate: settings.node_sandbox_evaluate,
                FlowStatus.FAILED.value: END,
                FlowStatus.CODER_RETRY.value: "coder_session",
            },
        )

        # self_critic -> sandbox_evaluate
        workflow.add_edge("self_critic", settings.node_sandbox_evaluate)

        # Sandbox Evaluate -> Auditor, final_critic, failed, or coder_session
        workflow.add_conditional_edges(
            settings.node_sandbox_evaluate,
            self.nodes.route_sandbox_evaluate,
            {
                "auditor": "auditor",
                "coder_session": "coder_session",
                "final_critic": "final_critic",
                "failed": END,
            },
        )

        # Auditor -> Conditional routing (rejection loop, next auditor, or refactor)
        workflow.add_conditional_edges(
            "auditor",
            self.nodes.route_auditor,
            {
                "reject": "coder_session",
                "next_auditor": "auditor",
                "pass_all": "refactor_node",
            },
        )

        # refactor_node -> sandbox_evaluate
        workflow.add_edge("refactor_node", settings.node_sandbox_evaluate)

        # final_critic -> end or coder_session
        workflow.add_conditional_edges(
            "final_critic",
            self.nodes.route_final_critic,
            {
                "approve": END,
                "reject": "coder_session",
            },
        )

        return workflow

    def build_architect_graph(self) -> CompiledStateGraph[CycleState, Any, Any, Any]:
        return self._create_architect_graph().compile(checkpointer=MemorySaver())

    def build_coder_graph(self) -> CompiledStateGraph[CycleState, Any, Any, Any]:
        return self._create_coder_graph().compile(checkpointer=MemorySaver())

    def _create_qa_graph(self) -> StateGraph[CycleState]:
        """Create the graph for the QA/Tutorial generation phase."""
        workflow = StateGraph(CycleState)

        workflow.add_node("qa_session", self.nodes.qa_session_node)
        workflow.add_node("qa_auditor", self.nodes.qa_auditor_node)

        workflow.add_edge(START, "qa_session")

        # Custom logic for QA session routing (similar to coder_session)
        # If qa_session fails or succeeds
        workflow.add_conditional_edges(
            "qa_session",
            lambda state: "qa_auditor" if state.get("status") == "ready_for_audit" else END,
            {"qa_auditor": "qa_auditor", END: END},
        )

        # Router from Auditor
        workflow.add_conditional_edges(
            "qa_auditor",
            self.nodes.route_qa,
            {
                "end": END,
                "retry_fix": "qa_session",
                "failed": END,
            },
        )
        return workflow

    def build_qa_graph(self) -> CompiledStateGraph[CycleState, Any, Any, Any]:
        return self._create_qa_graph().compile(checkpointer=MemorySaver())
