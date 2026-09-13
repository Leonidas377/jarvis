# ==========================================================================
# JARVIS Financial Market & Telemetry Tools (Strictly Read-Only)
# No broker order tools or trading write permissions permitted
# ==========================================================================

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.tools.base import BaseTool
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.services.market import (
    market_service, MarketNewsCorrelator, MarketInsightService
)

# ----------------- 1. Search Assets Tool -----------------
class SearchAssetsInput(BaseModel):
    query: str = Field(..., description="Company name, fund, or ticker symbol to search")
    limit: int = Field(default=5, description="Maximum number of candidates to return")

class SearchAssetsTool(BaseTool):
    name = "search_assets"
    version = "1.0.0"
    description = "Searches financial instruments by ticker or company name and returns exact identity candidates."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = SearchAssetsInput

    async def execute(self, params: SearchAssetsInput, context: Dict[str, Any]) -> Dict[str, Any]:
        assets = await market_service.search_and_resolve_assets(params.query, limit=params.limit)
        return {
            "query": params.query,
            "count": len(assets),
            "candidates": [a.model_dump() for a in assets]
        }


# ----------------- 2. Get Market Quote Tool -----------------
class GetMarketQuoteInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset (e.g. NVDA, AAPL, TSM, BTC-USD)")

class GetMarketQuoteTool(BaseTool):
    name = "get_market_quote"
    version = "1.0.0"
    description = "Retrieves latest timestamped price quote, exchange, and data freshness for an asset."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = GetMarketQuoteInput

    async def execute(self, params: GetMarketQuoteInput, context: Dict[str, Any]) -> Dict[str, Any]:
        sym = params.symbol.strip().upper().replace("$", "")
        asset = await market_service.get_asset_by_id(sym)
        if not asset:
            # Try searching to resolve
            candidates = await market_service.search_and_resolve_assets(sym, limit=1)
            if candidates:
                asset = candidates[0]

        if not asset:
            return {"error": "ASSET_NOT_FOUND", "message": f"Asset {sym} could not be resolved."}

        quote = await market_service.get_asset_quote(asset)
        return quote.model_dump()


# ----------------- 3. Get Market History Tool -----------------
class GetMarketHistoryInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    range_str: str = Field(default="1mo", description="Time range: 1d | 1w | 1mo | 3mo | 1y | 5y")

class GetMarketHistoryTool(BaseTool):
    name = "get_market_history"
    version = "1.0.0"
    description = "Retrieves historical OHLCV chart bars for an asset over a bounded time window."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = GetMarketHistoryInput

    async def execute(self, params: GetMarketHistoryInput, context: Dict[str, Any]) -> Dict[str, Any]:
        sym = params.symbol.strip().upper().replace("$", "")
        asset = await market_service.get_asset_by_id(sym)
        if not asset:
            candidates = await market_service.search_and_resolve_assets(sym, limit=1)
            if candidates:
                asset = candidates[0]

        if not asset:
            return {"error": "ASSET_NOT_FOUND", "message": f"Asset {sym} could not be resolved."}

        bars = await market_service.get_asset_history(asset, range_str=params.range_str)
        return {
            "symbol": asset.symbol,
            "range": params.range_str,
            "bar_count": len(bars),
            "bars": [b.model_dump() for b in bars]
        }


# ----------------- 4. Get Market Overview Tool -----------------
class GetMarketOverviewInput(BaseModel):
    include_sectors: bool = Field(default=True, description="Whether to include sector performance")

class GetMarketOverviewTool(BaseTool):
    name = "get_market_overview"
    version = "1.0.0"
    description = "Retrieves market session status, major index telemetry (S&P 500, NASDAQ, BTC), and top gainers/losers."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = GetMarketOverviewInput

    async def execute(self, params: GetMarketOverviewInput, context: Dict[str, Any]) -> Dict[str, Any]:
        overview = await market_service.get_market_overview()
        return overview.model_dump()


# ----------------- 5. Get Related Market News Tool -----------------
class GetRelatedMarketNewsInput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol of the asset")
    limit: int = Field(default=3, description="Maximum news clusters to return")

