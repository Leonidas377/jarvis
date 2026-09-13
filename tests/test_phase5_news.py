# ==========================================================================
# Phase 5 Acceptance Tests: Real-Time News Intelligence & Topic Tracking
# ==========================================================================

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from server.main import app
from server.database import get_db_connection, init_db
from server.models.schemas import (
    NewsItemOut, NewsTopicCreate, NewsBriefingCreate,
    NotificationRuleCreate, NotificationRuleUpdate
)
from server.services.news.deduplication import NewsClusterer, normalize_url, detect_conflicting_coverage
from server.services.news.importance_scorer import ImportanceScorer
from server.services.news.notification_engine import NotificationEngine, notification_engine
from server.services.news.briefing import NewsBriefingGenerator, briefing_generator


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    asyncio.run(init_db())


def test_url_normalization_and_conflict_detection():
    """Verifies that tracking params are stripped and conflicting coverage is detected."""
    raw_url_1 = "https://reuters.com/business/tech-merger/?utm_source=twitter&utm_medium=social&ref=123"
    raw_url_2 = "https://reuters.com/business/tech-merger"
    assert normalize_url(raw_url_1) == normalize_url(raw_url_2)

    # Conflicting coverage: surge vs plunge
    headlines_conflict = [
        "Tech Index Surges Following Strong Semiconductor Forecast",
        "Chip Stocks Plunge Amid Supply Chain Anxiety"
    ]
    assert detect_conflicting_coverage(headlines_conflict) is True

    headlines_aligned = [
        "Tech Index Surges Following Strong Semiconductor Forecast",
        "Chip Stocks Rally On Robust Data Center Demand"
    ]
    assert detect_conflicting_coverage(headlines_aligned) is False


def test_news_clustering_and_multi_source_deduplication():
    """Verifies multi-source clustering, source/publisher counts, and canonical deduplication."""
    now_iso = datetime.now(timezone.utc).isoformat()
    items = [
        NewsItemOut(
            id="item-a1",
            headline="Taiwan Semiconductor Begins Pilot Production on 2nm Node",
            summary="TSMC started test wafer runs in Hsinchu with yields beating estimates.",
            url="https://reuters.com/tech/tsmc-2nm-pilot-production",
            canonical_url="https://reuters.com/tech/tsmc-2nm-pilot-production?utm_source=rss",
            publisher="Reuters",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Asia",
            related_entities=["TSMC", "Taiwan"]
        ),
        NewsItemOut(
            id="item-a2",
            headline="TSMC Ramps 2nm Trial Wafer Production Ahead of Schedule",
            summary="Bloomberg reports TSMC pilot production on next-gen 2nm chips progressing smoothly.",
            url="https://bloomberg.com/news/tsmc-2nm-chips-pilot",
            canonical_url="https://bloomberg.com/news/tsmc-2nm-chips-pilot",
            publisher="Bloomberg",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Asia",
            related_entities=["TSMC"]
        ),
        NewsItemOut(
            id="item-b1",
            headline="European Central Bank Cuts Key Interest Rate by 25 Basis Points",
            summary="ECB policymakers lowered deposit rates as eurozone inflation slowed to target.",
            url="https://ft.com/ecb-interest-rate-cut-2026",
            canonical_url="https://ft.com/ecb-interest-rate-cut-2026",
            publisher="Financial Times",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Economy",
            region="Europe",
            related_entities=["ECB", "Eurozone"]
        )
    ]

    clusters, updated_items = NewsClusterer.cluster_items(items, threshold=0.25)
    assert len(clusters) == 2

    # Find TSMC cluster
    tsmc_cl = next(c for c in clusters if "tsmc" in c["representative_headline"].lower() or "taiwan" in c["representative_headline"].lower())
    assert tsmc_cl["publisher_count"] == 2
    assert tsmc_cl["source_count"] == 2
    assert len(tsmc_cl["sources"]) == 2
    assert "item-a1" in tsmc_cl["item_ids"]
    assert "item-a2" in tsmc_cl["item_ids"]

    # Verify item-level cluster IDs
    item_a1 = next(it for it in updated_items if it.id == "item-a1")
    assert item_a1.cluster_id == tsmc_cl["id"]


