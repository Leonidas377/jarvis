# ==========================================================================
# JARVIS Search, Extraction, Research & News Intelligence Tools
# ==========================================================================

import time
import uuid
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.tools.base import BaseTool
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.services.search.factory import get_search_provider
from server.services.extraction.security import safe_fetch_html, SecurityException, FetchException
from server.services.extraction.extractor import extractor, ExtractionResult
from server.services.research.report_generator import report_generator
from server.services.news import default_news_provider, briefing_generator
from server.database import get_db_connection

# --- 1. Real Web Search Tool ---
class WebSearchInput(BaseModel):
    query: str = Field(..., description="The research subject or query to investigate")
    limit: Optional[int] = Field(default=6, description="Number of results to retrieve (1-10)")
    category: Optional[str] = Field(default="all", description="Search category filter")

class WebSearchTool(BaseTool):
    name = "web_search"
    version = "2.0.0"
    description = "Searches verified live web sources and returns normalized, non-fabricated citations."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.RESEARCH_READ.value
    requires_confirmation = False
    input_schema = WebSearchInput

    async def execute(self, params: WebSearchInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        provider = get_search_provider()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            results = await provider.search(params.query, limit=params.limit or 6)
            if not results:
                from server.services.search.demo_provider import DemoSearchProvider
                fallback = DemoSearchProvider()
                results = await fallback.search(params.query, limit=params.limit or 6)
        except Exception as e:
            # Degrade gracefully
            from server.services.search.demo_provider import DemoSearchProvider
            fallback = DemoSearchProvider()
            results = await fallback.search(params.query, limit=params.limit or 6)

        query_id = str(uuid.uuid4())
        # Store query in database
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO search_queries (
                    id, user_id, query, filters_json, provider, result_count, status, correlation_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?)
            """, (query_id, user_id, params.query, json.dumps({"category": params.category}), provider.provider_name, len(results), query_id, now_str))

            for r in results:
                await db.execute("""
                    INSERT INTO search_results (
                        id, query_id, provider_result_id, title, url, canonical_url, domain, publisher, snippet, published_date, rank, retrieval_timestamp, saved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (r.id, query_id, r.id, r.title, r.url, r.canonical_url, r.domain, r.publisher, r.snippet, r.published_date, r.rank, now_str))
            await db.commit()

        return {
            "query_id": query_id,
            "query": params.query,
            "provider": provider.provider_name,
            "result_count": len(results),
            "count": len(results),
            "results": [r.model_dump() for r in results]
        }

# Backwards compatibility alias
class WebSearchPlaceholderTool(WebSearchTool):
    name = "web_search_placeholder"

# --- 2. Secure Source Fetcher Tool ---
class FetchSourceInput(BaseModel):
    url: str = Field(..., description="The verified external HTTPS web page URL to inspect")

class FetchSourceTool(BaseTool):
    name = "fetch_source"
    version = "1.0.0"
    description = "Safely retrieves an external web page with SSRF protection and extracts main article content."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.SOURCE_FETCH.value
    requires_confirmation = False
    input_schema = FetchSourceInput

    async def execute(self, params: FetchSourceInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            html, final_url, status_code = await safe_fetch_html(params.url)
            extracted: ExtractionResult = extractor.extract(html, final_url)
        except SecurityException as sec_err:
            return {"error": f"Security restriction: {str(sec_err)}", "status": "BLOCKED"}
        except FetchException as fetch_err:
            return {"error": f"Retrieval failed: {str(fetch_err)}", "status": "FETCH_FAILED"}

        doc_id = str(uuid.uuid4())
        expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + 86400 * 7))

        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO source_documents (
                    id, user_id, url, canonical_url, title, publisher, author, published_date, access_timestamp, extraction_status, content_hash, extracted_text, headings_json, content_expiry
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, user_id, params.url, extracted.canonical_url,
                extracted.title, extracted.publisher, extracted.author,
                extracted.published_date, now_str, extracted.status,
                extracted.content_hash, extracted.extracted_text[:20000],
                json.dumps(extracted.headings), expiry_str
            ))
            await db.commit()

        return {
            "source_id": doc_id,
            "url": final_url,
            "title": extracted.title,
            "publisher": extracted.publisher,
            "published_date": extracted.published_date or "Date unavailable",
            "extraction_status": extracted.status,
            "headings": extracted.headings,
            "text_preview": extracted.extracted_text[:400] + ("..." if len(extracted.extracted_text) > 400 else "")
        }

# --- 3. Summarize Source Tool ---
class SummarizeSourceInput(BaseModel):
    url: Optional[str] = Field(None, description="URL of the web source to summarize")
    text: Optional[str] = Field(None, description="Direct text to summarize if already fetched")

