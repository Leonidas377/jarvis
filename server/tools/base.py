# ==========================================================================
# JARVIS Base Tool Specification
# ==========================================================================

from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope

class BaseTool(ABC):
    name: str
    version: str = "1.0.0"
    description: str
    risk_level: str = RiskLevel.R0_SAFE.value
    required_scope: str = Scope.CONVERSATION_WRITE.value
    requires_confirmation: bool = False
    input_schema: Type[BaseModel]

    @abstractmethod
    async def execute(self, params: BaseModel, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the tool logic safely within context."""
        pass