class GetRelatedMarketNewsTool(BaseTool):
    name = "get_related_market_news"
    version = "1.0.0"
    description = "Correlates financial assets with Phase 5 news wire clusters and transparent relationship labels."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = GetRelatedMarketNewsInput

    async def execute(self, params: GetRelatedMarketNewsInput, context: Dict[str, Any]) -> Dict[str, Any]:
        sym = params.symbol.strip().upper().replace("$", "")
        asset = await market_service.get_asset_by_id(sym)
        if not asset:
            candidates = await market_service.search_and_resolve_assets(sym, limit=1)
            if candidates:
                asset = candidates[0]

        if not asset:
            return {"error": "ASSET_NOT_FOUND", "message": f"Asset {sym} could not be resolved."}

        correlated = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=params.limit)
        return {
            "symbol": asset.symbol,
            "related_events": correlated
        }


# ----------------- 6. Generate Market Insight Tool -----------------
class GenerateMarketInsightInput(BaseModel):
    question: str = Field(..., description="User question explaining asset or sector movement")
    symbol: Optional[str] = Field(default=None, description="Optional focus ticker symbol")
    time_window: str = Field(default="24h", description="Time window for news and price telemetry")

class GenerateMarketInsightTool(BaseTool):
    name = "generate_market_insight"
    version = "1.0.0"
    description = "Generates a grounded, cited explanation of market price movement using LLM synthesis and observational disclaimers."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = GenerateMarketInsightInput

    async def execute(self, params: GenerateMarketInsightInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        asset = None
        quote = None
        related_news = []

        if params.symbol:
            sym = params.symbol.strip().upper().replace("$", "")
            asset = await market_service.get_asset_by_id(sym)
            if not asset:
                candidates = await market_service.search_and_resolve_assets(sym, limit=1)
                if candidates:
                    asset = candidates[0]

            if asset:
                quote = await market_service.get_asset_quote(asset)
                related_news = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=3)

        insight = await MarketInsightService.generate_insight(
            question=params.question,
            asset=asset,
            quote=quote,
            related_news=related_news,
            user_id=user_id,
            time_window=params.time_window
        )
        return insight.model_dump()


# ----------------- 7. Read-Only Portfolio Tool -----------------
class GetReadOnlyPortfolioInput(BaseModel):
    account_id: Optional[str] = Field(default=None, description="Optional account identifier")

class GetReadOnlyPortfolioTool(BaseTool):
    name = "get_read_only_portfolio"
    version = "1.0.0"
    description = "Inspects read-only account balance and holdings (Strictly no broker order or write execution)."
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.BROKER_READ.value
    requires_confirmation = True
    input_schema = GetReadOnlyPortfolioInput

    async def execute(self, params: GetReadOnlyPortfolioInput, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "BROKER_READ_ONLY_NOT_CONFIGURED",
            "message": "Broker read-only telemetry is not configured. Live broker order placement and trading write operations are disabled.",
            "is_configured": False,
            "holdings": [],
            "buying_power": None,
            "cash_balance": None
        }


# ----------------- 8. Backward-Compatible Demo Tool -----------------
class MarketDataInput(BaseModel):
    symbols: Optional[List[str]] = Field(default=["S&P 500", "NASDAQ", "NVDA", "AAPL", "BTC/USD"], description="List of financial ticker symbols")

class GetMarketDemoDataTool(BaseTool):
    name = "get_market_demo_data"
    version = "1.0.0"
    description = "Retrieves current market indicators, prices, and volatility (SIMULATED DATA ONLY)."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MARKET_READ.value
    requires_confirmation = False
    input_schema = MarketDataInput

    async def execute(self, params: MarketDataInput, context: Dict[str, Any]) -> Dict[str, Any]:
        simulated_quotes = {
            "S&P 500": {"price": "5,842.10", "change": "+0.59%", "volume": "3.4B", "status": "NYSE Open"},
            "NASDAQ": {"price": "18,410.50", "change": "+0.78%", "volume": "4.8B", "status": "NASDAQ Open"},
            "NVDA": {"price": "138.45", "change": "+2.33%", "volume": "62.1M", "status": "Active"},
            "AAPL": {"price": "232.10", "change": "-0.36%", "volume": "41.2M", "status": "Active"},
            "BTC/USD": {"price": "68,420.00", "change": "+2.73%", "volume": "28.4B", "status": "24/7 Global"}
        }

        requested_data = {}
        for s in params.symbols:
            if s in simulated_quotes:
                requested_data[s] = simulated_quotes[s]
            else:
                requested_data[s] = {"price": "100.00", "change": "0.00%", "status": "Simulated"}

        return {
            "notice": "DEMO DATA // SIMULATED FEED // NO FINANCIAL TRADING ALLOWED",
            "timestamp": "2026-09-10 09:30:00 EST",
            "quotes": requested_data
        }
