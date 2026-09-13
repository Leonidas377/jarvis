# ==========================================================================
# JARVIS DuckDuckGo Search Provider
# Provides live, unauthenticated web search without external API key quotas
# ==========================================================================

import time
import uuid
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from server.services.search.base import BaseSearchProvider
from server.models.schemas import SearchResultItem

class DuckDuckGoSearchProvider(BaseSearchProvider):
    provider_name: str = "DuckDuckGo"

    def _unwrap_ddg_url(self, raw_url: str) -> str:
        """Extracts the actual destination URL from DuckDuckGo redirection wrapper."""
        if "uddg=" in raw_url:
            try:
                parsed = urlparse(raw_url)
                qs = parse_qs(parsed.query)
                if "uddg" in qs and qs["uddg"]:
                    return unquote(qs["uddg"][0])
            except Exception:
                pass
        if raw_url.startswith("//"):
            return "https:" + raw_url
        return raw_url

    async def search(
        self,
        query: str,
        limit: int = 8,
        category: Optional[str] = "all",
        region: Optional[str] = "us-en"
    ) -> List[SearchResultItem]:
        endpoint = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        data = {"q": query}
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(endpoint, data=data, headers=headers)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        results: List[SearchResultItem] = []
        rank = 1

        # DuckDuckGo HTML results container
        result_divs = soup.find_all("div", class_="result")

        for r_div in result_divs:
            if rank > limit:
                break

            # Title & URL link
            title_a = r_div.find("a", class_="result__a")
            if not title_a:
                continue

            title = title_a.get_text(strip=True)
            raw_href = title_a.get("href", "")
            target_url = self._unwrap_ddg_url(raw_href)

            if not target_url.startswith("http"):
                continue

            # Snippet
            snippet_tag = r_div.find("a", class_="result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            # Domain & Publisher
            parsed_domain = urlparse(target_url).netloc
            publisher = parsed_domain.replace("www.", "")

            item = SearchResultItem(
                id=str(uuid.uuid4()),
                title=title,
                url=target_url,
                canonical_url=target_url,
                domain=parsed_domain,
                publisher=publisher,
                snippet=snippet,
                published_date="Date unavailable",  # Honest label: do not invent dates
                rank=rank,
                provider=self.provider_name,
                retrieval_timestamp=now_str,
                saved=False
            )
            results.append(item)
            rank += 1

        return results
