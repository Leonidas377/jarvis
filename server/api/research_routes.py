# ==========================================================================
# JARVIS Research, Web Search & Source Intelligence API Routes
# ==========================================================================

import time
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import (
    SearchRequest, SearchResponseOut, SearchResultItem,
    SourceFetchRequest, SourceDocumentOut,
    ResearchReportCreate, ResearchReportOut, CitationItem,
    ResearchBriefRequest, ResearchBriefOut, ResearchBriefActionRequest,
    ResearchBriefRenameRequest, ResearchBriefExportOut
)
from server.services.search.factory import get_search_provider
from server.services.extraction.security import safe_fetch_html, SecurityException, FetchException
from server.services.extraction.extractor import extractor, ExtractionResult
from server.services.research.report_generator import report_generator
from server.services.research.brief_service import research_brief_service
from server.audit.logger import audit_logger


router = APIRouter(prefix="/api/research", tags=["Research & Web Intelligence"])

# --- 1. Web Search ---
@router.post("/search", response_model=SearchResponseOut)
async def execute_search(req: SearchRequest, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    provider = get_search_provider()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        results = await provider.search(req.query, limit=req.limit or 8, category=req.category, region=req.region)
    except Exception as e:
        from server.services.search.demo_provider import DemoSearchProvider
        fallback = DemoSearchProvider()
        results = await fallback.search(req.query, limit=req.limit or 8)

    query_id = str(uuid.uuid4())

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO search_queries (
                id, user_id, query, filters_json, provider, result_count, status, correlation_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?)
        """, (query_id, user_id, req.query, json.dumps({"category": req.category, "region": req.region}), provider.provider_name, len(results), query_id, now_str))

        for r in results:
            await db.execute("""
                INSERT INTO search_results (
                    id, query_id, provider_result_id, title, url, canonical_url, domain, publisher, snippet, published_date, rank, retrieval_timestamp, saved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (r.id, query_id, r.id, r.title, r.url, r.canonical_url, r.domain, r.publisher, r.snippet, r.published_date, r.rank, now_str))
        await db.commit()

    await audit_logger.log_event(
        event_type="SEARCH_PERFORMED",
        action="research.search",
        user_id=user_id,
        correlation_id=query_id,
        details={"query": req.query, "provider": provider.provider_name, "count": len(results)}
    )

    return SearchResponseOut(
        query_id=query_id,
        query=req.query,
        provider=provider.provider_name,
        total_results=len(results),
        results=results,
        status="completed"
    )

@router.get("/search-history")
async def get_search_history(limit: int = Query(20, le=50), user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, query, filters_json, provider, result_count, status, created_at
            FROM search_queries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user["id"], limit))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