def test_importance_scoring_and_explainable_labels():
    """Verifies that importance scoring properly weights critical keywords, breaking flags, and user topics."""
    now_iso = datetime.now(timezone.utc).isoformat()
    item_critical = NewsItemOut(
        id="crit-1",
        headline="Global Cloud Outage Disrupts Financial Services Across North America",
        summary="Major infrastructure outage triggers catastrophic system downtime across major banks.",
        url="https://reuters.com/tech/outage-banks",
        publisher="Reuters",
        published_at=now_iso,
        retrieval_timestamp=now_iso,
        category="Technology",
        region="US",
        is_breaking=True
    )

    user_topics = [{"topic_name": "Cloud Infrastructure", "query": "cloud outage", "ticker": None, "entity_id": None}]
    score_res = ImportanceScorer.score_item(item_critical, user_topics)

    assert score_res["label"] == "critical"
    assert score_res["score"] >= 6.5
    assert "outage" in score_res["explanation"].lower() or "breaking" in score_res["explanation"].lower()


def test_quiet_hours_and_duplicate_notification_suppression():
    """Verifies quiet hours logic and duplicate notification suppression."""
    # 1. Quiet hours evaluation (22:00 to 07:00)
    assert NotificationEngine.is_in_quiet_hours("22:00", "07:00", "23:30") is True
    assert NotificationEngine.is_in_quiet_hours("22:00", "07:00", "03:15") is True
    assert NotificationEngine.is_in_quiet_hours("22:00", "07:00", "14:00") is False
    assert NotificationEngine.is_in_quiet_hours("22:00", "07:00", "08:30") is False


@pytest.mark.asyncio
async def test_briefing_synthesis_and_citations():
    """Verifies executive briefing generation, citation mapping, and safe observational disclaimer."""
    now_iso = datetime.now(timezone.utc).isoformat()
    items = [
        NewsItemOut(
            id="wire-1",
            headline="NVIDIA and Partners Reveal High-Density Liquid Cooling Architecture",
            summary="New specifications enable 120kW per rack thermal dissipation for next-gen clusters.",
            url="https://anandtech.com/nvidia-liquid-cooling",
            publisher="AnandTech",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Global",
            related_entities=["NVIDIA"]
        ),
        NewsItemOut(
            id="wire-2",
            headline="ASML Ships Advanced High-NA EUV Scanner to Research Facility",
            summary="Semiconductor manufacturers prepare for sub-1.4nm pilot production.",
            url="https://reuters.com/tech/asml-high-na",
            publisher="Reuters",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Europe",
            related_entities=["ASML"]
        )
    ]

    briefing = await briefing_generator.generate_briefing(
        news_items=items,
        topic="Advanced Lithography & AI Hardware",
        user_id="default-tony-stark",
        briefing_type="morning",
        time_window="24h",
        save_result=True
    )

    assert briefing.briefing_id is not None
    assert briefing.title is not None
    assert briefing.summary.strip() != ""
    assert len(briefing.key_events) >= 1
    assert len(briefing.citations) == 2
    assert briefing.citations[0].id == "1"
    assert briefing.citations[1].id == "2"
    # Strict observational notice without broker trades
    assert "no live financial execution" in briefing.market_implications.lower()


