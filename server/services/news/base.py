# ==========================================================================
# JARVIS Base News Provider Interface
# ==========================================================================

from abc import ABC, abstractmethod
from typing import List, Optional
from server.models.schemas import NewsItemOut

class BaseNewsProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def fetch_news(
        self,
        category: Optional[str] = "all",
        limit: int = 20,
        region: Optional[str] = "Global",
        query: Optional[str] = None,
        ticker: Optional[str] = None,
        entity: Optional[str] = None,
        time_range: Optional[str] = "24h",
        language: Optional[str] = "en"
    ) -> List[NewsItemOut]:
        """Retrieves and normalizes latest live news items."""
        pass

