# ==========================================================================
# JARVIS Market Data Provider: Base Interface
# ==========================================================================

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from server.models.schemas import AssetOut, MarketQuoteOut, PriceBarOut, MarketOverviewOut

class BaseMarketDataProvider(ABC):
    """Abstract interface for all financial market data providers."""

    provider_name: str = "BaseProvider"

    @abstractmethod
    async def search_assets(self, query: str, limit: int = 10) -> List[AssetOut]:
        """Searches assets by company name or ticker symbol."""
        pass

    @abstractmethod
    async def get_quote(self, asset: AssetOut) -> MarketQuoteOut:
        """Retrieves real-time or delayed market quote for an asset."""
        pass

    @abstractmethod
    async def get_history(
        self,
        asset: AssetOut,
        interval: str = "1d",
        range_str: str = "1mo"
    ) -> List[PriceBarOut]:
        """Retrieves OHLCV price bars for a specific time range and interval."""
        pass

    @abstractmethod
    async def get_overview(self) -> MarketOverviewOut:
        """Retrieves major market indices, gainers, losers, and sector performance."""
        pass

    @abstractmethod
    def get_market_status(self) -> str:
        """Returns market session status: OPEN | CLOSED | PRE_MARKET | AFTER_HOURS."""
        pass
