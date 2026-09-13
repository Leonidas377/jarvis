# ==========================================================================
# JARVIS Core Market Service
# Central orchestrator for market data, watchlists, charts, and resolution
# ==========================================================================

import time
import uuid
import json
from typing import List, Optional, Dict, Any
from server.database import get_db_connection
from server.models.schemas import (
    AssetOut, MarketQuoteOut, PriceBarOut, MarketOverviewOut,
    WatchlistOut, WatchlistItemOut
)
from server.services.market.yahoo_provider import LiveYahooMarketDataProvider
from server.services.market.demo_provider import DeterministicDemoMarketProvider
from server.services.market.alert_evaluator import MarketAlertEvaluator
from server.audit.logger import audit_logger

class MarketService:
    def __init__(self):
        self.live_provider = LiveYahooMarketDataProvider()
        self.demo_provider = DeterministicDemoMarketProvider()
        self._quote_cache: Dict[str, Dict[str, Any]] = {} # asset_id -> {"quote": quote, "ts": time}
        self._history_cache: Dict[str, Dict[str, Any]] = {} # f"{asset_id}_{range}" -> {"bars": bars, "ts": time}
        self._overview_cache: Optional[Dict[str, Any]] = None # {"overview": overview, "ts": time}

        self.QUOTE_CACHE_TTL = 60.0 # 60 seconds
        self.HISTORY_CACHE_TTL = 300.0 # 5 minutes
        self.OVERVIEW_CACHE_TTL = 120.0 # 2 minutes

    # ---------------- 1. Asset Resolution ----------------
    async def search_and_resolve_assets(self, query: str, limit: int = 10) -> List[AssetOut]:
        q = query.strip()
        if not q:
            return []

        # 1. Search locally in database
        local_assets: List[AssetOut] = []
        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT * FROM assets 
                WHERE symbol LIKE ? OR name LIKE ?
                ORDER BY symbol ASC LIMIT ?
            """, (f"%{q}%", f"%{q}%", limit))
            rows = await cur.fetchall()
            for r in rows:
                local_assets.append(AssetOut(
                    id=r["id"],
                    provider_id=r["provider_id"],
                    symbol=r["symbol"],
                    name=r["name"],
                    asset_type=r["asset_type"],
                    exchange=r["exchange"],
                    mic=r["mic"],
                    country=r["country"],
                    currency=r["currency"],
                    sector=r["sector"],
                    industry=r["industry"],
                    timezone=r["timezone"],
                    is_active=bool(r["is_active"]),
                    provider=r["provider"],
                    identity_confidence=r["identity_confidence"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                ))

        if local_assets:
            return local_assets

        # 2. Query provider
        provider_assets = await self.live_provider.search_assets(q, limit=limit)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Persist newly found assets to database
        async with get_db_connection() as db:
            for a in provider_assets:
                await db.execute("""
                    INSERT OR IGNORE INTO assets (
                        id, provider_id, symbol, name, asset_type, exchange, mic,
                        country, currency, sector, industry, timezone, is_active,
                        provider, identity_confidence, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    a.id, a.provider_id, a.symbol, a.name, a.asset_type, a.exchange,
                    a.mic, a.country, a.currency, a.sector, a.industry, a.timezone,
                    a.provider, a.identity_confidence, now_str, now_str
                ))
            await db.commit()

        return provider_assets

    async def get_asset_by_id(self, asset_id: str) -> Optional[AssetOut]:
        async with get_db_connection() as db:
            cur = await db.execute("SELECT * FROM assets WHERE id = ? OR symbol = ?", (asset_id, asset_id.upper()))
            r = await cur.fetchone()
            if not r:
                return None
            return AssetOut(
                id=r["id"],
                provider_id=r["provider_id"],
                symbol=r["symbol"],
                name=r["name"],
                asset_type=r["asset_type"],
                exchange=r["exchange"],
                mic=r["mic"],
                country=r["country"],
                currency=r["currency"],
                sector=r["sector"],
                industry=r["industry"],
                timezone=r["timezone"],
                is_active=bool(r["is_active"]),
                provider=r["provider"],
                identity_confidence=r["identity_confidence"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )

    # ---------------- 2. Quotes & Caching ----------------
    async def get_asset_quote(self, asset: AssetOut, force_refresh: bool = False) -> MarketQuoteOut:
        now = time.time()
        # Check cache
        if not force_refresh and asset.id in self._quote_cache:
            entry = self._quote_cache[asset.id]
            if (now - entry["ts"]) < self.QUOTE_CACHE_TTL:
                return entry["quote"]

        # Retrieve quote from provider
        quote = await self.live_provider.get_quote(asset)

        # Cache quote
        self._quote_cache[asset.id] = {"quote": quote, "ts": now}

        # Check informational price alerts
        try:
            await MarketAlertEvaluator.evaluate_alerts_for_quote(quote)
        except Exception as e:
            print(f"[JARVIS Market] Alert evaluation: {e}")

        # Persist latest quote to DB
        try:
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            async with get_db_connection() as db:
                await db.execute("""
                    INSERT OR REPLACE INTO market_quotes (
                        id, asset_id, price, previous_close, change, change_percent,
                        volume, market_cap, currency, exchange, market_status,
                        data_status, timestamp, provider, retrieved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"quote-{asset.id}", asset.id, quote.price, quote.previous_close,
                    quote.change, quote.change_percent, quote.volume, quote.market_cap,
                    quote.currency, quote.exchange, quote.market_status,
                    quote.data_status, quote.timestamp, quote.provider, now_str
                ))
                await db.commit()
        except Exception as ex:
            print(f"[JARVIS Market] DB quote save: {ex}")

        return quote

    # ---------------- 3. Historical Bars & Charts ----------------
    async def get_asset_history(
        self,
        asset: AssetOut,
        interval: str = "1d",
        range_str: str = "1mo",
        force_refresh: bool = False
    ) -> List[PriceBarOut]:
        now = time.time()
        cache_key = f"{asset.id}_{range_str.lower()}_{interval.lower()}"
        if not force_refresh and cache_key in self._history_cache:
            entry = self._history_cache[cache_key]
            if (now - entry["ts"]) < self.HISTORY_CACHE_TTL:
                return entry["bars"]

        bars = await self.live_provider.get_history(asset, interval, range_str)
        self._history_cache[cache_key] = {"bars": bars, "ts": now}
        return bars

    # ---------------- 4. Dashboard Overview ----------------
    async def get_market_overview(self, force_refresh: bool = False) -> MarketOverviewOut:
        now = time.time()
        if not force_refresh and self._overview_cache:
            if (now - self._overview_cache["ts"]) < self.OVERVIEW_CACHE_TTL:
                return self._overview_cache["overview"]

        overview = await self.live_provider.get_overview()
        self._overview_cache = {"overview": overview, "ts": now}
        return overview

    # ---------------- 5. Watchlist Management ----------------
    async def get_user_watchlists(self, user_id: str) -> List[WatchlistOut]:
        watchlists: List[WatchlistOut] = []
        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT * FROM watchlists 
                WHERE user_id = ? 
                ORDER BY sort_order ASC, created_at ASC
            """, (user_id,))
            wl_rows = await cur.fetchall()

            for wl in wl_rows:
                # Load items
                cur_i = await db.execute("""
                    SELECT wi.id, wi.watchlist_id, wi.asset_id, wi.sort_order, wi.added_at,
                           a.symbol, a.name, a.exchange, a.currency, a.asset_type, a.sector
                    FROM watchlist_items wi
                    JOIN assets a ON wi.asset_id = a.id
                    WHERE wi.watchlist_id = ?
                    ORDER BY wi.sort_order ASC, wi.added_at ASC
                """, (wl["id"],))
                i_rows = await cur_i.fetchall()

                items_out: List[WatchlistItemOut] = []
                for ir in i_rows:
                    asset_obj = AssetOut(
                        id=ir["asset_id"],
                        symbol=ir["symbol"],
                        name=ir["name"],
                        exchange=ir["exchange"],
                        currency=ir["currency"],
                        asset_type=ir["asset_type"],
                        sector=ir["sector"]
                    )
                    # Fetch quote (cached)
                    quote_obj = await self.get_asset_quote(asset_obj)
                    items_out.append(WatchlistItemOut(
                        id=ir["id"],
                        watchlist_id=wl["id"],
                        asset_id=ir["asset_id"],
                        sort_order=ir["sort_order"],
                        added_at=ir["added_at"],
                        asset=asset_obj,
                        quote=quote_obj
                    ))

                watchlists.append(WatchlistOut(
                    id=wl["id"],
                    user_id=user_id,
                    name=wl["name"],
                    sort_order=wl["sort_order"],
                    items=items_out,
                    created_at=wl["created_at"],
                    updated_at=wl["updated_at"]
                ))

        return watchlists

    async def create_watchlist(self, user_id: str, name: str) -> WatchlistOut:
        wl_id = f"wl-{uuid.uuid4().hex[:12]}"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO watchlists (id, user_id, name, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (wl_id, user_id, name.strip(), now_str, now_str))
            await db.commit()

        await audit_logger.log_event(
            event_type="MARKET_WATCHLIST_CREATED",
            action="market.watchlist_create",
            user_id=user_id,
            resource_id=wl_id,
            details={"name": name}
        )

        return WatchlistOut(
            id=wl_id,
            user_id=user_id,
            name=name.strip(),
            sort_order=0,
            items=[],
            created_at=now_str,
            updated_at=now_str
        )

    async def update_watchlist(self, user_id: str, watchlist_id: str, name: Optional[str] = None, sort_order: Optional[int] = None) -> Optional[WatchlistOut]:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        async with get_db_connection() as db:
            cur = await db.execute("SELECT * FROM watchlists WHERE id = ? AND user_id = ?", (watchlist_id, user_id))
            wl = await cur.fetchone()
            if not wl:
                return None

            new_name = name.strip() if name is not None else wl["name"]
            new_sort = sort_order if sort_order is not None else wl["sort_order"]

            await db.execute("""
                UPDATE watchlists SET name = ?, sort_order = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (new_name, new_sort, now_str, watchlist_id, user_id))
            await db.commit()

        return await self.get_watchlist_by_id(user_id, watchlist_id)

    async def get_watchlist_by_id(self, user_id: str, watchlist_id: str) -> Optional[WatchlistOut]:
        wls = await self.get_user_watchlists(user_id)
        for w in wls:
            if w.id == watchlist_id:
                return w
        return None

    async def delete_watchlist(self, user_id: str, watchlist_id: str) -> bool:
        async with get_db_connection() as db:
            cur = await db.execute("DELETE FROM watchlists WHERE id = ? AND user_id = ?", (watchlist_id, user_id))
            await db.commit()
            if cur.rowcount > 0:
                await audit_logger.log_event(
                    event_type="MARKET_WATCHLIST_DELETED",
                    action="market.watchlist_delete",
                    user_id=user_id,
                    resource_id=watchlist_id
                )
                return True
        return False

    async def add_watchlist_item(self, user_id: str, watchlist_id: str, asset_id: str) -> Optional[WatchlistItemOut]:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        item_id = f"wli-{uuid.uuid4().hex[:12]}"

        # Verify user owns watchlist
        async with get_db_connection() as db:
            cur = await db.execute("SELECT id FROM watchlists WHERE id = ? AND user_id = ?", (watchlist_id, user_id))
            if not await cur.fetchone():
                return None

            # Verify asset exists
            cur_a = await db.execute("SELECT * FROM assets WHERE id = ? OR symbol = ?", (asset_id, asset_id.upper()))
            a_row = await cur_a.fetchone()
            if not a_row:
                return None

            real_asset_id = a_row["id"]

            # Add item
            await db.execute("""
                INSERT OR IGNORE INTO watchlist_items (id, watchlist_id, asset_id, sort_order, added_at)
                VALUES (?, ?, ?, 0, ?)
            """, (item_id, watchlist_id, real_asset_id, now_str))
            await db.commit()

        asset_obj = await self.get_asset_by_id(real_asset_id)
        quote_obj = await self.get_asset_quote(asset_obj) if asset_obj else None

        return WatchlistItemOut(
            id=item_id,
            watchlist_id=watchlist_id,
            asset_id=real_asset_id,
            sort_order=0,
            added_at=now_str,
            asset=asset_obj,
            quote=quote_obj
        )

    async def remove_watchlist_item(self, user_id: str, watchlist_id: str, item_id: str) -> bool:
        async with get_db_connection() as db:
            # Verify user owns watchlist
            cur = await db.execute("SELECT id FROM watchlists WHERE id = ? AND user_id = ?", (watchlist_id, user_id))
            if not await cur.fetchone():
                return False

            cur_del = await db.execute("DELETE FROM watchlist_items WHERE (id = ? OR asset_id = ?) AND watchlist_id = ?", (item_id, item_id, watchlist_id))
            await db.commit()
            return cur_del.rowcount > 0

    async def reorder_watchlist_items(self, user_id: str, watchlist_id: str, item_ids: List[str]) -> bool:
        async with get_db_connection() as db:
            cur = await db.execute("SELECT id FROM watchlists WHERE id = ? AND user_id = ?", (watchlist_id, user_id))
            if not await cur.fetchone():
                return False

            for order_idx, i_id in enumerate(item_ids):
                await db.execute("UPDATE watchlist_items SET sort_order = ? WHERE id = ? AND watchlist_id = ?", (order_idx, i_id, watchlist_id))
            await db.commit()
            return True

# Singleton instance
market_service = MarketService()
