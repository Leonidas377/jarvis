# ==========================================================================
# JARVIS News Importance & Relevance Scoring Engine
# Computes explainable priority metrics for news intelligence & notifications
# ==========================================================================

import re
import time
from typing import List, Dict, Any, Optional
from server.models.schemas import NewsItemOut

HIGH_IMPACT_KEYWORDS = {
    "critical": ["sanction", "antitrust", "recall", "outage", "war", "insolvency", "bankruptcy", "catastrophe", "meltdown", "breach", "hack"],
    "high": ["breakthrough", "acquisition", "merger", "regulation", "fda approval", "earnings", "subpoena", "lawsuit", "investigation", "ceo", "partnership", "rate cut", "rate hike", "inflation"],
    "moderate": ["unveils", "announces", "expands", "upgrades", "releases", "reports", "contracts", "guidance"]
}

RELIABLE_PUBLISHERS = {
    "reuters": 1.3,
    "bloomberg": 1.3,
    "financial times": 1.3,
    "wsj": 1.3,
    "wall street journal": 1.3,
    "bbc": 1.2,
    "bbc news": 1.2,
    "nature": 1.3,
    "science": 1.3,
    "associated press": 1.25,
    "ap": 1.25,
    "cnbc": 1.15,
    "techcrunch": 1.1,
    "the verge": 1.1
}

class ImportanceScorer:
    """
    Computes explainable relevance and importance metrics.
    Labels: 'low', 'moderate', 'high', 'critical'.
    """

    @classmethod
    def score_item(
        cls,
        item: NewsItemOut,
        user_topics: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates relevance score (0.0 - 10.0) and importance label.
        Returns score metadata explaining the signals.
        """
        score = 1.0
        reasons = []

        text_corpus = f"{item.headline} {item.summary}".lower()

        # 1. Severity & Market Impact Keywords
        matched_level = None
        for kw in HIGH_IMPACT_KEYWORDS["critical"]:
            if re.search(rf"\b{re.escape(kw)}\b", text_corpus):
                score += 3.5
                reasons.append(f"Critical impact keyword: '{kw}'")
                matched_level = "critical"
                break

        if not matched_level:
            for kw in HIGH_IMPACT_KEYWORDS["high"]:
                if re.search(rf"\b{re.escape(kw)}\b", text_corpus):
                    score += 2.0
                    reasons.append(f"High-impact development keyword: '{kw}'")
                    matched_level = "high"
                    break

        if not matched_level:
            for kw in HIGH_IMPACT_KEYWORDS["moderate"]:
                if re.search(rf"\b{re.escape(kw)}\b", text_corpus):
                    score += 1.0
                    reasons.append(f"Standard event keyword: '{kw}'")
                    break

        # 2. Breaking News flag
        if item.is_breaking:
            score += 2.0
            reasons.append("Flagged as breaking wire update")

        # 3. Publisher Reliability Weight
        pub_lower = item.publisher.lower()
        pub_weight = 1.0
        for known_pub, weight in RELIABLE_PUBLISHERS.items():
            if known_pub in pub_lower:
                pub_weight = weight
                reasons.append(f"Verified tier-1 wire reliability ({item.publisher})")
                break
        score *= pub_weight

        # 4. User Followed Topic & Entity Match
        if user_topics:
            for topic in user_topics:
                q_terms = [t.strip().lower() for t in topic.get("query", "").split() if len(t.strip()) > 2]
                name = topic.get("topic_name", "").lower()
                ticker = (topic.get("ticker") or "").lower()
                entity = (topic.get("entity_id") or "").lower()

                # Ticker exact match
                if ticker and re.search(rf"\b{re.escape(ticker)}\b", text_corpus):
                    score += 3.0
                    reasons.append(f"Exact ticker match (${ticker.upper()})")
                    break
                # Topic name match
                if name and name in text_corpus:
                    score += 2.5
                    reasons.append(f"Followed topic match ('{topic.get('topic_name')}')")
                    break
                # Entity match
                if entity and entity in text_corpus:
                    score += 2.0
                    reasons.append(f"Followed entity match ('{entity}')")
                    break
                # Query terms match
                if q_terms and all(t in text_corpus for t in q_terms):
                    score += 1.5
                    reasons.append(f"Search query match ('{topic.get('query')}')")
                    break

        # 5. Determine Label
        if score >= 6.5:
            label = "critical"
        elif score >= 4.0:
            label = "high"
        elif score >= 2.0:
            label = "moderate"
        else:
            label = "low"

        return {
            "score": round(score, 2),
            "label": label,
            "explanation": "; ".join(reasons) if reasons else "General standard reporting"
        }

    @classmethod
    def score_cluster(
        cls,
        cluster: Dict[str, Any],
        member_items: List[NewsItemOut]
    ) -> str:
        """
        Determines overall cluster importance level based on source breadth and member item scores.
        """
        publisher_count = len(set(cl_s for cl_s in cluster.get("sources", [])))
        has_critical = any(getattr(m, "importance_label", "normal") == "critical" for m in member_items)
        has_high = any(getattr(m, "importance_label", "normal") == "high" or m.is_breaking for m in member_items)

        if has_critical or (publisher_count >= 3 and has_high):
            return "critical"
        elif has_high or publisher_count >= 2:
            return "high"
        elif publisher_count >= 1:
            return "moderate"
        return "low"

importance_scorer = ImportanceScorer()
