import pytest
from datetime import datetime, timezone
from server.services.news.deduplication import NewsClusterer
from server.services.news.briefing import NewsBriefingGenerator
from server.models.schemas import NewsItemOut

def test_news_clustering_and_deduplication():
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 3 items covering the same event from different publishers, and 1 unrelated item
    items = [
        NewsItemOut(
            id="item-1",
            headline="Google Invests 1 Billion Euros in Finnish Data Center",
            summary="Alphabet announced massive expansion of its data center in Hamina Finland.",
            url="https://reuters.com/tech/google-finland-datacenter-1",
            canonical_url="https://reuters.com/tech/google-finland-datacenter-1",
            publisher="Reuters",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Europe",
            related_entities=["Google", "Finland"]
        ),
        NewsItemOut(
            id="item-2",
            headline="Google Invests 1 Billion Euros in Finland Data Center",
            summary="Tech giant Alphabet commits funding to expand its clean data infrastructure in Finland.",
            url="https://bloomberg.com/news/google-hamina-green-power",
            canonical_url="https://bloomberg.com/news/google-hamina-green-power",
            publisher="Bloomberg",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Europe",
            related_entities=["Google", "Finland"]
        ),
        NewsItemOut(
            id="item-3",
            headline="Finland Google Data Center Receives 1 Billion Investment",
            summary="BBC wire reports major 1B euro data center project in Hamina.",
            url="https://bbc.com/news/technology-google-finland",
            canonical_url="https://bbc.com/news/technology-google-finland",
            publisher="BBC News",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Europe",
            related_entities=["Google", "Finland"]
        ),
        NewsItemOut(
            id="item-4",
            headline="James Webb Telescope detects atmospheric water on habitable-zone exoplanet",
            summary="Astronomers confirm spectroscopic evidence of liquid water clouds 120 light years away.",
            url="https://nasa.gov/news/jwst-exoplanet-water",
            canonical_url="https://nasa.gov/news/jwst-exoplanet-water",
            publisher="NASA Press",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Science",
            region="Global",
            related_entities=["NASA", "JWST"]
        )
    ]
    
    clusters, updated_items = NewsClusterer.cluster_items(items, threshold=0.25)
    
    # We expect 2 clusters: One for Google Finland data center and one for NASA JWST
    assert len(clusters) == 2
    
    # Find Google cluster
    google_cluster = next(c for c in clusters if "Finland" in c["representative_headline"] or "Google" in c["representative_headline"])
    assert len(google_cluster["item_ids"]) == 3
    assert "item-1" in google_cluster["item_ids"]
    assert "item-2" in google_cluster["item_ids"]
    assert "item-3" in google_cluster["item_ids"]

@pytest.mark.asyncio
async def test_news_briefing_generation():
    now_iso = datetime.now(timezone.utc).isoformat()
    items = [
        NewsItemOut(
            id="n-1",
            headline="Taiwan Semiconductor ramps 2nm trial wafer runs",
            summary="TSMC reports yield curves exceeding initial targets ahead of 2026 commercial volume.",
            url="https://digitimes.com/tsmc-2nm",
            publisher="DigiTimes",
            published_at=now_iso,
            retrieval_timestamp=now_iso,
            category="Technology",
            region="Asia",
            related_entities=["TSMC"]
        )
    ]
    
    briefing = await NewsBriefingGenerator.generate_briefing(items, topic="Semiconductor Intelligence")
    
    assert briefing.title is not None
    assert len(briefing.key_events) >= 1
    assert "TSMC" in briefing.key_events[0]["headline"] or "Taiwan Semiconductor" in briefing.key_events[0]["headline"]
    assert briefing.key_events[0]["summary"] is not None
    # Verify market notes are strictly observational and safe
    assert briefing.market_implications is not None
    assert "Observation:" in briefing.market_implications
    assert "no live financial execution" in briefing.market_implications
