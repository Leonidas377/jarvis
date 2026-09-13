# ==========================================================================
# JARVIS Deterministic Demo Search Provider
# Clearly labeled simulated provider for offline testing and air-gapped environments
# ==========================================================================

import time
import uuid
from typing import List, Optional
from server.services.search.base import BaseSearchProvider
from server.models.schemas import SearchResultItem

class DemoSearchProvider(BaseSearchProvider):
    provider_name: str = "Demo Search Engine (Simulated)"

    async def search(
        self,
        query: str,
        limit: int = 8,
        category: Optional[str] = "all",
        region: Optional[str] = "us-en"
    ) -> List[SearchResultItem]:
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        mock_templates = [
            {
                "title": f"Scientific Benchmarks and Empirical Advances in {query}",
                "url": "https://nature.com/articles/computing-2026",
                "domain": "nature.com",
                "publisher": "Nature Computing",
                "snippet": f"A comprehensive review of {query} demonstrating low latency and high energy efficiency in distributed clusters.",
                "published_date": "2026-09-01"
            },
            {
                "title": f"Technical Consortium Architecture Report on {query}",
                "url": "https://arxiv.org/abs/2608.12991",
                "domain": "arxiv.org",
                "publisher": "ArXiv Preprint Server",
                "snippet": f"Empirical findings regarding fault-tolerant architectures and verification frameworks for {query}.",
                "published_date": "2026-08-28"
            },
            {
                "title": f"Industrial Readiness and Global Supply Chain for {query}",
                "url": "https://ieee.org/spectrum/insights-2026",
                "domain": "ieee.org",
                "publisher": "IEEE Spectrum",
                "snippet": f"Industry analysis analyzing commercial scaling barriers and silicon roadmap for {query}.",
                "published_date": "2026-08-15"
            }
        ]

        results = []
        for i, item in enumerate(mock_templates[:limit], 1):
            results.append(SearchResultItem(
                id=str(uuid.uuid4()),
                title=item["title"],
                url=item["url"],
                canonical_url=item["url"],
                domain=item["domain"],
                publisher=item["publisher"],
                snippet=item["snippet"],
                published_date=item["published_date"],
                rank=i,
                provider=self.provider_name,
                retrieval_timestamp=now_str,
                saved=False
            ))

        return results
