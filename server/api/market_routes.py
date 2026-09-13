# ==========================================================================
# JARVIS Financial Markets & Read-Only Market Intelligence API Routes
# Strictly Read-Only: No broker write operations or live trading tools
# ==========================================================================

import time
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import (
    AssetOut, MarketQuoteOut, MarketHistoryOut, PriceBarOut,
    MarketOverviewOut, WatchlistCreate, WatchlistUpdate, WatchlistOut,
    WatchlistItemAdd, WatchlistItemOut, WatchlistReorderIn,
    MarketAlertCreate, MarketAlertUpdate, MarketAlertOut,
    MarketInsightCreate, MarketInsightOut, ReadOnlyPortfolioOut
)
from server.services.market import (
    market_service, MarketNewsCorrelator, MarketInsightService
)
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/markets", tags=["Financial Markets & Read-Only Intelligence"])

# ----------------- 1. Market Dashboard & Status -----------------
@router.get("/overview", response_model=MarketOverviewOut)
async def get_market_overview(user: dict = Depends(get_optional_user)):
    return await market_service.get_market_overview()

@router.post("/refresh", response_model=MarketOverviewOut)
async def refresh_market_overview(user: dict = Depends(get_optional_user)):
    return await market_service.get_market_overview(force_refresh=True)

@router.get("/status")
async def get_market_status(user: dict = Depends(get_optional_user)):
    status_str = market_service.live_provider.get_market_status()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "status": status_str,
        "timestamp": now_str,
        "trading_enabled": False,
        "trading_boundary_notice": "LIVE TRADING WILL BE IMPLEMENTED IN A LATER PHASE",
        "broker_status": "READ_ONLY_MODE"
    }


# ----------------- 2. Asset Search & Identity Resolution -----------------
@router.get("/assets/search", response_model=List[AssetOut])
async def search_assets(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, le=25),
    user: dict = Depends(get_optional_user)
):
    assets = await market_service.search_and_resolve_assets(query, limit=limit)
    return assets


