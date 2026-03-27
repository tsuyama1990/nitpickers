import abc
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseNode(BaseModel, abc.ABC):
    """
    Strictly-typed Pydantic base class for all Pipeline Nodes.
    Enforces interface contracts for integration testing without mocks.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        arbitrary_types_allowed=True,  # To allow dependencies like JulesClient/GitManager
        frozen=True,  # Enforce immutability of node dependencies
    )

    @abc.abstractmethod
    async def __call__(self, state: Any) -> dict[str, Any]:
        """
        The main execution method for the node.
        MUST be implemented by all subclasses and used as the entry point.
        """
