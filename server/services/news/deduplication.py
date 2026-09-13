# ==========================================================================
# JARVIS News Deduplication & Event Clustering Engine
# Groups similar breaking headlines across multiple publishers into cohesive event clusters
# ==========================================================================

import re
import uuid
import hashlib
from typing import List, Dict, Any, Tuple
from server.models.schemas import NewsItemOut

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "it", "its", "that", "this"
}

def tokenize_headline(text: str) -> set:
    """Extracts significant words from a headline for similarity comparison, normalizing plurals and tech acronyms."""
    words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
    # Light stemming for plurals
    stemmed = [w.rstrip("s") if len(w) > 3 and not w.endswith("ss") else w for w in words]
    return {w for w in stemmed if w not in STOP_WORDS}

def calculate_jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculates Jaccard overlap between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

from urllib.parse import urlparse, parse_qs, urlunparse
from server.services.news.importance_scorer import importance_scorer

CONFLICT_KEYWORDS = [
    ("surge", "plunge"), ("rises", "drops"), ("gain", "loss"),
    ("approve", "reject"), ("beat", "miss"), ("expand", "cut"),
    ("growth", "decline"), ("bullish", "bearish")
]

def normalize_url(url: str) -> str:
    """Strips query tracking parameters (utm_*, ref, etc.) and trailing slashes."""
    try:
        p = urlparse(url)
        # Keep query only if it's essential (not utm or ref)
        filtered_qs = "&".join([f"{k}={v[0]}" for k, v in parse_qs(p.query).items() if not k.startswith("utm_") and k not in {"ref", "source", "fbclid"}])
        clean_path = p.path.rstrip("/")
        return urlunparse((p.scheme.lower(), p.netloc.lower(), clean_path, p.params, filtered_qs, ""))
    except Exception:
        return url.strip().lower()

def detect_conflicting_coverage(headlines: List[str]) -> bool:
    """Flags potential conflicting coverage across multiple publishers."""
    text_corpus = " ".join(headlines).lower()
    for pos, neg in CONFLICT_KEYWORDS:
        if pos in text_corpus and neg in text_corpus:
            return True
    return False

class NewsClusterer:
    @staticmethod
    def cluster_items(
        items: List[NewsItemOut],
        threshold: float = 0.35,
        user_topics: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], List[NewsItemOut]]:
        """
        Groups duplicate and related news stories into clusters using multi-signal correlation.
        Returns (clusters_list, updated_items_with_cluster_ids).
        """
        # Step 1: Pre-score all items with importance & relevance
        for item in items:
            score_meta = importance_scorer.score_item(item, user_topics)
            item.relevance_score = score_meta["score"]
            item.importance_label = score_meta["label"]

        clusters: List[Dict[str, Any]] = []
        tokenized_items = [(item, tokenize_headline(item.headline), normalize_url(item.canonical_url or item.url)) for item in items]
        assigned_cluster: Dict[str, str] = {}

        for item, tokens, norm_url in tokenized_items:
            best_cluster = None
            best_score = 0.0

            # Compare against existing clusters
            for cl in clusters:
                # 1. URL exact canonical match
                if norm_url and norm_url in cl["canonical_urls"]:
                    best_cluster = cl
                    best_score = 1.0
                    break

                # 2. Token Jaccard similarity & Entity Overlap
                jaccard_score = calculate_jaccard_similarity(tokens, cl["tokens"])
                
                # Check entity overlap
                item_entities = set(e.lower() for e in (item.related_entities or []))
                cl_entities = set(e.lower() for e in cl.get("related_entities", []))
                has_entity_overlap = bool(item_entities and (item_entities & cl_entities))

                # If they share an entity, apply correlation boost
                combined_score = jaccard_score + (0.15 if has_entity_overlap else 0.0)

                if combined_score > best_score and combined_score >= threshold:
                    best_score = combined_score
                    best_cluster = cl

            if best_cluster:
                # Add to existing cluster
                best_cluster["item_ids"].append(item.id)
                best_cluster["sources"].append(item.publisher)
                best_cluster["headlines"].append(item.headline)
                best_cluster["tokens"].update(tokens)
                if norm_url:
                    best_cluster["canonical_urls"].add(norm_url)
                if item.related_entities:
                    best_cluster["related_entities"].extend(item.related_entities)

                # Update observed timestamps
                if item.published_at < best_cluster["first_observed_at"]:
                    best_cluster["first_observed_at"] = item.published_at
                if item.published_at > best_cluster["last_observed_at"]:
                    best_cluster["last_observed_at"] = item.published_at

                assigned_cluster[item.id] = best_cluster["id"]
            else:
                # Create a new cluster with deterministic ID based on significant tokens
                sig = "-".join(sorted(list(tokens))[:4]) if tokens else item.headline.lower()[:32]
                new_cl_id = hashlib.sha256(f"cl-{sig}".encode()).hexdigest()[:16]
                new_cluster = {
                    "id": new_cl_id,
                    "representative_headline": item.headline,
                    "summary": item.summary,
                    "tokens": set(tokens),
                    "canonical_urls": {norm_url} if norm_url else set(),
                    "item_ids": [item.id],
                    "sources": [item.publisher],
                    "headlines": [item.headline],
                    "category": item.category,
                    "related_entities": list(item.related_entities or []),
                    "first_observed_at": item.published_at,
                    "last_observed_at": item.published_at,
                    "importance_level": item.importance_label
                }
                clusters.append(new_cluster)
                assigned_cluster[item.id] = new_cl_id

        # Post-process clusters: compute publisher count, conflicting coverage, and cluster importance
        for cl in clusters:
            unique_sources = list(dict.fromkeys(cl["sources"]))
            cl["publisher_count"] = len(unique_sources)
            cl["source_count"] = len(cl["item_ids"])
            cl["conflicting_coverage"] = detect_conflicting_coverage(cl["headlines"])
            cl["related_entities"] = list(dict.fromkeys(cl["related_entities"]))

            # Member items for cluster importance calculation
            cluster_members = [item for item in items if item.id in cl["item_ids"]]
            cl["importance_level"] = importance_scorer.score_cluster(cl, cluster_members)
            cl["importance"] = cl["importance_level"] # backward compatibility

        # Update items with their cluster IDs
        for item in items:
            item.cluster_id = assigned_cluster.get(item.id)

        return clusters, items

clusterer = NewsClusterer()

