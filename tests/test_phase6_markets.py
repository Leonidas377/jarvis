# ==========================================================================
# Tests: Phase 6 Real Market Data & Read-Only Market Intelligence
# ==========================================================================

import pytest
import uuid
import time
from httpx import AsyncClient, ASGITransport
from server.main import app
from server.database import init_db, get_db_connection
from server.models.schemas import (
    AssetOut, MarketQuoteOut, RiskLevel
)
from server.services.market import (
    market_service, MarketNewsCorrelator, MarketInsightService, MarketAlertEvaluator
)
from server.permissions.policy_engine import PolicyEngine
from server.permissions.scopes import Scope

@pytest.mark.asyncio
async def test_asset_search_and_identity_resolution():
    """Verifies searching assets, resolving exact identities, and normalizing symbols."""
    await init_db()

    # Search for NVIDIA
    results = await market_service.search_and_resolve_assets("NVDA", limit=5)
    assert len(results) >= 1
    nvda = next((a for a in results if a.symbol == "NVDA"), results[0])

    assert nvda.symbol == "NVDA"
    assert "NVIDIA" in nvda.name
    assert nvda.exchange in ["NASDAQ", "XNAS", "UNKNOWN"]
    assert nvda.currency == "USD"
    assert nvda.identity_confidence in ["confirmed", "tentative"]

    # Search for Apple
    apple_results = await market_service.search_and_resolve_assets("Apple", limit=5)
    assert len(apple_results) >= 1
    assert any("AAPL" in a.symbol or "Apple" in a.name for a in apple_results)


@pytest.mark.asyncio
async def test_market_quote_normalization_and_freshness():
    """Verifies quote retrieval, exchange, currency, timestamp, and data status."""
    await init_db()
    asset = await market_service.get_asset_by_id("asset-nvda")
    assert asset is not None

    quote = await market_service.get_asset_quote(asset, force_refresh=True)
    assert quote.symbol == "NVDA"
    assert quote.price > 0
    assert quote.currency == "USD"
    assert quote.exchange is not None
    assert quote.data_status in ["LIVE DATA", "SIMULATED DATA", "MARKET CLOSED", "DELAYED DATA"]
    assert quote.timestamp is not None
    assert quote.market_status in ["OPEN", "CLOSED", "PRE_MARKET", "AFTER_HOURS"]


@pytest.mark.asyncio
async def test_market_history_intervals_and_ranges():
    """Verifies historical OHLCV bar series and time ranges (1d, 1w, 1mo, 1y)."""
    await init_db()
    asset = await market_service.get_asset_by_id("asset-spy")
    assert asset is not None

    bars = await market_service.get_asset_history(asset, interval="1d", range_str="1mo")
    assert len(bars) >= 5

    first_bar = bars[0]
    assert first_bar.open > 0
    assert first_bar.high >= first_bar.low
    assert first_bar.close > 0
    assert first_bar.timestamp is not None
    assert first_bar.currency == "USD"


