# ==========================================================================
# JARVIS Global News Intelligence & Topic Tracking API Routes
# ==========================================================================

import time
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import (
    NewsItemOut, NewsTopicCreate, NewsTopicUpdate, NewsTopicOut,
    NewsClusterOut, NewsBriefingCreate, NewsBriefingOut,
    NotificationRuleCreate, NotificationRuleUpdate, NotificationRuleOut,
    NewsNotificationOut
)
from server.services.news import default_news_provider, briefing_generator
from server.services.news.deduplication import clusterer
from server.services.news.notification_engine import notification_engine
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/news", tags=["News & Global Intelligence"])

# ----------------- 1. News Feed & Articles -----------------
@router.get("", response_model=List[NewsItemOut])
async def get_news_feed(
    category: Optional[str] = Query("all"),
    topic_id: Optional[str] = Query(None),
    limit: int = Query(25, le=50),
    user: dict = Depends(get_optional_user)
):
    user_id = user["id"]

    # If topic_id is provided, load topic query
    query_filter = None
    ticker_filter = None
    if topic_id:
        async with get_db_connection() as db:
            cur = await db.execute("SELECT query, ticker FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
            t_row = await cur.fetchone()
            if t_row:
                query_filter = t_row["query"]
                ticker_filter = t_row["ticker"]

    items = await default_news_provider.fetch_news(
        category=category,
        limit=limit,
        query=query_filter,
        ticker=ticker_filter
    )

    # Load user topics for importance and relevance scoring
    user_topics = []
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM news_topics WHERE user_id = ? AND is_active = 1", (user_id,))
        user_topics = [dict(r) for r in await cur.fetchall()]

    clusters, clustered_items = clusterer.cluster_items(items, user_topics=user_topics)

    # In background, evaluate notification triggers for active topics
    try:
        await notification_engine.evaluate_notifications_for_feed(user_id, clusters)
    except Exception as e:
        print(f"[JARVIS News] Notification check: {e}")

    return clustered_items

@router.get("/article/{news_id}", response_model=NewsItemOut)
async def get_news_article(news_id: str, user: dict = Depends(get_optional_user)):
    # Look for item in feed or fallback
    items = await default_news_provider.fetch_news(limit=50)
    for it in items:
        if it.id == news_id:
            return it

    # Check database
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM news_items WHERE id = ?", (news_id,))
        row = await cur.fetchone()
        if row:
            return NewsItemOut(
                id=row["id"],
                headline=row["headline"],
                summary=row["summary"] or "",
                url=row["url"],
                canonical_url=row["canonical_url"],
                publisher=row["publisher"],
                author=row["author"],
                published_at=row["published_at"],
                retrieval_timestamp=row["retrieval_timestamp"],
                category=row["category"],
                region=row["region"] or "Global",
                related_entities=json.loads(row["related_entities_json"] or "[]"),
                ticker=row["ticker"],
                importance_label=row["importance_label"],
                relevance_score=row["relevance_score"],
                extraction_status=row["extraction_status"],
                source_quality=row["source_quality"],
                cluster_id=row["cluster_id"],
                is_read=bool(row["is_read"]),
                is_saved=bool(row["is_saved"])
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News article not found.")

@router.post("/refresh", response_model=List[NewsItemOut])
async def refresh_news_feed(user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    # Clear cache by fetching fresh
    items = await default_news_provider.fetch_news(limit=30)
    _, clustered_items = clusterer.cluster_items(items)

    await audit_logger.log_event(
        event_type="NEWS_FEED_REFRESHED",
        action="news.feed_refresh",
        user_id=user_id,
        details={"items_count": len(clustered_items)}
    )
    return clustered_items

@router.post("/{news_id}/read")
async def mark_news_read(news_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        await db.execute("UPDATE news_items SET is_read = 1 WHERE id = ?", (news_id,))
        await db.commit()
    return {"success": True, "news_id": news_id, "is_read": True}

@router.post("/{news_id}/unread")
async def mark_news_unread(news_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        await db.execute("UPDATE news_items SET is_read = 0 WHERE id = ?", (news_id,))
        await db.commit()
    return {"success": True, "news_id": news_id, "is_read": False}

@router.post("/{news_id}/save")
async def save_news_item(news_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        await db.execute("UPDATE news_items SET is_saved = 1 WHERE id = ?", (news_id,))
        await db.commit()
    return {"success": True, "news_id": news_id, "is_saved": True}

@router.delete("/{news_id}/save")
async def unsave_news_item(news_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        await db.execute("UPDATE news_items SET is_saved = 0 WHERE id = ?", (news_id,))
        await db.commit()
    return {"success": True, "news_id": news_id, "is_saved": False}


# ----------------- 2. Topic Subscriptions -----------------
@router.get("/topics", response_model=List[NewsTopicOut])
async def list_topics(user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT * FROM news_topics
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user["id"],))
        rows = await cur.fetchall()
        return [
            NewsTopicOut(
                id=r["id"],
                user_id=r["user_id"],
                topic_name=r["topic_name"],
                query=r["query"],
                topic_type=r["topic_type"] if "topic_type" in r.keys() else "keyword",
                entity_id=r["entity_id"] if "entity_id" in r.keys() else None,
                ticker=r["ticker"] if "ticker" in r.keys() else None,
                category=r["category"] or "General",
                region=r["region"] or "Global",
                notifications_enabled=bool(r["notifications_enabled"]),
                notification_frequency=r["notification_frequency"] if "notification_frequency" in r.keys() else "immediate",
                importance_threshold=r["importance_threshold"] if "importance_threshold" in r.keys() else "all",
                refresh_preference=r["refresh_preference"] if "refresh_preference" in r.keys() else "auto",
                is_active=bool(r["is_active"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"] if "updated_at" in r.keys() else None
            )
            for r in rows
        ]

@router.post("/topics", response_model=NewsTopicOut, status_code=status.HTTP_201_CREATED)
async def subscribe_topic(topic_in: NewsTopicCreate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    topic_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Validate ticker if provided
    ticker_val = topic_in.ticker.strip().upper().replace("$", "") if topic_in.ticker else None

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO news_topics (
                id, user_id, topic_name, query, topic_type, entity_id, ticker,
                category, region, notifications_enabled, notification_frequency,
                importance_threshold, refresh_preference, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            topic_id, user_id, topic_in.topic_name.strip(), topic_in.query.strip(),
            topic_in.topic_type or "keyword", topic_in.entity_id, ticker_val,
            topic_in.category or "General", topic_in.region or "Global",
            1 if topic_in.notifications_enabled else 0,
            topic_in.notification_frequency or "immediate",
            topic_in.importance_threshold or "all",
            topic_in.refresh_preference or "auto",
            now_str, now_str
        ))
        await db.commit()

    await audit_logger.log_event(
        event_type="NEWS_TOPIC_SUBSCRIBED",
        action="news.topic_create",
        user_id=user_id,
        resource_id=topic_id,
        details={
            "topic_name": topic_in.topic_name,
            "query": topic_in.query,
            "type": topic_in.topic_type,
            "ticker": ticker_val
        }
    )

    return NewsTopicOut(
        id=topic_id,
        user_id=user_id,
        topic_name=topic_in.topic_name.strip(),
        query=topic_in.query.strip(),
        topic_type=topic_in.topic_type or "keyword",
        entity_id=topic_in.entity_id,
        ticker=ticker_val,
        category=topic_in.category or "General",
        region=topic_in.region or "Global",
        notifications_enabled=bool(topic_in.notifications_enabled),
        notification_frequency=topic_in.notification_frequency or "immediate",
        importance_threshold=topic_in.importance_threshold or "all",
        refresh_preference=topic_in.refresh_preference or "auto",
        is_active=True,
        created_at=now_str,
        updated_at=now_str
    )

@router.get("/topics/{topic_id}", response_model=NewsTopicOut)
async def get_topic(topic_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user["id"]))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News topic not found.")
        return NewsTopicOut(
            id=r["id"],
            user_id=r["user_id"],
            topic_name=r["topic_name"],
            query=r["query"],
            topic_type=r["topic_type"],
            entity_id=r["entity_id"],
            ticker=r["ticker"],
            category=r["category"] or "General",
            region=r["region"] or "Global",
            notifications_enabled=bool(r["notifications_enabled"]),
            notification_frequency=r["notification_frequency"],
            importance_threshold=r["importance_threshold"],
            refresh_preference=r["refresh_preference"],
            is_active=bool(r["is_active"]),
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        )

@router.patch("/topics/{topic_id}", response_model=NewsTopicOut)
async def update_topic(topic_id: str, update_in: NewsTopicUpdate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News topic not found.")

        t_name = update_in.topic_name or r["topic_name"]
        q_val = update_in.query or r["query"]
        notif_en = 1 if (update_in.notifications_enabled if update_in.notifications_enabled is not None else r["notifications_enabled"]) else 0
        freq = update_in.notification_frequency or r["notification_frequency"]
        thresh = update_in.importance_threshold or r["importance_threshold"]
        ref_pref = update_in.refresh_preference or r["refresh_preference"]
        active = 1 if (update_in.is_active if update_in.is_active is not None else r["is_active"]) else 0

        await db.execute("""
            UPDATE news_topics SET
                topic_name = ?, query = ?, notifications_enabled = ?,
                notification_frequency = ?, importance_threshold = ?,
                refresh_preference = ?, is_active = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (t_name, q_val, notif_en, freq, thresh, ref_pref, active, now_str, topic_id, user_id))
        await db.commit()

    await audit_logger.log_event(
        event_type="NEWS_TOPIC_UPDATED",
        action="news.topic_update",
        user_id=user_id,
        resource_id=topic_id,
        details={"topic_name": t_name, "is_active": bool(active)}
    )

    return NewsTopicOut(
        id=topic_id,
        user_id=user_id,
        topic_name=t_name,
        query=q_val,
        topic_type=r["topic_type"],
        entity_id=r["entity_id"],
        ticker=r["ticker"],
        category=r["category"],
        region=r["region"],
        notifications_enabled=bool(notif_en),
        notification_frequency=freq,
        importance_threshold=thresh,
        refresh_preference=ref_pref,
        is_active=bool(active),
        created_at=r["created_at"],
        updated_at=now_str
    )

@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News topic subscription not found.")

    await audit_logger.log_event(
        event_type="NEWS_TOPIC_REMOVED",
        action="news.topic_delete",
        user_id=user_id,
        resource_id=topic_id
    )
    return {"success": True, "topic_id": topic_id, "message": "Unfollowed topic subscription."}

@router.post("/topics/{topic_id}/refresh", response_model=List[NewsItemOut])
async def refresh_topic_news(topic_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("SELECT query, ticker, category FROM news_topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News topic not found.")

    items = await default_news_provider.fetch_news(
        category=r["category"] or "all",
        query=r["query"],
        ticker=r["ticker"],
        limit=20
    )
    _, clustered = clusterer.cluster_items(items)
    return clustered


# ----------------- 3. Event Clusters -----------------
@router.get("/clusters", response_model=List[NewsClusterOut])
async def list_event_clusters(
    category: Optional[str] = Query("all"),
    user: dict = Depends(get_optional_user)
):
    items = await default_news_provider.fetch_news(category=category or "all", limit=30)
    clusters, _ = clusterer.cluster_items(items)

    return [
        NewsClusterOut(
            id=cl["id"],
            representative_headline=cl["representative_headline"],
            summary=cl["summary"],
            first_observed_at=cl["first_observed_at"],
            last_observed_at=cl["last_observed_at"],
            category=cl["category"],
            importance_level=cl.get("importance_level", "normal"),
            publisher_count=cl.get("publisher_count", 1),
            source_count=cl.get("source_count", 1),
            conflicting_coverage=cl.get("conflicting_coverage", False),
            member_item_ids=cl.get("item_ids", []),
            related_entities=cl.get("related_entities", []),
            sources=list(dict.fromkeys(cl.get("sources", []))),
            last_summarized_at=cl.get("last_summarized_at")
        )
        for cl in clusters
    ]

@router.get("/clusters/{cluster_id}", response_model=NewsClusterOut)
async def get_cluster_details(cluster_id: str, user: dict = Depends(get_optional_user)):
    items = await default_news_provider.fetch_news(limit=50)
    clusters, _ = clusterer.cluster_items(items)
    for cl in clusters:
        if cl["id"] == cluster_id:
            return NewsClusterOut(
                id=cl["id"],
                representative_headline=cl["representative_headline"],
                summary=cl["summary"],
                first_observed_at=cl["first_observed_at"],
                last_observed_at=cl["last_observed_at"],
                category=cl["category"],
                importance_level=cl.get("importance_level", "normal"),
                publisher_count=cl.get("publisher_count", 1),
                source_count=cl.get("source_count", 1),
                conflicting_coverage=cl.get("conflicting_coverage", False),
                member_item_ids=cl.get("item_ids", []),
                related_entities=cl.get("related_entities", []),
                sources=list(dict.fromkeys(cl.get("sources", []))),
                last_summarized_at=cl.get("last_summarized_at")
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event cluster not found.")

@router.post("/clusters/{cluster_id}/summarize")
async def summarize_cluster(cluster_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    items = await default_news_provider.fetch_news(limit=50)
    clusters, _ = clusterer.cluster_items(items)
    target_cluster = next((c for c in clusters if c["id"] == cluster_id), None)
    if not target_cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event cluster not found.")

    member_items = [it for it in items if it.id in target_cluster.get("item_ids", [])]
    summary = await briefing_generator.summarize_cluster(target_cluster, member_items, user_id)

    await audit_logger.log_event(
        event_type="NEWS_CLUSTER_SUMMARIZED",
        action="news.cluster_summarize",
        user_id=user_id,
        resource_id=cluster_id,
        details={"sources_count": len(member_items)}
    )
    return summary


# ----------------- 4. News Briefings -----------------
@router.post("/briefings", response_model=NewsBriefingOut, status_code=status.HTTP_201_CREATED)
async def generate_briefing(
    req: Optional[NewsBriefingCreate] = None,
    category: Optional[str] = Query(None),
    user: dict = Depends(get_optional_user)
):
    user_id = user["id"]
    cat = (req.category if req and req.category else category) or "all"
    b_type = req.type if req and req.type else "on_demand"
    t_window = req.time_window if req and req.time_window else "24h"
    save_res = req.save_result if req and req.save_result is not None else False

    # Topic query if bound
    topic_query = None
    if req and req.topic_id:
        async with get_db_connection() as db:
            cur = await db.execute("SELECT query FROM news_topics WHERE id = ? AND user_id = ?", (req.topic_id, user_id))
            r = await cur.fetchone()
            if r:
                topic_query = r["query"]

    items = await default_news_provider.fetch_news(category=cat, query=topic_query, limit=25)
    topic_title = f"{cat.title()} Intelligence Summary" if not topic_query else f"Topic Intelligence: {topic_query}"

    briefing = await briefing_generator.generate_briefing(
        news_items=items,
        topic=topic_title,
        user_id=user_id,
        briefing_type=b_type,
        time_window=t_window,
        save_result=save_res
    )
    return briefing

@router.get("/briefings", response_model=List[NewsBriefingOut])
async def list_briefings(limit: int = Query(20, le=50), user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT * FROM news_briefings WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = await cur.fetchall()
        return [
            NewsBriefingOut(
                id=r["id"],
                briefing_id=r["id"],
                user_id=r["user_id"],
                type=r["type"],
                time_window=r["time_window"],
                title=r["title"],
                summary=r["summary"],
                key_events=json.loads(r["key_events_json"] or "[]"),
                citations=json.loads(r["citations_json"] or "[]"),
                market_implications=r["market_implications"],
                uncertainty_notes=r["uncertainty_notes"],
                provider_name=r["provider_name"],
                model_name=r["model_name"],
                saved=bool(r["saved"]),
                timestamp=r["created_at"],
                created_at=r["created_at"]
            )
            for r in rows
        ]

@router.get("/briefings/{briefing_id}", response_model=NewsBriefingOut)
async def get_briefing_by_id(briefing_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM news_briefings WHERE id = ? AND user_id = ?", (briefing_id, user_id))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News briefing not found.")
        return NewsBriefingOut(
            id=r["id"],
            briefing_id=r["id"],
            user_id=r["user_id"],
            type=r["type"],
            time_window=r["time_window"],
            title=r["title"],
            summary=r["summary"],
            key_events=json.loads(r["key_events_json"] or "[]"),
            citations=json.loads(r["citations_json"] or "[]"),
            market_implications=r["market_implications"],
            uncertainty_notes=r["uncertainty_notes"],
            provider_name=r["provider_name"],
            model_name=r["model_name"],
            saved=bool(r["saved"]),
            timestamp=r["created_at"],
            created_at=r["created_at"]
        )

@router.post("/briefings/{briefing_id}/save")
async def save_briefing(briefing_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("UPDATE news_briefings SET saved = 1 WHERE id = ? AND user_id = ?", (briefing_id, user_id))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News briefing not found.")
    return {"success": True, "briefing_id": briefing_id, "saved": True}

@router.delete("/briefings/{briefing_id}/save")
async def unsave_briefing(briefing_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    async with get_db_connection() as db:
        cur = await db.execute("UPDATE news_briefings SET saved = 0 WHERE id = ? AND user_id = ?", (briefing_id, user_id))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News briefing not found.")
    return {"success": True, "briefing_id": briefing_id, "saved": False}


# ----------------- 5. Notification Rules -----------------
@router.get("/notification-rules", response_model=List[NotificationRuleOut])
async def list_notification_rules(user: dict = Depends(get_optional_user)):
    return await notification_engine.get_user_rules(user["id"])

@router.post("/notification-rules", response_model=NotificationRuleOut, status_code=status.HTTP_201_CREATED)
async def create_notification_rule(rule_in: NotificationRuleCreate, user: dict = Depends(get_optional_user)):
    return await notification_engine.create_rule(user["id"], rule_in)

@router.patch("/notification-rules/{rule_id}", response_model=NotificationRuleOut)
async def update_notification_rule(rule_id: str, update_in: NotificationRuleUpdate, user: dict = Depends(get_optional_user)):
    res = await notification_engine.update_rule(user["id"], rule_id, update_in)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification rule not found.")
    return res

@router.delete("/notification-rules/{rule_id}")
async def delete_notification_rule(rule_id: str, user: dict = Depends(get_optional_user)):
    success = await notification_engine.delete_rule(user["id"], rule_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification rule not found.")
    return {"success": True, "rule_id": rule_id, "deleted": True}

@router.get("/notifications", response_model=List[NewsNotificationOut])
async def list_dispatched_notifications(limit: int = Query(30, le=100), user: dict = Depends(get_optional_user)):
    return await notification_engine.list_notifications(user["id"], limit=limit)

@router.get("/{news_id}", response_model=NewsItemOut)
async def get_news_article_by_id(news_id: str, user: dict = Depends(get_optional_user)):
    return await get_news_article(news_id=news_id, user=user)

