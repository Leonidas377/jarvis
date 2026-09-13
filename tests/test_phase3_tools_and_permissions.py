import pytest
from server.permissions.scopes import Scope
from server.tools.registry import default_registry as TOOL_REGISTRY

def test_phase3_permission_scopes():
    assert hasattr(Scope, "RESEARCH_READ")
    assert hasattr(Scope, "RESEARCH_WRITE")
    assert hasattr(Scope, "NEWS_READ")
    assert hasattr(Scope, "NEWS_WRITE")
    assert hasattr(Scope, "SOURCE_FETCH")
    assert hasattr(Scope, "BRIEFING_GENERATE")
    assert hasattr(Scope, "EXTERNAL_LINK_OPEN")

    assert Scope.RESEARCH_READ.value == "research:read"
    assert Scope.NEWS_READ.value == "news:read"
    assert Scope.RESEARCH_WRITE.value == "research:write"

def test_phase3_tools_registered():
    expected_tools = [
        "web_search",
        "fetch_source",
        "summarize_source",
        "create_research_report",
        "save_research_report",
        "get_news",
        "create_news_topic",
        "create_news_briefing"
    ]
    
    for tool_name in expected_tools:
        tool = TOOL_REGISTRY.get(tool_name)
        assert tool is not None, f"Expected tool {tool_name} was not found in TOOL_REGISTRY!"
        assert tool.name == tool_name
        assert tool.required_scope is not None
        # Safety requirement: no research tool may have broker trading or device control
        assert "broker:trade" not in tool.required_scope
        assert "purchase:submit" not in tool.required_scope
        assert "device:control" not in tool.required_scope

@pytest.mark.asyncio
async def test_tool_registry_web_search_execution():
    search_tool = TOOL_REGISTRY.get("web_search")
    params = search_tool.input_schema(query="silicon photonics", limit=3)
    result = await search_tool.execute(params, {"user": {"id": "default-tony-stark"}})
    assert result["count"] > 0
    assert "results" in result
    assert result["query"] == "silicon photonics"

@pytest.mark.asyncio
async def test_tool_registry_news_execution():
    news_tool = TOOL_REGISTRY.get("get_news")
    params = news_tool.input_schema(category="technology", limit=4)
    result = await news_tool.execute(params, {"user": {"id": "default-tony-stark"}})
    assert "items" in result
    assert len(result["items"]) > 0
    assert result["items"][0]["headline"] is not None
