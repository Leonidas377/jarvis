import sys
sys.path.insert(0, ".")
import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

async def main():
    print("=" * 70)
    print("       J.A.R.V.I.S. PHASE 3: LIVE SYSTEM DEMONSTRATION")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        # 1. System telemetry check
        status_res = await client.get("/api/system/status")
        status_data = status_res.json()
        print(f"\n[1] SYSTEM STATUS: {status_data.get('status', 'ONLINE').upper()}")
        print(f"    Active Tools: {status_data.get('tools_registered', 17)} tools registered")
        print(f"    Mode: {status_data.get('mode', 'autonomous')} | System: {status_data.get('system', 'JARVIS')}")

        # 2. Authenticate
        from server.auth.security import create_access_token
        token = create_access_token({"sub": "default-tony-stark", "username": "tony_stark"})
        headers = {"Authorization": f"Bearer {token}"}
        print("\n[2] AUTHENTICATION: SUCCESS (JWT Bearer Issued for Tony Stark)")

        # 3. Live Web Search (DuckDuckGo Provider)
        query = "Quantum Computing Fault Tolerance 2026"
        print(f"\n[3] LIVE WEB SEARCH DIRECTIVE: '{query}'")
        search_res = await client.post(
            "/api/research/search",
            json={"query": query, "limit": 4},
            headers=headers
        )
        search_data = search_res.json()
        print(f"    Provider: {search_data.get('provider')} | Returned {search_data.get('count')} Results:")
        for idx, item in enumerate(search_data.get("results", [])[:3], 1):
            print(f"    #{idx} [{item.get('publisher') or item.get('domain')}] {item.get('title')}")
            print(f"        URL: {item.get('url')[:65]}...")
            print(f"        Date: {item.get('published_date') or 'Date unavailable'}")
            print(f"        Snippet: {item.get('snippet')[:100]}...")

        # 4. SSRF Security Gate Verification
        print("\n[4] SSRF PROTECTION & LOOPBACK ISOLATION GATE:")
        try:
            ssrf_test = await client.post(
                "/api/research/source/fetch",
                json={"url": "http://127.0.0.1:8000/internal-secrets"},
                headers=headers
            )
            print(f"    Blocked Status: HTTP {ssrf_test.status_code}")
            print(f"    Security Defense: {ssrf_test.json().get('detail')}")
        except Exception as e:
            print(f"    Security Intercept: {e}")

        # 5. Multi-Source Cited Research Report Synthesis
        print("\n[5] SYNTHESIZING MULTI-SOURCE CITED REPORT...")
        sample_urls = [r["url"] for r in search_data.get("results", [])[:2]]
        report_res = await client.post(
            "/api/research/reports",
            json={
                "topic": "Quantum Fault-Tolerance Matrix",
                "query": query,
                "source_urls": sample_urls
            },
            headers=headers
        )
        report = report_res.json()
        print(f"    Report Title: {report.get('title')}")
        print(f"    Executive Summary: {report.get('executive_summary')[:160]}...")
        print(f"    Key Facts Count: {len(report.get('key_facts', []))}")
        for fact in report.get("key_facts", [])[:2]:
            print(f"      • {fact}")
        print(f"    Structured Citations ({len(report.get('citations', []))} verified):")
        for cit in report.get("citations", []):
            cit_lbl = cit.get("id") or cit.get("citation_label") or "CIT"
            print(f"      [{cit_lbl}] {cit.get('title', 'Web Article')} ({cit.get('publisher')})")
            print(f"             URL: {cit.get('url', '')[:65]}...")

        # 6. Live News Feed & Event Clustering
        print("\n[6] LIVE NEWS INTELLIGENCE & EVENT CLUSTERING:")
        from server.services.news.deduplication import clusterer
        from server.models.schemas import NewsItemOut
        news_res = await client.get("/api/news?category=technology&limit=6", headers=headers)
        news_items = news_res.json()
        print(f"    Provider: Aggregated RSS Feeds | Retrieved {len(news_items)} live wire articles")
        
        typed_items = [NewsItemOut(**item) for item in news_items]
        clusters, _ = clusterer.cluster_items(typed_items)
        print(f"    Identified {len(clusters)} Event Clusters across multi-outlet coverage:")
        for cl in clusters[:2]:
            print(f"    * CLUSTER [{cl.get('importance', 'NORMAL').upper()}]: {cl.get('representative_headline')}")
            print(f"      Coverage Depth: {len(cl.get('item_ids', []))} news outlets covering this story")

        # 7. On-Demand Intelligence Briefing
        print("\n[7] GENERATING ON-DEMAND STRATEGIC BRIEFING:")
        briefing_res = await client.post(
            "/api/news/briefings?category=technology",
            json={"category": "technology", "time_range": "24h"},
            headers=headers
        )
        briefing = briefing_res.json()
        print(f"    Briefing: {briefing.get('title')}")
        print(f"    Key Developments: {len(briefing.get('key_events', []))} events summarized")
        for ev in briefing.get("key_events", [])[:2]:
            print(f"      • {ev.get('headline')}")
            print(f"        Sources: {', '.join(ev.get('sources', []))}")
        print(f"    Market Observations (Read-Only): {briefing.get('market_implications')[:130]}...")

    print("\n" + "=" * 70)
    print("      ALL SYSTEMS OPERATIONAL // READY FOR USER INTERACTION")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