# ----------------- 3. Watchlists (CRUD & Items) -----------------
@router.get("/watchlists", response_model=List[WatchlistOut])
async def list_user_watchlists(user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    return await market_service.get_user_watchlists(user_id)

@router.post("/watchlists", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
async def create_watchlist(payload: WatchlistCreate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Watchlist name cannot be empty.")
    return await market_service.create_watchlist(user_id, name_clean)

@router.get("/watchlists/{watchlist_id}", response_model=WatchlistOut)
async def get_watchlist(watchlist_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    wl = await market_service.get_watchlist_by_id(user_id, watchlist_id)
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    return wl

@router.patch("/watchlists/{watchlist_id}", response_model=WatchlistOut)
async def update_watchlist(watchlist_id: str, payload: WatchlistUpdate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    wl = await market_service.update_watchlist(user_id, watchlist_id, name=payload.name, sort_order=payload.sort_order)
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    return wl

@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    success = await market_service.delete_watchlist(user_id, watchlist_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    return {"success": True, "message": "Watchlist deleted.", "watchlist_id": watchlist_id}

@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
async def add_asset_to_watchlist(watchlist_id: str, payload: WatchlistItemAdd, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    item = await market_service.add_watchlist_item(user_id, watchlist_id, payload.asset_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist or Asset not found.")
    return item

@router.delete("/watchlists/{watchlist_id}/items/{item_id}")
async def remove_asset_from_watchlist(watchlist_id: str, item_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    success = await market_service.remove_watchlist_item(user_id, watchlist_id, item_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item or Watchlist not found.")
    return {"success": True, "message": "Item removed from watchlist.", "item_id": item_id}

@router.patch("/watchlists/{watchlist_id}/reorder")
async def reorder_watchlist(watchlist_id: str, payload: WatchlistReorderIn, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    success = await market_service.reorder_watchlist_items(user_id, watchlist_id, payload.item_ids)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    return {"success": True, "reordered_count": len(payload.item_ids)}

@router.post("/watchlists/{watchlist_id}/refresh", response_model=WatchlistOut)
async def refresh_watchlist(watchlist_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    wl = await market_service.get_watchlist_by_id(user_id, watchlist_id)
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")
    # Force quote refresh
    for it in wl.items:
        if it.asset:
            it.quote = await market_service.get_asset_quote(it.asset, force_refresh=True)
    return wl


# ----------------- 4. Informational Price Alerts -----------------
@router.get("/alerts", response_model=List[MarketAlertOut])
async def list_market_alerts(user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    alerts: List[MarketAlertOut] = []
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT ma.*, a.symbol 
            FROM market_alerts ma
            LEFT JOIN assets a ON ma.asset_id = a.id
            WHERE ma.user_id = ?
            ORDER BY ma.created_at DESC
        """, (user_id,))
        rows = await cur.fetchall()
        for r in rows:
            alerts.append(MarketAlertOut(
                id=r["id"],
                user_id=r["user_id"],
                asset_id=r["asset_id"],
                symbol=r["symbol"],
                condition_type=r["condition_type"],
                threshold=r["threshold"],
                cooldown_minutes=r["cooldown_minutes"],
                is_enabled=bool(r["is_enabled"]),
                last_triggered_at=r["last_triggered_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
    return alerts

@router.post("/alerts", response_model=MarketAlertOut, status_code=status.HTTP_201_CREATED)
async def create_market_alert(payload: MarketAlertCreate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    alert_id = f"alert-{uuid.uuid4().hex[:12]}"
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Verify asset
    asset = await market_service.get_asset_by_id(payload.asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO market_alerts (
                id, user_id, asset_id, condition_type, threshold,
                cooldown_minutes, is_enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id, user_id, asset.id, payload.condition_type,
            payload.threshold, payload.cooldown_minutes,
            1 if payload.is_enabled else 0, now_str, now_str
        ))
        await db.commit()

    await audit_logger.log_event(
        event_type="MARKET_ALERT_CREATED",
        action="market.alert_create",
        user_id=user_id,
        resource_id=alert_id,
        details={"symbol": asset.symbol, "condition": payload.condition_type, "threshold": payload.threshold}
    )

    return MarketAlertOut(
        id=alert_id,
        user_id=user_id,
        asset_id=asset.id,
        symbol=asset.symbol,
        condition_type=payload.condition_type,
        threshold=payload.threshold,
        cooldown_minutes=payload.cooldown_minutes,
        is_enabled=payload.is_enabled,
        last_triggered_at=None,
        created_at=now_str,
        updated_at=now_str
    )

@router.patch("/alerts/{alert_id}", response_model=MarketAlertOut)
async def update_market_alert(alert_id: str, payload: MarketAlertUpdate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM market_alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

        new_cond = payload.condition_type or r["condition_type"]
        new_thresh = payload.threshold if payload.threshold is not None else r["threshold"]
        new_cool = payload.cooldown_minutes if payload.cooldown_minutes is not None else r["cooldown_minutes"]
        new_en = (1 if payload.is_enabled else 0) if payload.is_enabled is not None else r["is_enabled"]

        await db.execute("""
            UPDATE market_alerts SET condition_type = ?, threshold = ?, cooldown_minutes = ?, is_enabled = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (new_cond, new_thresh, new_cool, new_en, now_str, alert_id, user_id))
        await db.commit()

    asset = await market_service.get_asset_by_id(r["asset_id"])
    return MarketAlertOut(
        id=alert_id,
        user_id=user_id,
        asset_id=r["asset_id"],
        symbol=asset.symbol if asset else None,
        condition_type=new_cond,
        threshold=new_thresh,
        cooldown_minutes=new_cool,
        is_enabled=bool(new_en),
        last_triggered_at=r["last_triggered_at"],
        created_at=r["created_at"],
        updated_at=now_str
    )

@router.delete("/alerts/{alert_id}")
async def delete_market_alert(alert_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM market_alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    return {"success": True, "message": "Alert deleted.", "alert_id": alert_id}


# ----------------- 5. Read-Only Portfolio Area -----------------
@router.get("/portfolio", response_model=ReadOnlyPortfolioOut)
async def get_read_only_portfolio(user: dict = Depends(get_optional_user)):
    return ReadOnlyPortfolioOut(
        status="BROKER_READ_ONLY_NOT_CONFIGURED",
        message="Broker read-only telemetry is not configured. Live broker order placement and trading write operations are disabled.",
        is_configured=False,
        holdings=[],
        buying_power=None,
        cash_balance=None
    )

@router.get("/portfolio/holdings")
async def get_portfolio_holdings(user: dict = Depends(get_optional_user)):
    return {
        "status": "BROKER_READ_ONLY_NOT_CONFIGURED",
        "holdings": []
    }

@router.get("/portfolio/history")
async def get_portfolio_history(user: dict = Depends(get_optional_user)):
    return {
        "status": "BROKER_READ_ONLY_NOT_CONFIGURED",
        "history": []
    }


# ----------------- 6. Market Insights -----------------
@router.post("/insights", response_model=MarketInsightOut, status_code=status.HTTP_201_CREATED)
async def generate_market_insight(payload: MarketInsightCreate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    asset = None
    quote = None
    related_news = []

    if payload.asset_id:
        asset = await market_service.get_asset_by_id(payload.asset_id)
        if asset:
            quote = await market_service.get_asset_quote(asset)
            related_news = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=3)

    insight = await MarketInsightService.generate_insight(
        question=payload.question,
        asset=asset,
        quote=quote,
        related_news=related_news,
        user_id=user_id,
        time_window=payload.time_window
    )
    return insight

@router.get("/insights/{insight_id}", response_model=MarketInsightOut)
async def get_market_insight(insight_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM market_insights WHERE id = ? AND user_id = ?", (insight_id, user_id))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market insight not found.")

        return MarketInsightOut(
            id=r["id"],
            user_id=r["user_id"],
            question=r["question"],
            direct_answer=r["direct_answer"],
            observed_data=json.loads(r["observed_data_json"] or "{}"),
            possible_explanations=json.loads(r["possible_explanations_json"] or "[]"),
            uncertainty_notes=r["uncertainty_notes"],
            scenarios=json.loads(r["scenarios_json"] or "[]"),
            citations=json.loads(r["citations_json"] or "[]"),
            market_disclaimer=r["market_disclaimer"],
            provider_name=r["provider_name"],
            model_name=r["model_name"],
            created_at=r["created_at"]
        )


# ----------------- 7. Asset Detail, Quotes, Charts & Correlated News -----------------
@router.get("/assets/{asset_id}", response_model=AssetOut)
async def get_asset_detail(asset_id: str, user: dict = Depends(get_optional_user)):
    asset = await market_service.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return asset

@router.get("/assets/{asset_id}/quote", response_model=MarketQuoteOut)
async def get_asset_quote(asset_id: str, user: dict = Depends(get_optional_user)):
    asset = await market_service.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return await market_service.get_asset_quote(asset)

@router.get("/assets/{asset_id}/history", response_model=MarketHistoryOut)
async def get_asset_history(
    asset_id: str,
    interval: str = Query("1d"),
    range: str = Query("1mo"),
    user: dict = Depends(get_optional_user)
):
    asset = await market_service.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    bars = await market_service.get_asset_history(asset, interval=interval, range_str=range)
    return MarketHistoryOut(
        asset_id=asset.id,
        symbol=asset.symbol,
        interval=interval,
        range=range,
        bars=bars,
        provider=asset.provider,
        data_status="LIVE DATA" if any(b.volume > 0 for b in bars) else "SIMULATED DATA"
    )

@router.get("/assets/{asset_id}/news")
async def get_asset_related_news(asset_id: str, limit: int = Query(5, le=10), user: dict = Depends(get_optional_user)):
    asset = await market_service.get_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    correlated = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=limit)
    return correlated

@router.get("/assets/{asset_id}/insights", response_model=List[MarketInsightOut])
async def get_asset_insights(asset_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    insights = []
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT * FROM market_insights 
            WHERE user_id = ? AND asset_ids_json LIKE ?
            ORDER BY created_at DESC LIMIT 5
        """, (user_id, f"%{asset_id}%"))
        rows = await cur.fetchall()
        for r in rows:
            insights.append(MarketInsightOut(
                id=r["id"],
                user_id=r["user_id"],
                question=r["question"],
                direct_answer=r["direct_answer"],
                observed_data=json.loads(r["observed_data_json"] or "{}"),
                possible_explanations=json.loads(r["possible_explanations_json"] or "[]"),
                uncertainty_notes=r["uncertainty_notes"],
                scenarios=json.loads(r["scenarios_json"] or "[]"),
                citations=json.loads(r["citations_json"] or "[]"),
                market_disclaimer=r["market_disclaimer"],
                provider_name=r["provider_name"],
                model_name=r["model_name"],
                created_at=r["created_at"]
            ))
    return insights
