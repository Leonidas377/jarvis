# ==========================================================================
# JARVIS Deterministic Demo Market Data Provider
# High-fidelity, offline deterministic telemetry explicitly labeled SIMULATED DATA
# ==========================================================================

import time
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from server.services.market.base import BaseMarketDataProvider
from server.models.schemas import AssetOut, MarketQuoteOut, PriceBarOut, MarketOverviewOut

DEMO_ASSET_BASELINES: Dict[str, Dict[str, Any]] = {
    "NVDA": {"name": "NVIDIA Corporation", "price": 142.50, "prev_close": 139.20, "vol": 52100000, "mcap": 3500000000000, "exch": "NASDAQ", "sec": "Technology"},
    "AAPL": {"name": "Apple Inc.", "price": 234.80, "prev_close": 236.10, "vol": 43200000, "mcap": 3580000000000, "exch": "NASDAQ", "sec": "Technology"},
    "TSM": {"name": "Taiwan Semiconductor", "price": 188.20, "prev_close": 184.40, "vol": 18900000, "mcap": 975000000000, "exch": "NYSE", "sec": "Technology"},
    "MSFT": {"name": "Microsoft Corporation", "price": 428.60, "prev_close": 425.90, "vol": 21300000, "mcap": 3180000000000, "exch": "NASDAQ", "sec": "Technology"},
    "SPY": {"name": "SPDR S&P 500 ETF", "price": 586.40, "prev_close": 583.10, "vol": 68400000, "mcap": 590000000000, "exch": "NYSE Arca", "sec": "Financials"},
    "QQQ": {"name": "Invesco QQQ Trust", "price": 498.20, "prev_close": 494.50, "vol": 38100000, "mcap": 280000000000, "exch": "NASDAQ", "sec": "Technology"},
    "BTC-USD": {"name": "Bitcoin / US Dollar", "price": 68450.00, "prev_close": 67100.00, "vol": 29400000000, "mcap": 1350000000000, "exch": "CRYPTO", "sec": "Digital Assets"}
}

