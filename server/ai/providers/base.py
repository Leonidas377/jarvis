# ==========================================================================
# JARVIS Base LLM Client Interface
# ==========================================================================

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolCallPlan(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    rationale: Optional[str] = None

class AIResponse(BaseModel):
    content: Optional[str] = None
    tool_call: Optional[ToolCallPlan] = None
    model: str = "unknown"
    usage: Optional[Dict[str, int]] = None

class ProviderTestResult(BaseModel):
    status: str  # CONNECTED, INVALID_KEY, MODEL_NOT_FOUND, PROVIDER_UNREACHABLE, TIMEOUT, RATE_LIMITED, etc.
    message: str
    provider: str
    model: str
    latency_ms: Optional[int] = None

class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        """Generates conversational response or plans tool calls."""
        pass

    @abstractmethod
    async def test_connection(self) -> ProviderTestResult:
        """Performs a minimal non-sensitive connectivity and authentication check."""
        pass
