# ==========================================================================
# Tests: Tool Registry & Safe Execution
# ==========================================================================

import pytest
from server.tools.registry import default_registry

def test_registry_contains_expected_safe_tools():
    expected_tools = [
        "create_task", "list_tasks", "complete_task",
        "save_memory", "list_memories", "delete_memory",
        "web_search_placeholder", "summarize_text", "get_market_demo_data"
    ]
    for tool_name in expected_tools:
        assert default_registry.has_tool(tool_name) is True
        tool = default_registry.get(tool_name)
        assert tool is not None
        assert tool.name == tool_name

def test_tool_catalog_descriptor_schemas():
    tools = default_registry.list_tools()
    assert len(tools) >= 9
    for desc in tools:
        assert "name" in desc
        assert "description" in desc
        assert "risk_level" in desc
        assert "parameters_schema" in desc

@pytest.mark.asyncio
async def test_market_demo_data_tool():
    tool = default_registry.get("get_market_demo_data")
    result = await tool.execute(tool.input_schema(symbols=["NVDA", "AAPL"]), {})
    assert "quotes" in result
    assert "NVDA" in result["quotes"]
    assert "AAPL" in result["quotes"]
    assert "SIMULATED FEED" in result["notice"]

@pytest.mark.asyncio
async def test_web_search_placeholder_tool():
    tool = default_registry.get("web_search_placeholder")
    result = await tool.execute(tool.input_schema(query="Solid state batteries"), {})
    assert "results" in result
    assert len(result["results"]) > 0
    assert result["query"] == "Solid state batteries"

