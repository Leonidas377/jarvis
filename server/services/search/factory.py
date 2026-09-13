# ==========================================================================
# JARVIS Search Provider Factory
# Resolves the active search engine (live DuckDuckGo or demo fallback)
# ==========================================================================

import os
from server.services.search.base import BaseSearchProvider
from server.services.search.duckduckgo_provider import DuckDuckGoSearchProvider
from server.services.search.demo_provider import DemoSearchProvider

def get_search_provider() -> BaseSearchProvider:
    """Returns the configured search provider."""
    engine = os.getenv("JARVIS_SEARCH_ENGINE", "duckduckgo").lower()
    if engine == "demo":
        return DemoSearchProvider()
    return DuckDuckGoSearchProvider()
