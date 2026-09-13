# ==========================================================================
# JARVIS Informational Market Price Alert Evaluator
# Evaluates threshold conditions without ANY live trade or order capability
# ==========================================================================

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from server.database import get_db_connection
from server.models.schemas import MarketQuoteOut
from server.audit.logger import audit_logger

class MarketAlertEvaluator:
    """Evaluates user-configured informational price & percentage alerts."""

    @classmethod
    async def evaluate_alerts_for_quote(cls, quote: MarketQuoteOut) -> List[Dict[str, Any]]:
        triggered_alerts = []
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        async with get_db_connection() as db:
            cur = await db.execute("""
                SELECT * FROM market_alerts 
                WHERE asset_id = ? AND is_enabled = 1
            """, (quote.asset_id,))
            alerts = await cur.fetchall()

            for a in alerts:
                c_type = a["condition_type"]
                threshold = a["threshold"]
                cooldown = a["cooldown_minutes"]
                last_trig = a["last_triggered_at"]

                # Check cooldown
                if last_trig:
                    try:
                        last_dt = datetime.strptime(last_trig, "%Y-%m-%d %H:%M:%S")
                        now_dt = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
                        if (now_dt - last_dt).total_seconds() < (cooldown * 60):
                            continue
                    except Exception:
                        pass

                is_triggered = False
                msg = ""

                if c_type == "price_above" and quote.price >= threshold:
                    is_triggered = True
                    msg = f"{quote.symbol} exceeded target price of ${threshold:.2f} (Current: ${quote.price:.2f})"
                elif c_type == "price_below" and quote.price <= threshold:
                    is_triggered = True
                    msg = f"{quote.symbol} dropped below target price of ${threshold:.2f} (Current: ${quote.price:.2f})"
                elif c_type == "pct_change_above" and abs(quote.change_percent) >= threshold:
                    is_triggered = True
                    msg = f"{quote.symbol} daily shift reached {quote.change_percent:+.2f}% (Threshold: {threshold:.2f}%)"

                if is_triggered:
                    # Update alert last triggered timestamp
                    await db.execute("""
                        UPDATE market_alerts SET last_triggered_at = ? WHERE id = ?
                    """, (now_str, a["id"]))
                    await db.commit()

                    # Audit event
                    await audit_logger.log_event(
                        event_type="MARKET_ALERT_TRIGGERED",
                        action="market.alert_dispatch",
                        user_id=a["user_id"],
                        resource_id=a["id"],
                        details={
                            "symbol": quote.symbol,
                            "condition": c_type,
                            "threshold": threshold,
                            "price": quote.price,
                            "message": msg
                        }
                    )

                    triggered_alerts.append({
                        "alert_id": a["id"],
                        "user_id": a["user_id"],
                        "symbol": quote.symbol,
                        "message": msg,
                        "triggered_at": now_str
                    })

        return triggered_alerts