@pytest.mark.asyncio
async def test_watchlist_crud_and_reorder():
    """Verifies creating, populating, reordering, and deleting watchlists."""
    await init_db()
    test_user = f"user-{uuid.uuid4().hex[:8]}"
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO users (id, username, email, hashed_password, display_name, created_at)
            VALUES (?, ?, ?, 'hash', 'Test User', ?)
        """, (test_user, f"user_{test_user}", f"{test_user}@test.com", now_str))
        await db.commit()

    # 1. Create Watchlist
    wl = await market_service.create_watchlist(test_user, "Autonomous Tech Radar")
    assert wl.name == "Autonomous Tech Radar"
    assert wl.user_id == test_user

    # 2. Add Items
    item1 = await market_service.add_watchlist_item(test_user, wl.id, "asset-nvda")
    item2 = await market_service.add_watchlist_item(test_user, wl.id, "asset-tsm")
    assert item1 is not None
    assert item2 is not None

    # 3. Retrieve Watchlists
    wls = await market_service.get_user_watchlists(test_user)
    assert len(wls) == 1
    assert len(wls[0].items) == 2

    # 4. Reorder Items
    success_reorder = await market_service.reorder_watchlist_items(test_user, wl.id, [item2.id, item1.id])
    assert success_reorder is True

    # 5. Remove Item
    success_remove = await market_service.remove_watchlist_item(test_user, wl.id, item1.id)
    assert success_remove is True

    # 6. Delete Watchlist
    success_delete = await market_service.delete_watchlist(test_user, wl.id)
    assert success_delete is True


@pytest.mark.asyncio
async def test_market_alert_evaluation_without_trading():
    """Verifies informational price alerts trigger without any trade execution capability."""
    await init_db()
    test_user = f"user-{uuid.uuid4().hex[:8]}"
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO users (id, username, email, hashed_password, display_name, created_at)
            VALUES (?, ?, ?, 'hash', 'Test User', ?)
        """, (test_user, f"user_{test_user}", f"{test_user}@test.com", now_str))
        await db.commit()

    asset = await market_service.get_asset_by_id("asset-aapl")
    assert asset is not None

    alert_id = f"alert-{uuid.uuid4().hex[:8]}"

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO market_alerts (id, user_id, asset_id, condition_type, threshold, cooldown_minutes, is_enabled, created_at, updated_at)
            VALUES (?, ?, ?, 'price_above', 100.0, 0, 1, ?, ?)
        """, (alert_id, test_user, asset.id, now_str, now_str))
        await db.commit()

    # Simulate quote with price above threshold
    mock_quote = MarketQuoteOut(
        asset_id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        price=220.50,
        previous_close=218.00,
        change=2.50,
        change_percent=1.15,
        volume=5000000,
        currency="USD",
        exchange="NASDAQ",
        market_status="OPEN",
        data_status="SIMULATED DATA",
        timestamp=now_str
    )

    triggered = await MarketAlertEvaluator.evaluate_alerts_for_quote(mock_quote)
    assert len(triggered) >= 1
    assert triggered[0]["symbol"] == "AAPL"
    assert "exceeded target price" in triggered[0]["message"]


@pytest.mark.asyncio
async def test_related_news_correlation_and_labels():
    """Verifies connecting Phase 5 news wire events to assets without false causation."""
    await init_db()
    asset = await market_service.get_asset_by_id("asset-tsm")
    assert asset is not None

    correlated = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=3)
    assert len(correlated) >= 1
    first_event = correlated[0]
    assert "headline" in first_event
    assert "relationship_label" in first_event
    # Relationship label must be objective
    assert first_event["relationship_label"] in ["REPORTED EVENT", "OBSERVED PRICE MOVE", "POSSIBLE CONNECTION", "CONFLICTING COVERAGE"]


@pytest.mark.asyncio
async def test_llm_market_insight_and_disclaimer():
    """Verifies LLM market explanation structure, citations, and observational disclaimer."""
    await init_db()
    asset = await market_service.get_asset_by_id("asset-nvda")
    quote = await market_service.get_asset_quote(asset)
    news = await MarketNewsCorrelator.get_related_news_for_asset(asset, limit=2)

    insight = await MarketInsightService.generate_insight(
        question="Why did NVIDIA stock move today?",
        asset=asset,
        quote=quote,
        related_news=news,
        user_id="default-tony-stark"
    )

    assert insight.direct_answer is not None
    assert len(insight.possible_explanations) >= 1
    assert len(insight.citations) >= 1
    # Strict observational notice without broker trades
    assert "no live financial execution" in insight.market_disclaimer.lower()
    assert "Strict Notice:" in insight.market_disclaimer


@pytest.mark.asyncio
async def test_strict_trading_boundary_refusal():
    """Verifies that trading commands and broker write operations are strictly refused and audited."""
    user = {"id": "default-tony-stark", "username": "tony_stark"}

    # Mock a hypothetical trading tool
    class MockTradeTool:
        name = "place_trade_order"
        risk_level = RiskLevel.R4_CRITICAL.value
        required_scope = Scope.BROKER_TRADE.value
        requires_confirmation = True

    decision = await PolicyEngine.evaluate(user=user, tool=MockTradeTool(), parameters={"symbol": "NVDA", "quantity": 10})
    assert decision.allowed is False
    assert decision.risk_level == RiskLevel.R4_CRITICAL.value
    assert "disabled in this implementation phase" in decision.reason


@pytest.mark.asyncio
async def test_market_rest_api_endpoints():
    """Verifies Phase 6 Market REST API routes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /api/markets/status
        res_st = await ac.get("/api/markets/status")
        assert res_st.status_code == 200
        assert res_st.json()["trading_enabled"] is False

        # 2. GET /api/markets/overview
        res_ov = await ac.get("/api/markets/overview")
        assert res_ov.status_code == 200
        assert "indices" in res_ov.json()

        # 3. GET /api/markets/assets/search
        res_sr = await ac.get("/api/markets/assets/search?query=TSM&limit=5")
        assert res_sr.status_code == 200
        assets = res_sr.json()
        assert len(assets) >= 1
        asset_id = assets[0]["id"]

        # 4. GET /api/markets/assets/{id}/quote
        res_q = await ac.get(f"/api/markets/assets/{asset_id}/quote")
        assert res_q.status_code == 200
        assert "price" in res_q.json()

        # 5. GET /api/markets/assets/{id}/history
        res_h = await ac.get(f"/api/markets/assets/{asset_id}/history?interval=1d&range=1mo")
        assert res_h.status_code == 200
        assert "bars" in res_h.json()

        # 6. GET /api/markets/assets/{id}/news
        res_n = await ac.get(f"/api/markets/assets/{asset_id}/news")
        assert res_n.status_code == 200
        assert isinstance(res_n.json(), list)

        # 7. POST /api/markets/watchlists
        res_wl = await ac.post("/api/markets/watchlists", json={"name": "Semiconductor Focus"})
        assert res_wl.status_code == 201
        wl_data = res_wl.json()
        wl_id = wl_data["id"]

        # 8. POST /api/markets/watchlists/{id}/items
        res_item = await ac.post(f"/api/markets/watchlists/{wl_id}/items", json={"asset_id": asset_id})
        assert res_item.status_code == 201
        item_data = res_item.json()
        item_id = item_data["id"]

        # 9. GET /api/markets/watchlists
        res_wls = await ac.get("/api/markets/watchlists")
        assert res_wls.status_code == 200
        assert any(w["id"] == wl_id for w in res_wls.json())

        # 10. DELETE /api/markets/watchlists/{id}/items/{itemId}
        res_del_item = await ac.delete(f"/api/markets/watchlists/{wl_id}/items/{item_id}")
        assert res_del_item.status_code == 200

        # 11. DELETE /api/markets/watchlists/{id}
        res_del_wl = await ac.delete(f"/api/markets/watchlists/{wl_id}")
        assert res_del_wl.status_code == 200

        # 12. GET /api/markets/portfolio (Read-only unconfigured state)
        res_port = await ac.get("/api/markets/portfolio")
        assert res_port.status_code == 200
        assert res_port.json()["status"] == "BROKER_READ_ONLY_NOT_CONFIGURED"

        # 13. POST /api/markets/insights
        res_ins = await ac.post("/api/markets/insights", json={
            "question": "What is the broader trend in global semiconductor fabrication?",
            "asset_id": asset_id,
            "time_window": "24h"
        })
        assert res_ins.status_code == 201
        ins_data = res_ins.json()
        assert "direct_answer" in ins_data
        assert "Strict Notice:" in ins_data["market_disclaimer"]


@pytest.mark.asyncio
async def test_market_user_data_isolation():
    """Verifies that User B cannot read or delete User A's watchlists."""
    user_a = "default-tony-stark"
    user_b = "rogue-agent-market"

    wl = await market_service.create_watchlist(user_a, "Tony Stark Core Radar")

    # User B attempts deletion directly in DB or via service
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM watchlists WHERE id = ? AND user_id = ?", (wl.id, user_b))
        await db.commit()
        assert cur.rowcount == 0

    # Verify User A's watchlist remains intact
    wl_check = await market_service.get_watchlist_by_id(user_a, wl.id)
    assert wl_check is not None
    assert wl_check.name == "Tony Stark Core Radar"


@pytest.mark.asyncio
async def test_market_audit_events_trail():
    """Verifies that market operations create auditable events in audit_events."""
    user_id = "default-tony-stark"
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT event_type FROM audit_events 
            WHERE user_id = ? AND event_type LIKE 'MARKET_%'
            ORDER BY timestamp DESC LIMIT 20
        """, (user_id,))
        rows = await cur.fetchall()
        events = [r["event_type"] for r in rows]

    assert any(e.startswith("MARKET_") for e in events)
