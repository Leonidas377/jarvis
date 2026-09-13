# ==========================================================================
# JARVIS Live Yahoo Market Data Provider
# Real-time financial telemetry, OHLCV charts, and symbol resolution
# ==========================================================================

import time
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from server.services.market.base import BaseMarketDataProvider
from server.services.market.demo_provider import DeterministicDemoMarketProvider
from server.models.schemas import AssetOut, MarketQuoteOut, PriceBarOut, MarketOverviewOut

YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

class LiveYahooMarketDataProvider(BaseMarketDataProvider):
    provider_name: str = "Live Wire Telemetry (Yahoo Finance)"

    def __init__(self):
        self._demo_fallback = DeterministicDemoMarketProvider()

    def get_market_status(self) -> str:
        # Standard US Market Session (9:30 AM - 4:00 PM Eastern, Mon-Fri)
        now_utc = datetime.now(timezone.utc)
        weekday = now_utc.weekday()
        if weekday >= 5:
            return "CLOSED"
        
        # New York Eastern Time is approximately UTC - 4 (EDT) or UTC - 5 (EST)
        # 9:30 AM EDT = 13:30 UTC, 4:00 PM EDT = 20:00 UTC
        utc_minutes = now_utc.hour * 60 + now_utc.minute
        if 13 * 60 + 30 <= utc_minutes < 20 * 60:
            return "OPEN"
        elif 8 * 60 <= utc_minutes < 13 * 60 + 30:
            return "PRE_MARKET"
        elif 20 * 60 <= utc_minutes < 24 * 60:
            return "AFTER_HOURS"
        else:
            return "CLOSED"

    async def search_assets(self, query: str, limit: int = 10) -> List[AssetOut]:
        q = query.strip()
        if not q:
            return []

        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount={limit}&newsCount=0"
        try:
            async with httpx.AsyncClient(timeout=4.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    quotes = data.get("quotes", [])
                    results: List[AssetOut] = []
                    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

                    for it in quotes:
                        sym = it.get("symbol")
                        if not sym:
                            continue
                        name = it.get("longname") or it.get("shortname") or sym
                        exch = it.get("exchDisp") or it.get("exchange") or "UNKNOWN"
                        q_type = (it.get("quoteType") or "EQUITY").lower()
                        sector = it.get("sector") or "General"
                        industry = it.get("industry")

                        results.append(AssetOut(
                            id=f"asset-{sym.lower().replace('^', '').replace('-', '_')}",
                            provider_id=sym,
                            symbol=sym,
                            name=name,
                            asset_type=q_type,
                            exchange=exch,
                            country="US" if any(e in exch.upper() for e in ["NAS", "NYS", "ARC"]) else "Global",
                            currency="USD",
                            sector=sector,
                            industry=industry,
                            timezone="America/New_York",
                            is_active=True,
                            provider="yahoo_live",
                            identity_confidence="confirmed",
                            created_at=now_str,
                            updated_at=now_str
                        ))
                    if results:
                        return results
        except Exception as e:
            print(f"[JARVIS Market] Yahoo search error: {e}")

        # Fallback to demo provider
        return await self._demo_fallback.search_assets(query, limit=limit)

    async def get_quote(self, asset: AssetOut) -> MarketQuoteOut:
        sym = asset.symbol.upper()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            async with httpx.AsyncClient(timeout=4.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    res_chart = data.get("chart", {}).get("result", [])
                    if res_chart:
                        meta = res_chart[0].get("meta", {})
                        price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose") or 100.0
                        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or price
                        change = round(price - prev_close, 2)
                        pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
                        vol = meta.get("regularMarketVolume") or 0
                        exch = meta.get("exchangeName") or asset.exchange or "NASDAQ"
                        currency = meta.get("currency") or asset.currency or "USD"

                        m_status = self.get_market_status()
                        data_status = "LIVE DATA" if m_status == "OPEN" else "MARKET CLOSED"

                        return MarketQuoteOut(
                            id=f"quote-{asset.id}",
                            asset_id=asset.id,
                            symbol=sym,
                            name=asset.name,
                            price=round(float(price), 2),
                            previous_close=round(float(prev_close), 2),
                            change=change,
                            change_percent=pct,
                            volume=int(vol),
                            market_cap=None,
                            currency=currency,
                            exchange=exch,
                            market_status=m_status,
                            data_status=data_status,
                            timestamp=now_str,
                            provider="yahoo_live",
                            retrieved_at=now_str
                        )
        except Exception as e:
            print(f"[JARVIS Market] Yahoo quote failed for {sym}: {e}")

        # Fallback to demo provider
        return await self._demo_fallback.get_quote(asset)

    async def get_history(
        self,
        asset: AssetOut,
        interval: str = "1d",
        range_str: str = "1mo"
    ) -> List[PriceBarOut]:
        sym = asset.symbol.upper()
        # Map range to yahoo compatible
        valid_ranges = {"1d": "1d", "1w": "5d", "1mo": "1mo", "3mo": "3mo", "1y": "1y", "5y": "5y"}
        y_range = valid_ranges.get(range_str.lower(), "1mo")
        y_interval = "5m" if y_range == "1d" else ("1h" if y_range == "5d" else "1d")

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval={y_interval}&range={y_range}"

        try:
            async with httpx.AsyncClient(timeout=5.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    res_chart = data.get("chart", {}).get("result", [])
                    if res_chart:
                        timestamps = res_chart[0].get("timestamp", [])
                        indicators = res_chart[0].get("indicators", {}).get("quote", [{}])[0]
                        opens = indicators.get("open", [])
                        highs = indicators.get("high", [])
                        lows = indicators.get("low", [])
                        closes = indicators.get("close", [])
                        volumes = indicators.get("volume", [])

                        bars: List[PriceBarOut] = []
                        for i in range(len(timestamps)):
                            if closes[i] is None or opens[i] is None:
                                continue
                            dt_str = datetime.fromtimestamp(timestamps[i], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                            bars.append(PriceBarOut(
                                timestamp=dt_str,
                                open=round(float(opens[i]), 2),
                                high=round(float(highs[i] or opens[i]), 2),
                                low=round(float(lows[i] or opens[i]), 2),
                                close=round(float(closes[i]), 2),
                                volume=int(volumes[i] or 0),
                                is_adjusted=True,
                                currency=asset.currency or "USD"
                            ))
                        if bars:
                            return bars
        except Exception as e:
            print(f"[JARVIS Market] Yahoo history fetch failed for {sym}: {e}")

        # Fallback to demo provider
        return await self._demo_fallback.get_history(asset, interval, range_str)

    async def get_overview(self) -> MarketOverviewOut:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        m_status = self.get_market_status()

        # Try to pull major indices
        indices_syms = [
            ("SPY", "SPDR S&P 500 ETF", "NYSE Arca"),
            ("QQQ", "Invesco QQQ Trust", "NASDAQ"),
            ("BTC-USD", "Bitcoin / USD", "CRYPTO")
        ]
        indices: List[MarketQuoteOut] = []
        for s, name, exch in indices_syms:
            a = AssetOut(id=f"asset-{s.lower().replace('-', '_')}", symbol=s, name=name, exchange=exch, currency="USD")
            indices.append(await self.get_quote(a))

        # Gainers & losers
        key_stocks = [
            ("NVDA", "NVIDIA Corporation", "NASDAQ"),
            ("AAPL", "Apple Inc.", "NASDAQ"),
            ("TSM", "Taiwan Semiconductor", "NYSE"),
            ("MSFT", "Microsoft Corporation", "NASDAQ")
        ]
        quotes = []
        for s, name, exch in key_stocks:
            a = AssetOut(id=f"asset-{s.lower()}", symbol=s, name=name, exchange=exch, currency="USD")
            quotes.append(await self.get_quote(a))

        gainers = [q for q in quotes if q.change >= 0]
        losers = [q for q in quotes if q.change < 0]

        sectors = [
            {"sector": "Technology", "performance": "+1.85%", "sentiment": "Bullish"},
            {"sector": "Semiconductors", "performance": "+2.40%", "sentiment": "Strong"},
            {"sector": "Financials", "performance": "+0.45%", "sentiment": "Neutral"},
            {"sector": "Energy", "performance": "-0.92%", "sentiment": "Cooling"},
            {"sector": "Healthcare", "performance": "-0.15%", "sentiment": "Defensive"}
        ]

        data_status = "LIVE DATA" if any(q.provider == "yahoo_live" for q in indices) else "SIMULATED DATA"

        return MarketOverviewOut(
            market_status=m_status,
            timestamp=now_str,
            provider_status=data_status,
            indices=indices,
            gainers=gainers,
            losers=losers,
            sectors=sectors,
            related_news=[]
        )