@router.get("/search/{query_id}", response_model=SearchResponseOut)
async def get_search_by_id(query_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur_q = await db.execute("SELECT * FROM search_queries WHERE id = ? AND user_id = ?", (query_id, user["id"]))
        q_row = await cur_q.fetchone()
        if not q_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search query record not found.")

        cur_r = await db.execute("SELECT * FROM search_results WHERE query_id = ? ORDER BY rank ASC", (query_id,))
        r_rows = await cur_r.fetchall()

        results = []
        for r in r_rows:
            results.append(SearchResultItem(
                id=r["id"],
                title=r["title"],
                url=r["url"],
                canonical_url=r["canonical_url"],
                domain=r["domain"],
                publisher=r["publisher"],
                snippet=r["snippet"] or "",
                published_date=r["published_date"],
                rank=r["rank"],
                provider=q_row["provider"],
                retrieval_timestamp=r["retrieval_timestamp"],
                saved=bool(r["saved"])
            ))

        return SearchResponseOut(
            query_id=q_row["id"],
            query=q_row["query"],
            provider=q_row["provider"],
            total_results=len(results),
            results=results,
            status=q_row["status"]
        )

@router.post("/results/{result_id}/save")
async def save_search_result(result_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("UPDATE search_results SET saved = 1 WHERE id = ?", (result_id,))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search result not found.")
    return {"success": True, "result_id": result_id, "saved": True}

@router.delete("/results/{result_id}/save")
async def unsave_search_result(result_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("UPDATE search_results SET saved = 0 WHERE id = ?", (result_id,))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search result not found.")
    return {"success": True, "result_id": result_id, "saved": False}

# --- 2. Source Fetching & Extraction (SSRF Protected) ---
@router.post("/source/fetch", response_model=SourceDocumentOut)
async def fetch_source(req: SourceFetchRequest, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        html, final_url, status_code = await safe_fetch_html(req.url)
        ext: ExtractionResult = extractor.extract(html, final_url)
    except SecurityException as sec_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Security violation: {str(sec_err)}")
    except FetchException as fetch_err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Source fetch failed: {str(fetch_err)}")

    doc_id = str(uuid.uuid4())
    expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + 86400 * 7))

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO source_documents (
                id, user_id, url, canonical_url, title, publisher, author, published_date, access_timestamp, extraction_status, content_hash, extracted_text, headings_json, content_expiry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, user_id, req.url, ext.canonical_url,
            ext.title, ext.publisher, ext.author,
            ext.published_date, now_str, ext.status,
            ext.content_hash, ext.extracted_text[:20000],
            json.dumps(ext.headings), expiry_str
        ))
        await db.commit()

    await audit_logger.log_event(
        event_type="SOURCE_FETCHED",
        action="research.source_fetch",
        user_id=user_id,
        resource_id=doc_id,
        details={"url": req.url, "status": ext.status, "publisher": ext.publisher}
    )

    return SourceDocumentOut(
        id=doc_id,
        url=final_url,
        canonical_url=ext.canonical_url,
        title=ext.title,
        publisher=ext.publisher,
        author=ext.author,
        published_date=ext.published_date,
        access_timestamp=now_str,
        extraction_status=ext.status,
        extracted_text=ext.extracted_text,
        headings=ext.headings,
        content_expiry=expiry_str
    )

# --- 3. Research Reports ---
@router.post("/reports", response_model=ResearchReportOut, status_code=status.HTTP_201_CREATED)
async def create_research_report(req: ResearchReportCreate, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    sources: List[ExtractionResult] = []

    if req.source_urls:
        for url in req.source_urls[:req.max_sources or 3]:
            try:
                html, final_url, _ = await safe_fetch_html(url)
                ext = extractor.extract(html, final_url)
                if ext.status in ["EXTRACTED", "PARTIAL"]:
                    sources.append(ext)
            except Exception:
                pass

    if not sources:
        # Perform automatic live search to gather sources
        provider = get_search_provider()
        search_res = await provider.search(req.query, limit=req.max_sources or 3)

        async def fetch_one(r_item):
            try:
                html, final_url, _ = await safe_fetch_html(r_item.url)
                ext = extractor.extract(html, final_url)
                if ext.status in ["EXTRACTED", "PARTIAL"]:
                    return ext
            except Exception:
                pass
            return ExtractionResult(
                url=r_item.url,
                title=r_item.title,
                canonical_url=r_item.canonical_url,
                publisher=r_item.publisher or r_item.domain,
                author=None,
                published_date=r_item.published_date,
                extracted_text=r_item.snippet,
                headings=[],
                status="PARTIAL",
                content_hash=r_item.id
            )

        import asyncio
        tasks = [fetch_one(r) for r in search_res]
        sources = await asyncio.gather(*tasks)

    report = await report_generator.generate_report(user_id=user_id, query=req.query, sources=sources)

    # Persist in database
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

    await audit_logger.log_event(
        event_type="RESEARCH_REPORT_GENERATED",
        action="research.report_create",
        user_id=user_id,
        resource_id=report.id,
        details={"query": req.query, "citations_count": len(report.citations)}
    )

    return report

@router.get("/reports", response_model=List[ResearchReportOut])
async def list_research_reports(user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT * FROM research_reports WHERE user_id = ? ORDER BY created_at DESC
        """, (user["id"],))
        rows = await cur.fetchall()

        reports = []
        for r in rows:
            reports.append(ResearchReportOut(
                id=r["id"],
                user_id=r["user_id"],
                title=r["title"],
                request_query=r["request_query"],
                executive_summary=r["executive_summary"],
                key_facts=json.loads(r["key_facts_json"]),
                source_comparison=json.loads(r["source_comparison_json"] or "[]"),
                analysis=r["analysis"],
                unknowns_and_limitations=r["unknowns_and_limitations"],
                citations=[CitationItem(**c) for c in json.loads(r["citations_json"])],
                status=r["status"],
                saved=bool(r["saved"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return reports

@router.get("/reports/{report_id}", response_model=ResearchReportOut)
async def get_report_by_id(report_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM research_reports WHERE id = ? AND user_id = ?", (report_id, user["id"]))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found.")

        return ResearchReportOut(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            request_query=row["request_query"],
            executive_summary=row["executive_summary"],
            key_facts=json.loads(row["key_facts_json"]),
            source_comparison=json.loads(row["source_comparison_json"] or "[]"),
            analysis=row["analysis"],
            unknowns_and_limitations=row["unknowns_and_limitations"],
            citations=[CitationItem(**c) for c in json.loads(row["citations_json"])],
            status=row["status"],
            saved=bool(row["saved"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM research_reports WHERE id = ? AND user_id = ?", (report_id, user["id"]))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found.")

    await audit_logger.log_event(
        event_type="RESEARCH_REPORT_DELETED",
        action="research.report_delete",
        user_id=user["id"],
        resource_id=report_id
    )
    return {"success": True, "report_id": report_id, "message": "Report permanently removed from notebook."}

@router.post("/reports/{report_id}/export")
async def export_report(report_id: str, format: str = Query("markdown", pattern="^(markdown|json)$"), user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM research_reports WHERE id = ? AND user_id = ?", (report_id, user["id"]))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found.")

    if format == "json":
        return {
            "title": row["title"],
            "query": row["request_query"],
            "summary": row["executive_summary"],
            "facts": json.loads(row["key_facts_json"]),
            "analysis": row["analysis"],
            "citations": json.loads(row["citations_json"])
        }

    # Markdown export
    facts = json.loads(row["key_facts_json"])
    citations = json.loads(row["citations_json"])
    md_lines = [
        f"# {row['title']}",
        f"**Date:** {row['created_at']} | **Author:** J.A.R.V.I.S. Research Core",
        f"**Subject:** {row['request_query']}",
        "",
        "## Executive Summary",
        row["executive_summary"],
        "",
        "## Key Empirical Facts",
        "\n".join([f"- {f}" for f in facts]),
        "",
        "## Analysis & Implications",
        row["analysis"] or "No analytical caveats noted.",
        "",
        "## Unknowns & Limitations",
        row["unknowns_and_limitations"] or "Data current at retrieval timestamp.",
        "",
        "## Verified Citations",
        "\n".join([f"[{c['id']}] {c['title']} ({c['publisher']}) - <{c['url']}>" for c in citations])
    ]
    return {"format": "markdown", "content": "\n".join(md_lines)}

# --- 4. Research Briefs (10-15 line synthesized briefs with verified citations) ---
@router.post("/briefs", response_model=ResearchBriefOut, status_code=status.HTTP_201_CREATED)
@router.post("/brief", response_model=ResearchBriefOut, status_code=status.HTTP_201_CREATED)
async def generate_research_brief(req: ResearchBriefRequest, user: dict = Depends(get_optional_user)):
    """
    Generates an autonomous, concise 10-15 line research brief.
    Includes direct answer first, inline citations, compact sources, and takeaway.
    Supports response modes: 'quick' (3-6), 'brief' (10-15), 'detailed' (20-35), 'full'.
    """
    user_id = user["id"]
    try:
        brief = await research_brief_service.generate_brief(user_id=user_id, request=req)
        return brief
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research brief generation failed: {str(e)}"
        )

@router.get("/briefs", response_model=List[ResearchBriefOut])
async def list_saved_briefs(
    query: Optional[str] = Query(None, description="Optional search term to filter saved briefs"),
    limit: int = Query(20, le=50),
    user: dict = Depends(get_optional_user)
):
    """Lists or searches saved research briefs in the permanent vault."""
    user_id = user["id"]
    return await research_brief_service.search_saved_briefs(user_id=user_id, query=query, limit=limit)

@router.get("/briefs/{brief_id}", response_model=ResearchBriefOut)
@router.get("/brief/{brief_id}", response_model=ResearchBriefOut)
async def get_brief_by_id(brief_id: str, user: dict = Depends(get_optional_user)):
    """Retrieves a single research brief by ID."""
    user_id = user["id"]
    brief = await research_brief_service.get_brief_by_id(brief_id, user_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found.")
    return brief

@router.patch("/briefs/{brief_id}", response_model=Dict[str, Any])
@router.patch("/brief/{brief_id}", response_model=Dict[str, Any])
async def rename_brief(brief_id: str, req: ResearchBriefRenameRequest, user: dict = Depends(get_optional_user)):
    """Renames a saved research brief."""
    user_id = user["id"]
    success = await research_brief_service.rename_brief(brief_id, user_id, req.title)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found or not owned by user.")
    return {"success": True, "brief_id": brief_id, "title": req.title}

@router.delete("/briefs/{brief_id}", response_model=Dict[str, Any])
@router.delete("/brief/{brief_id}", response_model=Dict[str, Any])
async def delete_brief(brief_id: str, user: dict = Depends(get_optional_user)):
    """Deletes a research brief from the permanent vault."""
    user_id = user["id"]
    success = await research_brief_service.delete_brief(brief_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found or not owned by user.")
    return {"success": True, "brief_id": brief_id, "deleted": True}

@router.post("/briefs/{brief_id}/save")
@router.post("/brief/{brief_id}/save")
async def save_brief(brief_id: str, user: dict = Depends(get_optional_user)):
    """Saves a research brief to the permanent vault."""
    user_id = user["id"]
    success = await research_brief_service.toggle_save_brief(brief_id, user_id, save_state=True)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found.")
    await audit_logger.log_event(
        event_type="RESEARCH_BRIEF_SAVED",
        action="research.brief_save",
        user_id=user_id,
        resource_id=brief_id,
        details={"saved": True}
    )
    return {"success": True, "brief_id": brief_id, "saved": True}

@router.delete("/briefs/{brief_id}/save")
@router.delete("/brief/{brief_id}/save")
async def unsave_brief(brief_id: str, user: dict = Depends(get_optional_user)):
    """Removes a research brief from saved vault."""
    user_id = user["id"]
    success = await research_brief_service.toggle_save_brief(brief_id, user_id, save_state=False)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found.")
    return {"success": True, "brief_id": brief_id, "saved": False}

# Dedicated semantic action routes
@router.post("/briefs/{brief_id}/more-detail", response_model=ResearchBriefOut)
@router.post("/brief/{brief_id}/more-detail", response_model=ResearchBriefOut)
async def action_more_detail(brief_id: str, user: dict = Depends(get_optional_user)):
    """Expands answer to 20-35 lines using existing source context."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(user_id=user_id, brief_id=brief_id, action="more_detail")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/briefs/{brief_id}/simplify", response_model=ResearchBriefOut)
@router.post("/brief/{brief_id}/simplify", response_model=ResearchBriefOut)
async def action_simplify(brief_id: str, user: dict = Depends(get_optional_user)):
    """Converts answer to a quick 3-6 line summary."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(user_id=user_id, brief_id=brief_id, action="simplify")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/briefs/{brief_id}/examples", response_model=ResearchBriefOut)
@router.post("/brief/{brief_id}/examples", response_model=ResearchBriefOut)
async def action_examples(brief_id: str, user: dict = Depends(get_optional_user)):
    """Generates concrete real-world examples preserving citations."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(user_id=user_id, brief_id=brief_id, action="give_examples")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/briefs/{brief_id}/compare", response_model=ResearchBriefOut)
@router.post("/brief/{brief_id}/compare", response_model=ResearchBriefOut)
async def action_compare(brief_id: str, user: dict = Depends(get_optional_user)):
    """Compares key alternatives or competing approaches related to topic."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(user_id=user_id, brief_id=brief_id, action="compare_alternatives")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/briefs/{brief_id}/follow-up", response_model=ResearchBriefOut)
@router.post("/brief/{brief_id}/follow-up", response_model=ResearchBriefOut)
async def action_follow_up(brief_id: str, req: ResearchBriefActionRequest, user: dict = Depends(get_optional_user)):
    """Answers a specific follow-up question reusing retrieved evidence."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(
            user_id=user_id, brief_id=brief_id, action="follow_up", follow_up_query=req.follow_up_query
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/brief/{brief_id}/action", response_model=ResearchBriefOut)
@router.post("/briefs/{brief_id}/action", response_model=ResearchBriefOut)
async def execute_brief_action(brief_id: str, req: ResearchBriefActionRequest, user: dict = Depends(get_optional_user)):
    """Flexible follow-up control endpoint supporting all action types."""
    user_id = user["id"]
    try:
        return await research_brief_service.execute_action(
            user_id=user_id,
            brief_id=brief_id,
            action=req.action,
            follow_up_query=req.follow_up_query
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up action execution failed: {str(e)}"
        )

@router.get("/briefs/{brief_id}/export", response_model=ResearchBriefExportOut)
@router.get("/brief/{brief_id}/export", response_model=ResearchBriefExportOut)
async def export_brief(brief_id: str, user: dict = Depends(get_optional_user)):
    """Exports a formatted research brief as markdown for sharing."""
    user_id = user["id"]
    data = await research_brief_service.export_brief_markdown(brief_id, user_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found.")
    return ResearchBriefExportOut(
        brief_id=data["brief_id"],
        format=data["format"],
        content=data["content"],
        title=data["title"]
    )

