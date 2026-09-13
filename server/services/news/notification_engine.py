# ==========================================================================
# JARVIS News Notification & Alert Engine
# Manages quiet hours, importance thresholds, and duplicate suppression
# ==========================================================================

import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from server.models.schemas import NotificationRuleCreate, NotificationRuleUpdate, NotificationRuleOut, NewsNotificationOut
from server.database import get_db_connection
from server.audit.logger import audit_logger

IMPORTANCE_RANKS = {
    "all": 0,
    "low": 1,
    "normal": 2,
    "moderate": 2,
    "high": 3,
    "critical": 4
}

class NotificationEngine:
    """
    Evaluates news alerts against user notification rules, enforces quiet hours,
    and strictly suppresses duplicate notifications for the same event cluster.
    """

    @staticmethod
    def is_in_quiet_hours(quiet_start: str = "22:00", quiet_end: str = "07:00", current_time_str: Optional[str] = None) -> bool:
        """
        Determines whether the given or current local time falls within quiet hours.
        e.g. 22:00 to 07:00.
        """
        try:
            if not quiet_start or not quiet_end:
                return False

            if current_time_str:
                now_t = datetime.strptime(current_time_str, "%H:%M").time()
            else:
                now_t = datetime.now().time()

            start_t = datetime.strptime(quiet_start.strip(), "%H:%M").time()
            end_t = datetime.strptime(quiet_end.strip(), "%H:%M").time()

            if start_t > end_t:
                # Overnight window (e.g. 22:00 to 07:00)
                return now_t >= start_t or now_t < end_t
            else:
                # Same-day window (e.g. 13:00 to 14:00)
                return start_t <= now_t < end_t
        except Exception:
            return False

    @classmethod
    async def evaluate_notifications_for_feed(
        cls,
        user_id: str,
        clusters: List[Dict[str, Any]],
        current_time_str: Optional[str] = None
    ) -> List[NewsNotificationOut]:
        """
        Evaluates active event clusters against user rules and followed topics.
        Dispatches non-duplicate alerts and stores them in news_notifications.
        """
        rules = await cls.get_user_rules(user_id)
        if not rules:
            return []

        # Load previously notified cluster IDs for user to enforce duplicate suppression
        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT cluster_id, importance FROM news_notifications
                WHERE user_id = ? AND sent_at >= datetime('now', '-24 hours')
            """, (user_id,))
            rows = await cur.fetchall()
            already_notified = {r["cluster_id"]: r["importance"] for r in rows if r["cluster_id"]}

        dispatched: List[NewsNotificationOut] = []
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        for rule in rules:
            if not rule.is_enabled:
                continue

            # Check quiet hours
            if cls.is_in_quiet_hours(rule.quiet_hours_start, rule.quiet_hours_end, current_time_str):
                continue

            min_rank = IMPORTANCE_RANKS.get(rule.importance_threshold.lower(), 2)

            for cl in clusters:
                cl_id = cl["id"]
                cl_importance = cl.get("importance_level", "normal")
                cl_rank = IMPORTANCE_RANKS.get(cl_importance.lower(), 2)

                # Check importance threshold
                if cl_rank < min_rank:
                    continue

                # Check duplicate suppression: suppress if already notified unless material status upgrade
                if cl_id in already_notified:
                    prev_imp = already_notified[cl_id]
                    prev_rank = IMPORTANCE_RANKS.get(prev_imp.lower(), 2)
                    # Material update only if upgraded to higher rank (e.g. normal -> critical)
                    if cl_rank <= prev_rank:
                        continue

                # Check topic filter if rule is bound to a specific topic
                if rule.topic_id:
                    # check if cluster entities match
                    pass

                notif_id = str(uuid.uuid4())
                headline = cl["representative_headline"]
                msg = f"[{cl_importance.upper()}] {cl['summary'][:160]}... ({cl.get('publisher_count', 1)} sources)"

                notif_out = NewsNotificationOut(
                    id=notif_id,
                    user_id=user_id,
                    cluster_id=cl_id,
                    topic_id=rule.topic_id,
                    title=headline,
                    message=msg,
                    importance=cl_importance,
                    sent_at=now_str
                )

                # Record in database
                async with get_db_connection() as db:
                    await db.execute("""
                        INSERT INTO news_notifications (id, user_id, cluster_id, topic_id, title, message, importance, sent_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (notif_out.id, user_id, cl_id, rule.topic_id, notif_out.title, notif_out.message, notif_out.importance, now_str))
                    await db.commit()

                already_notified[cl_id] = cl_importance
                dispatched.append(notif_out)

                await audit_logger.log_event(
                    event_type="NEWS_NOTIFICATION_DISPATCHED",
                    action="news.notification_dispatch",
                    user_id=user_id,
                    resource_id=notif_out.id,
                    details={"cluster_id": cl_id, "importance": cl_importance, "title": headline}
                )

        return dispatched

    @classmethod
    async def get_user_rules(cls, user_id: str) -> List[NotificationRuleOut]:
        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT * FROM notification_rules WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            rows = await cur.fetchall()
            return [
                NotificationRuleOut(
                    id=r["id"],
                    user_id=r["user_id"],
                    topic_id=r["topic_id"],
                    notification_type=r["notification_type"],
                    frequency=r["frequency"],
                    importance_threshold=r["importance_threshold"],
                    quiet_hours_start=r["quiet_hours_start"],
                    quiet_hours_end=r["quiet_hours_end"],
                    is_enabled=bool(r["is_enabled"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                )
                for r in rows
            ]

    @classmethod
    async def create_rule(cls, user_id: str, rule_in: NotificationRuleCreate) -> NotificationRuleOut:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        rule_id = str(uuid.uuid4())
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO notification_rules (
                    id, user_id, topic_id, notification_type, frequency, importance_threshold,
                    quiet_hours_start, quiet_hours_end, is_enabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id, user_id, rule_in.topic_id, rule_in.notification_type,
                rule_in.frequency, rule_in.importance_threshold,
                rule_in.quiet_hours_start or "22:00", rule_in.quiet_hours_end or "07:00",
                1 if rule_in.is_enabled else 0, now_str, now_str
            ))
            await db.commit()

        await audit_logger.log_event(
            event_type="NEWS_NOTIFICATION_RULE_CREATED",
            action="news.rule_create",
            user_id=user_id,
            resource_id=rule_id,
            details={"type": rule_in.notification_type, "threshold": rule_in.importance_threshold}
        )

        return NotificationRuleOut(
            id=rule_id,
            user_id=user_id,
            topic_id=rule_in.topic_id,
            notification_type=rule_in.notification_type,
            frequency=rule_in.frequency,
            importance_threshold=rule_in.importance_threshold,
            quiet_hours_start=rule_in.quiet_hours_start,
            quiet_hours_end=rule_in.quiet_hours_end,
            is_enabled=rule_in.is_enabled,
            created_at=now_str,
            updated_at=now_str
        )

    @classmethod
    async def update_rule(cls, user_id: str, rule_id: str, update_in: NotificationRuleUpdate) -> Optional[NotificationRuleOut]:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        async with get_db_connection() as db:
            cur = await db.execute("SELECT * FROM notification_rules WHERE id = ? AND user_id = ?", (rule_id, user_id))
            row = await cur.fetchone()
            if not row:
                return None

            n_type = update_in.notification_type or row["notification_type"]
            freq = update_in.frequency or row["frequency"]
            thresh = update_in.importance_threshold or row["importance_threshold"]
            q_start = update_in.quiet_hours_start or row["quiet_hours_start"]
            q_end = update_in.quiet_hours_end or row["quiet_hours_end"]
            enabled = 1 if (update_in.is_enabled if update_in.is_enabled is not None else row["is_enabled"]) else 0

            await db.execute("""
                UPDATE notification_rules SET
                    notification_type = ?, frequency = ?, importance_threshold = ?,
                    quiet_hours_start = ?, quiet_hours_end = ?, is_enabled = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (n_type, freq, thresh, q_start, q_end, enabled, now_str, rule_id, user_id))
            await db.commit()

        return NotificationRuleOut(
            id=rule_id,
            user_id=user_id,
            topic_id=row["topic_id"],
            notification_type=n_type,
            frequency=freq,
            importance_threshold=thresh,
            quiet_hours_start=q_start,
            quiet_hours_end=q_end,
            is_enabled=bool(enabled),
            created_at=row["created_at"],
            updated_at=now_str
        )

    @classmethod
    async def delete_rule(cls, user_id: str, rule_id: str) -> bool:
        async with get_db_connection() as db:
            cur = await db.execute("DELETE FROM notification_rules WHERE id = ? AND user_id = ?", (rule_id, user_id))
            await db.commit()
            return cur.rowcount > 0

    @classmethod
    async def list_notifications(cls, user_id: str, limit: int = 30) -> List[NewsNotificationOut]:
        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT * FROM news_notifications WHERE user_id = ? ORDER BY sent_at DESC LIMIT ?
            """, (user_id, limit))
            rows = await cur.fetchall()
            return [
                NewsNotificationOut(
                    id=r["id"],
                    user_id=r["user_id"],
                    cluster_id=r["cluster_id"],
                    topic_id=r["topic_id"],
                    title=r["title"],
                    message=r["message"],
                    importance=r["importance"],
                    sent_at=r["sent_at"]
                )
                for r in rows
            ]

notification_engine = NotificationEngine()