class DeterministicDemoMarketProvider(BaseMarketDataProvider):
    provider_name: str = "Deterministic Simulator"

    def get_market_status(self) -> str:
        # Check standard US market hours (9:30 AM - 4:00 PM Eastern, Mon-Fri)
        now = datetime.now(timezone.utc)
        # EST is UTC-5 (or UTC-4 EDT)
        weekday = now.weekday()
        if weekday >= 5:
            return "CLOSED"
        # Deterministic simulation defaults to OPEN during weekdays
        return "OPEN"

    async def search_assets(self, query: str, limit: int = 10) -> List[AssetOut]:
        q = query.lower().strip()
        results: List[AssetOut] = []
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        for sym, data in DEMO_ASSET_BASELINES.items():
            if q in sym.lower() or q in data["name"].lower():
                results.append(AssetOut(
                    id=f"asset-{sym.lower().replace('-', '_')}",
                    provider_id=sym,
                    symbol=sym,
                    name=data["name"],
                    asset_type="crypto" if "BTC" in sym else ("etf" if sym in ["SPY", "QQQ"] else "equity"),
                    exchange=data["exch"],
                    country="Global" if "BTC" in sym else "US",
                    currency="USD",
                    sector=data["sec"],
                    timezone="UTC" if "BTC" in sym else "America/New_York",
                    is_active=True,
                    provider="demo_simulator",
                    identity_confidence="confirmed",
                    created_at=now_str,
                    updated_at=now_str
                ))
            if len(results) >= limit:
                break

        # If query is not in base seeds, provide a safe synthetic asset candidate
        if not results and len(q) >= 1:
            sym_clean = query.upper().replace("$", "").strip()[:6]
            results.append(AssetOut(
                id=f"asset-{sym_clean.lower()}",
                provider_id=sym_clean,
                symbol=sym_clean,
                name=f"{sym_clean} Corp (Simulated)",
                asset_type="equity",
                exchange="NASDAQ",
                country="US",
                currency="USD",
                sector="General",
                timezone="America/New_York",
                is_active=True,
                provider="demo_simulator",
                identity_confidence="tentative",
                created_at=now_str,
                updated_at=now_str
            ))

        return results

    async def get_quote(self, asset: AssetOut) -> MarketQuoteOut:
        sym = asset.symbol.upper()
        base = DEMO_ASSET_BASELINES.get(sym, {
            "name": asset.name,
            "price": 100.0,
            "prev_close": 98.5,
            "vol": 1000000,
            "mcap": 1000000000,
            "exch": asset.exchange or "NASDAQ"
        })

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        price = round(base["price"], 2)
        prev_close = round(base["prev_close"], 2)
        change = round(price - prev_close, 2)
        pct_change = round((change / prev_close) * 100, 2) if prev_close else 0.0

        return MarketQuoteOut(
            id=f"quote-{asset.id}",
            asset_id=asset.id,
            symbol=sym,
            name=asset.name,
            price=price,
            previous_close=prev_close,
            change=change,
            change_percent=pct_change,
            volume=base["vol"],
            market_cap=base["mcap"],
            currency=asset.currency or "USD",
            exchange=asset.exchange or base["exch"],
            market_status=self.get_market_status(),
            data_status="SIMULATED DATA",
            timestamp=now_str,
            provider="demo_simulator",
            retrieved_at=now_str
        )

    async def get_history(
        self,
        asset: AssetOut,
        interval: str = "1d",
        range_str: str = "1mo"
    ) -> List[PriceBarOut]:
        sym = asset.symbol.upper()
        base_price = DEMO_ASSET_BASELINES.get(sym, {}).get("price", 100.0)

        # Determine points count
        points_map = {"1d": 24, "1w": 35, "1mo": 30, "3mo": 60, "1y": 52, "5y": 60}
        num_points = points_map.get(range_str.lower(), 30)

        bars: List[PriceBarOut] = []
        base_dt = datetime.now(timezone.utc) - timedelta(days=num_points if "m" in range_str or "y" in range_str else 7)

        # Generate deterministic smooth wave
        for i in range(num_points):
            dt = base_dt + timedelta(days=i)
            # deterministic oscillation
            drift = math.sin(i * 0.35) * (base_price * 0.03) + (i * 0.001 * base_price)
            close = round(base_price * 0.95 + drift, 2)
            open_p = round(close - math.cos(i * 0.4) * (base_price * 0.008), 2)
            high_p = round(max(open_p, close) + abs(math.sin(i)) * (base_price * 0.01), 2)
            low_p = round(min(open_p, close) - abs(math.cos(i)) * (base_price * 0.01), 2)
            vol = int(1000000 + math.sin(i) * 500000)

            bars.append(PriceBarOut(
                timestamp=dt.strftime("%Y-%m-%d %H:%M:%S"),
                open=open_p,
                high=high_p,
                low=low_p,
                close=close,
                volume=vol,
                is_adjusted=True,
                currency=asset.currency or "USD"
            ))

        return bars

    async def get_overview(self) -> MarketOverviewOut:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        status = self.get_market_status()

        # Build indices quotes
        indices_symbols = ["SPY", "QQQ", "BTC-USD"]
        indices: List[MarketQuoteOut] = []
        for s in indices_symbols:
            mock_asset = AssetOut(
                id=f"asset-{s.lower().replace('-', '_')}",
                symbol=s,
                name=DEMO_ASSET_BASELINES[s]["name"],
                exchange=DEMO_ASSET_BASELINES[s]["exch"],
                currency="USD"
            )
            indices.append(await self.get_quote(mock_asset))

        # Top gainers and losers from baseline seeds
        all_quotes = []
        for s in ["NVDA", "AAPL", "TSM", "MSFT"]:
            mock_asset = AssetOut(
                id=f"asset-{s.lower()}",
                symbol=s,
                name=DEMO_ASSET_BASELINES[s]["name"],
                exchange=DEMO_ASSET_BASELINES[s]["exch"],
                currency="USD"
            )
            all_quotes.append(await self.get_quote(mock_asset))

        gainers = [q for q in all_quotes if q.change >= 0]
        losers = [q for q in all_quotes if q.change < 0]

        sectors = [
            {"sector": "Technology", "performance": "+1.85%", "sentiment": "Bullish"},
            {"sector": "Semiconductors", "performance": "+2.40%", "sentiment": "Strong"},
            {"sector": "Financials", "performance": "+0.45%", "sentiment": "Neutral"},
            {"sector": "Energy", "performance": "-0.92%", "sentiment": "Cooling"},
            {"sector": "Healthcare", "performance": "-0.15%", "sentiment": "Defensive"}
        ]

        return MarketOverviewOut(
            market_status=status,
            timestamp=now_str,
            provider_status="SIMULATED DATA",
            indices=indices,
            gainers=gainers,
            losers=losers,
            sectors=sectors,
            related_news=[]
        )