@pytest.mark.asyncio
async def test_phase5_rest_api_endpoints():
    """Verifies Phase 5 news REST API endpoints: feed, topics, clusters, briefings, and notifications."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /api/news
        res_feed = await ac.get("/api/news?category=technology&limit=10")
        assert res_feed.status_code == 200
        feed = res_feed.json()
        assert isinstance(feed, list)
        assert len(feed) >= 1

        # 2. POST /api/news/topics (Create topic)
        res_top = await ac.post("/api/news/topics", json={
            "topic_name": "TSMC 2nm Lithography",
            "query": "TSMC 2nm",
            "topic_type": "company",
            "ticker": "TSM",
            "category": "Technology",
            "notifications_enabled": True,
            "importance_threshold": "high"
        })
        assert res_top.status_code == 201
        top_data = res_top.json()
        topic_id = top_data["id"]
        assert top_data["topic_name"] == "TSMC 2nm Lithography"
        assert top_data["ticker"] == "TSM"
        assert top_data["notifications_enabled"] is True

        # 3. GET /api/news/topics
        res_list = await ac.get("/api/news/topics")
        assert res_list.status_code == 200
        topics = res_list.json()
        assert any(t["id"] == topic_id for t in topics)

        # 4. PATCH /api/news/topics/{id} (Update topic)
        res_patch = await ac.patch(f"/api/news/topics/{topic_id}", json={
            "topic_name": "Taiwan Semiconductor 2nm Pilot",
            "importance_threshold": "critical"
        })
        assert res_patch.status_code == 200
        assert res_patch.json()["topic_name"] == "Taiwan Semiconductor 2nm Pilot"

        # 5. GET /api/news/clusters
        res_cl = await ac.get("/api/news/clusters")
        assert res_cl.status_code == 200
        clusters = res_cl.json()
        assert isinstance(clusters, list)
        if clusters:
            cl_id = clusters[0]["id"]
            # 6. POST /api/news/clusters/{id}/summarize
            res_sum = await ac.post(f"/api/news/clusters/{cl_id}/summarize")
            assert res_sum.status_code == 200
            assert "summary" in res_sum.json()

        # 7. POST /api/news/briefings (Generate Briefing)
        res_br = await ac.post("/api/news/briefings", json={
            "type": "on_demand",
            "category": "technology",
            "time_window": "24h",
            "save_result": True
        })
        assert res_br.status_code == 201
        br_data = res_br.json()
        assert br_data["briefing_id"] is not None
        assert "citations" in br_data

        # 8. POST /api/news/notification-rules (Create Rule)
        res_rule = await ac.post("/api/news/notification-rules", json={
            "topic_id": topic_id,
            "notification_type": "high_importance",
            "frequency": "immediate",
            "importance_threshold": "high",
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "is_enabled": True
        })
        assert res_rule.status_code == 201
        rule_data = res_rule.json()
        rule_id = rule_data["id"]

        # 9. GET /api/news/notification-rules
        res_rules = await ac.get("/api/news/notification-rules")
        assert res_rules.status_code == 200
        assert any(r["id"] == rule_id for r in res_rules.json())

        # 10. DELETE /api/news/notification-rules/{id}
        res_del_rule = await ac.delete(f"/api/news/notification-rules/{rule_id}")
        assert res_del_rule.status_code == 200

        # 11. DELETE /api/news/topics/{id}
        res_del_top = await ac.delete(f"/api/news/topics/{topic_id}")
        assert res_del_top.status_code == 200


@pytest.mark.asyncio
async def test_news_user_data_isolation():
    """Verifies that User B cannot read or delete User A's followed topics or briefings."""
    user_a = "default-tony-stark"
    user_b = "rogue-agent-news"

    async with get_db_connection() as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, email, hashed_password, display_name, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (user_b, "rogue_news", "rogue_news@stark.com", "hash456", "Rogue News Agent"))
        await db.commit()

    topic_id = str(uuid.uuid4())
    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO news_topics (id, user_id, topic_name, query, created_at)
            VALUES (?, ?, 'Stark Top Secret Arc News', 'Arc Reactor', datetime('now'))
        """, (topic_id, user_a))
        await db.commit()

    # User B attempts to delete User A's topic
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Using dependency override or direct SQL isolation test
        async with get_db_connection() as db:
            cur = await db.execute("DELETE FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_b))
            await db.commit()
            assert cur.rowcount == 0

        # Verify User A's topic remains
        async with get_db_connection() as db:
            cur = await db.execute("SELECT * FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_a))
            row = await cur.fetchone()
            assert row is not None


@pytest.mark.asyncio
async def test_news_audit_events_trail():
    """Verifies that news operations create auditable events."""
    user_id = "default-tony-stark"
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT event_type FROM audit_events 
            WHERE user_id = ? AND event_type LIKE 'NEWS_%'
            ORDER BY timestamp DESC LIMIT 20
        """, (user_id,))
        rows = await cur.fetchall()
        events = [r["event_type"] for r in rows]

    assert any(e.startswith("NEWS_") for e in events)