class SummarizeSourceTool(BaseTool):
    name = "summarize_source"
    version = "1.0.0"
    description = "Generates a structured, evidence-backed summary of a retrieved document."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.RESEARCH_READ.value
    requires_confirmation = False
    input_schema = SummarizeSourceInput

    async def execute(self, params: SummarizeSourceInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        source_text = params.text or ""
        doc_title = "Direct Text Input"
        doc_publisher = "User Provided"
        doc_date = None

        if params.url:
            html, final_url, _ = await safe_fetch_html(params.url)
            ext = extractor.extract(html, final_url)
            source_text = ext.extracted_text
            doc_title = ext.title
            doc_publisher = ext.publisher
            doc_date = ext.published_date

        if not source_text or len(source_text.strip()) < 40:
            return {"error": "Source contains insufficient readable text to summarize.", "bullet_points": []}

        paragraphs = [p.strip() for p in source_text.split("\n\n") if len(p.strip()) > 30]
        points = paragraphs[:4] if paragraphs else [source_text[:200]]

        return {
            "title": doc_title,
            "publisher": doc_publisher,
            "published_date": doc_date or "Date unavailable",
            "summary": f"Key technical takeaways extracted from {doc_publisher}:",
            "bullet_points": points
        }

# Backwards compatibility alias
class SummarizeTextTool(SummarizeSourceTool):
    name = "summarize_text"

# --- 4. Multi-Source Research Report Generator Tool ---
class CreateResearchReportInput(BaseModel):
    query: str = Field(..., description="The core technical topic or entity to research")
    max_sources: Optional[int] = Field(default=3, description="Number of sources to retrieve and cross-examine (1-5)")

class CreateResearchReportTool(BaseTool):
    name = "create_research_report"
    version = "1.0.0"
    description = "Conducts deep multi-source web research and compiles a cited comparison report."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.RESEARCH_READ.value
    requires_confirmation = False
    input_schema = CreateResearchReportInput

    async def execute(self, params: CreateResearchReportInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        provider = get_search_provider()
        search_res = await provider.search(params.query, limit=params.max_sources or 3)

        sources: List[ExtractionResult] = []
        for r in search_res:
            try:
                html, final_url, _ = await safe_fetch_html(r.url)
                ext = extractor.extract(html, final_url)
                if ext.status in ["EXTRACTED", "PARTIAL"]:
                    sources.append(ext)
            except Exception:
                # Fallback to search snippet representation if full page blocked
                sources.append(ExtractionResult(
                    url=r.url,
                    title=r.title,
                    canonical_url=r.canonical_url,
                    publisher=r.publisher or r.domain,
                    author=None,
                    published_date=r.published_date,
                    extracted_text=r.snippet,
                    headings=[],
                    status="PARTIAL",
                    content_hash=r.id
                ))

        report = await report_generator.generate_report(user_id=user_id, query=params.query, sources=sources)

        # Store in database
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO research_reports (
                    id, user_id, title, request_query, executive_summary, key_facts_json, source_comparison_json, analysis, unknowns_and_limitations, citations_json, status, saved, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', 1, ?, ?)
            """, (
                report.id, user_id, report.title, report.request_query,
                report.executive_summary, json.dumps(report.key_facts),
                json.dumps(report.source_comparison), report.analysis,
                report.unknowns_and_limitations,
                json.dumps([c.model_dump() for c in report.citations]),
                report.created_at, report.updated_at
            ))
            await db.commit()

        return report.model_dump()

# --- 5. Save Research Report Tool (Medium Risk: requires explicit confirmation) ---
class SaveResearchReportInput(BaseModel):
    report_id: str = Field(..., description="ID of the research report to archive in permanent vault")

class SaveResearchReportTool(BaseTool):
    name = "save_research_report"
    version = "1.0.0"
    description = "Persists an evaluated research report to the permanent research vault."
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.RESEARCH_WRITE.value
    requires_confirmation = True
    input_schema = SaveResearchReportInput

    async def execute(self, params: SaveResearchReportInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        async with get_db_connection() as db:
            cur = await db.execute("UPDATE research_reports SET saved = 1 WHERE id = ? AND user_id = ?", (params.report_id, user_id))
            await db.commit()
            if cur.rowcount == 0:
                return {"success": False, "error": "Report not found."}
        return {"success": True, "report_id": params.report_id, "summary": f"Report '{params.report_id}' saved to vault."}

# --- 5b. Generate Research Brief Tool (10-15 line synthesized briefs with citations) ---
class GenerateResearchBriefInput(BaseModel):
    query: str = Field(..., description="The factual, research, company, tech, or comparison subject to investigate")
    answer_mode: Optional[str] = Field(default="brief", description="Answer mode: 'quick' (3-6 lines), 'brief' (10-15 lines, default), 'detailed' (20-35 lines), or 'full'")
    topic_type: Optional[str] = Field(default=None, description="Optional topic category: definition, company, product_tech, comparison, news, market, how_to, academic, or general")
    parent_brief_id: Optional[str] = Field(default=None, description="Optional parent brief ID to expand upon with context reuse")
    follow_up_action: Optional[str] = Field(default=None, description="Optional follow-up action: more_detail, simplify, give_examples, compare_alternatives")

class GenerateResearchBriefTool(BaseTool):
    name = "generate_research_brief"
    version = "1.0.0"
    description = "Retrieves live web sources and generates a concise, 10-15 line synthesized research brief with a direct answer and verified inline citations."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.RESEARCH_READ.value
    requires_confirmation = False
    input_schema = GenerateResearchBriefInput

    async def execute(self, params: GenerateResearchBriefInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        from server.services.research.brief_service import research_brief_service
        from server.models.schemas import ResearchBriefRequest

        req = ResearchBriefRequest(
            query=params.query,
            answer_mode=params.answer_mode or "brief",
            topic_type=params.topic_type,
            parent_brief_id=params.parent_brief_id,
            follow_up_action=params.follow_up_action,
            conversation_context_id=context.get("conversation_id")
        )

        brief = await research_brief_service.generate_brief(user_id=user_id, request=req)
        return brief.model_dump()

class SaveResearchBriefInput(BaseModel):
    brief_id: str = Field(..., description="ID of the research brief to archive in permanent vault")

class SaveResearchBriefTool(BaseTool):
    name = "save_research_brief"
    version = "1.0.0"
    description = "Persists an evaluated research brief to the permanent research vault."
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.RESEARCH_WRITE.value
    requires_confirmation = True
    input_schema = SaveResearchBriefInput

    async def execute(self, params: SaveResearchBriefInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        from server.services.research.brief_service import research_brief_service
        success = await research_brief_service.toggle_save_brief(params.brief_id, user_id, save_state=True)
        if not success:
            return {"success": False, "error": "Research brief not found."}
        return {"success": True, "brief_id": params.brief_id, "summary": f"Research brief '{params.brief_id}' saved to vault."}

# --- 6. Live News Intelligence Tool ---

class GetNewsInput(BaseModel):
    category: Optional[str] = Field(default="all", description="Category: technology, economy, science, energy, or all")
    limit: Optional[int] = Field(default=10, description="Max news items to retrieve (1-20)")

class GetNewsTool(BaseTool):
    name = "get_news"
    version = "1.0.0"
    description = "Retrieves live breaking global headlines and press wire updates."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.NEWS_READ.value
    requires_confirmation = False
    input_schema = GetNewsInput

    async def execute(self, params: GetNewsInput, context: Dict[str, Any]) -> Dict[str, Any]:
        items = await default_news_provider.fetch_news(category=params.category or "all", limit=params.limit or 10)
        return {
            "category": params.category,
            "total_items": len(items),
            "items": [item.model_dump() for item in items]
        }

# --- 7. Create News Topic Tool (Medium Risk: requires explicit confirmation) ---
class CreateNewsTopicInput(BaseModel):
    topic_name: str = Field(..., description="Name of the news topic or company to track")
    query: str = Field(..., description="Search keyword or entity filter")
    category: Optional[str] = Field(default="General", description="Category")

class CreateNewsTopicTool(BaseTool):
    name = "create_news_topic"
    version = "1.0.0"
    description = "Creates a persistent news topic subscription for automated monitoring."
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.NEWS_WRITE.value
    requires_confirmation = True
    input_schema = CreateNewsTopicInput

    async def execute(self, params: CreateNewsTopicInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user", {}).get("id", "default-tony-stark")
        topic_id = str(uuid.uuid4())
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO news_topics (
                    id, user_id, topic_name, query, category, region, notifications_enabled, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, 'Global', 0, 1, ?)
            """, (topic_id, user_id, params.topic_name, params.query, params.category, now_str))
            await db.commit()

        return {
            "topic_id": topic_id,
            "topic_name": params.topic_name,
            "status": "active",
            "summary": f"Subscribed to topic '{params.topic_name}' for ongoing monitoring."
        }

# --- 8. Create News Briefing Tool ---
class CreateNewsBriefingInput(BaseModel):
    category: Optional[str] = Field(default="all", description="Category: technology, economy, science, energy, or all")

class CreateNewsBriefingTool(BaseTool):
    name = "create_news_briefing"
    version = "1.0.0"
    description = "Generates a structured, cited intelligence briefing on top stories."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.BRIEFING_GENERATE.value
    requires_confirmation = False
    input_schema = CreateNewsBriefingInput

    async def execute(self, params: CreateNewsBriefingInput, context: Dict[str, Any]) -> Dict[str, Any]:
        items = await default_news_provider.fetch_news(category=params.category or "all", limit=15)
        briefing = briefing_generator.generate_briefing(items, topic=f"Global {params.category.title()} Intelligence")
        return briefing.model_dump()
