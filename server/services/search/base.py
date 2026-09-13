# ==========================================================================
# JARVIS Base Search Provider Interface
# ==========================================================================

from abc import ABC, abstractmethod
from typing import List, Optional
from server.models.schemas import SearchResultItem

class BaseSearchProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 8,
        category: Optional[str] = "all",
        region: Optional[str] = "us-en"
    ) -> List[SearchResultItem]:
        """Executes a search query and returns normalized search results."""
        pass
