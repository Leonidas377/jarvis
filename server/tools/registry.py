# ==========================================================================
# JARVIS Tool Registry & Dispatcher
# ==========================================================================

from typing import Dict, Any, List, Optional
from server.tools.base import BaseTool
from server.tools.task_tools import CreateTaskTool, ListTasksTool, CompleteTaskTool
from server.tools.memory_tools import SaveMemoryTool, ListMemoriesTool, DeleteMemoryTool
from server.tools.market_tools import (
    GetMarketDemoDataTool,
    SearchAssetsTool,
    GetMarketQuoteTool,
    GetMarketHistoryTool,
    GetMarketOverviewTool,
    GetRelatedMarketNewsTool,
    GenerateMarketInsightTool,
    GetReadOnlyPortfolioTool
)
from server.tools.search_tools import (
    WebSearchTool,
    WebSearchPlaceholderTool,
    FetchSourceTool,
    SummarizeSourceTool,
    SummarizeTextTool,
    CreateResearchReportTool,
    SaveResearchReportTool,
    GenerateResearchBriefTool,
    SaveResearchBriefTool,
    GetNewsTool,
    CreateNewsTopicTool,
    CreateNewsBriefingTool
)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers a tool in the catalog."""
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Retrieves a tool by name."""
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """Checks if a tool is registered."""
        return tool_name in self._tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists metadata and JSON schemas for all registered tools."""
        descriptors = []
        for name, tool in self._tools.items():
            descriptors.append({
                "name": tool.name,
                "version": tool.version,
                "description": tool.description,
                "risk_level": tool.risk_level,
                "required_scope": tool.required_scope,
                "requires_confirmation": tool.requires_confirmation,
                "parameters_schema": tool.input_schema.model_json_schema()
            })
        return descriptors

    def validate_params(self, tool_name: str, params: Dict[str, Any]):
        """Validates raw dictionary parameters against the tool's Pydantic schema."""
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        return tool.input_schema(**params)

    async def execute(self, tool_name: str, raw_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool with validated parameters and execution context."""
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        validated_params = tool.input_schema(**raw_params)
        return await tool.execute(validated_params, context)

def build_default_registry() -> ToolRegistry:
    """Builds and populates the default tool registry with all safe system tools."""
    reg = ToolRegistry()
    # Task tools
    reg.register(CreateTaskTool())
    reg.register(ListTasksTool())
    reg.register(CompleteTaskTool())
    # Memory tools
    reg.register(SaveMemoryTool())
    reg.register(ListMemoriesTool())
    reg.register(DeleteMemoryTool())
    # Search, Extraction & Research tools
    reg.register(WebSearchTool())
    reg.register(WebSearchPlaceholderTool())
    reg.register(FetchSourceTool())
    reg.register(SummarizeSourceTool())
    reg.register(SummarizeTextTool())
    reg.register(CreateResearchReportTool())
    reg.register(SaveResearchReportTool())
    reg.register(GenerateResearchBriefTool())
    reg.register(SaveResearchBriefTool())
    # News intelligence tools
    reg.register(GetNewsTool())
    reg.register(CreateNewsTopicTool())
    reg.register(CreateNewsBriefingTool())
    # Financial Market Intelligence Tools (Strictly Read-Only)
    reg.register(GetMarketDemoDataTool())
    reg.register(SearchAssetsTool())
    reg.register(GetMarketQuoteTool())
    reg.register(GetMarketHistoryTool())
    reg.register(GetMarketOverviewTool())
    reg.register(GetRelatedMarketNewsTool())
    reg.register(GenerateMarketInsightTool())
    reg.register(GetReadOnlyPortfolioTool())
    return reg

default_registry = build_default_registry()
