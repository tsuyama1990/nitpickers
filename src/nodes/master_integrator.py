from pathlib import Path
from typing import Any

from src.services.integration_usecase import IntegrationUsecase, MaxRetriesExceededError
from src.services.jules_client import JulesClient
from src.state import IntegrationState


class MasterIntegratorNodes:
    """Nodes for the Master Integrator conflict resolution flow."""

    def __init__(self, jules_client: JulesClient | None = None) -> None:
        self.jules = jules_client or JulesClient()
        self.usecase = IntegrationUsecase(self.jules)

    async def master_integrator_node(self, state: IntegrationState) -> dict[str, Any]:
        """
        Executes the master integrator conflict resolution loop.
        """
        repo_path = Path.cwd()
        try:
            new_state = await self.usecase.run_integration_loop(state, repo_path)
        except MaxRetriesExceededError:
            # We don't have an error field in IntegrationState by default,
            # we can just return what we have and let the caller check if all are resolved
            pass
        except Exception as e:
            from src.utils import logger
            logger.error(f"Master Integrator node encountered an error: {e}")
        else:
            # the run_integration_loop updates unresolved_conflicts in place,
            # but returning it guarantees langgraph updates state properly
            return {
                "master_integrator_session_id": new_state.master_integrator_session_id,
                "unresolved_conflicts": new_state.unresolved_conflicts,
            }

        return {
            "master_integrator_session_id": state.master_integrator_session_id,
            "unresolved_conflicts": state.unresolved_conflicts,
        }
