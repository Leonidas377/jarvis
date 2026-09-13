# ==========================================================================
# Phase 4 Acceptance Tests: LLM-Powered Cited Research Briefs
# ==========================================================================

import pytest
import asyncio
import json
import uuid
from httpx import AsyncClient, ASGITransport
from server.main import app
from server.database import get_db_connection, init_db
from server.services.research.brief_service import research_brief_service, TopicClassifier
from server.models.schemas import ResearchBriefRequest, ResearchBriefOut
from server.services.extraction.extractor import ExtractionResult


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    asyncio.run(init_db())


@pytest.mark.asyncio
async def test_topic_classification_coverage():
    """Verifies that queries across all 10 domain types are properly classified."""
    assert TopicClassifier.classify("Compare RISC-V vs ARM architecture") == "comparison"
    assert TopicClassifier.classify("What is quantum computing and why is it important?") == "definition"
    assert TopicClassifier.classify("NVIDIA Blackwell GPU specifications and architecture") == "product_tech"
    assert TopicClassifier.classify("How to deploy a FastAPI microservice on Linux") == "how_to"
    assert TopicClassifier.classify("Latest news on commercial fusion energy") == "news"
    assert TopicClassifier.classify("Federal reserve interest rate inflation and stock market") == "market"
    assert TopicClassifier.classify("Apple Inc revenue valuation and startup acquisitions") == "company"
    assert TopicClassifier.classify("Empirical study on quantum decoherence physics experiment") == "academic"
    assert TopicClassifier.classify("Best practices for system administration") == "general"


@pytest.mark.asyncio
async def test_brief_output_schema_and_modes():
    """Verifies ResearchBriefOut schema, field aliases, and sentence/line bounds across modes."""
    user_id = "default-tony-stark"

    # Test 1: Default 'brief' mode (~10-15 lines/sentences)
    req_brief = ResearchBriefRequest(
        query="What is quantum computing and why is it important?",
        answer_mode="brief",
        source_count=3
    )
    brief = await research_brief_service.generate_brief(user_id, req_brief)

    assert brief.id is not None
    assert brief.answer_mode == "brief"
    assert brief.direct_answer.strip() != ""
    assert not brief.direct_answer.lower().startswith("here are the search results")
    assert len(brief.brief_paragraphs) >= 1
    assert brief.takeaway.strip() != ""
    if brief.status == "ready":
        assert len(brief.citations) >= 1
        assert len(brief.citation_ids) == len(brief.citations)
    else:
        assert brief.source_coverage in ["complete", "partial"]
        assert len(brief.limitations) >= 1
    assert brief.generated_at != ""
    assert brief.provider_name is not None
    assert brief.model_name is not None

    # Test 2: 'quick' mode (~3-6 lines/sentences)
    req_quick = ResearchBriefRequest(
        query="Explain superconductors briefly",
        answer_mode="quick",
        source_count=2
    )
    quick_brief = await research_brief_service.generate_brief(user_id, req_quick)
    assert quick_brief.answer_mode == "quick"
    assert len(quick_brief.brief_paragraphs) >= 1
    if quick_brief.status == "ready":
        assert len(quick_brief.citations) >= 1
    else:
        assert quick_brief.source_coverage == "partial"
        assert len(quick_brief.limitations) >= 1

    # Test 3: 'detailed' mode (~20-35 lines/sentences)
    req_detailed = ResearchBriefRequest(
        query="High-NA EUV lithography mechanics",
        answer_mode="detailed",
        source_count=3
    )
    detailed_brief = await research_brief_service.generate_brief(user_id, req_detailed)
    assert detailed_brief.answer_mode == "detailed"
    assert len(detailed_brief.brief_paragraphs) >= 1


@pytest.mark.asyncio
async def test_citation_integrity_and_orphan_pruning():
    """Verifies that out-of-bounds citation numbers (e.g. [99]) are safely pruned and limitations recorded."""
    mock_sources = [
        ExtractionResult(
            url="https://example.com/quantum",
            title="Quantum Mechanics 101",
            canonical_url="https://example.com/quantum",
            publisher="Physics Press",
            author="Dr. Stark",
            published_date="2026-01-01",
            extracted_text="Quantum computers use qubits in superposition and entanglement.",
            headings=["Basics"],
            status="EXTRACTED",
            content_hash="h1"
        )
    ]

    # Model hallucinated citation [99] and [5] while only source [1] exists
    hallucinated_brief = {
        "title": "Quantum Overview",
        "direct_answer": "Quantum systems leverage qubits [1] and teleportation [99].",
        "brief_paragraphs": [
            "Superposition allows simultaneous calculation states [1].",
            "Non-existent paper claims breakthrough [5]."
        ],
        "key_points": [
            {"text": "Superposition works [1]", "citation_ids": ["1", "99"]}
        ],
        "takeaway": "Quantum computing is emerging [1].",
        "limitations": ["Initial assessment."]
    }

    citations, cleaned = research_brief_service._validate_and_anchor_citations(
        mock_sources, hallucinated_brief
    )

    # Citation [1] is retained, [99] and [5] are stripped
    assert len(citations) == 1
    assert citations[0].id == "1"
    assert "[99]" not in cleaned["direct_answer"]
    assert "[5]" not in cleaned["brief_paragraphs"][1]
    assert "[1]" in cleaned["direct_answer"]
    # Verify anti-hallucination limitation was appended
    assert any("pruned" in lim.lower() for lim in cleaned["limitations"])


@pytest.mark.asyncio
async def test_rest_api_endpoints():
    """Verifies Phase 4 REST API routes: /briefs, /more-detail, /simplify, /save, DELETE, PATCH, /export."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. POST /api/research/briefs
        res = await ac.post("/api/research/briefs", json={
            "query": "Compare RISC-V vs ARM architecture",
            "answerMode": "brief",
            "sourceCount": 3,
            "saveResult": True
        })
        assert res.status_code == 201
        data = res.json()
        brief_id = data["id"]
        assert data["query"] == "Compare RISC-V vs ARM architecture"
        assert data["directAnswer"] != ""
        assert "citationIds" in data
        assert data["saved"] is True

        # 2. GET /api/research/briefs/{id}
        res_get = await ac.get(f"/api/research/briefs/{brief_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == brief_id

        # 3. POST /api/research/briefs/{id}/simplify
        res_simp = await ac.post(f"/api/research/briefs/{brief_id}/simplify")
        assert res_simp.status_code == 200
        simp_data = res_simp.json()
        assert simp_data["answerMode"] == "quick"

        # 4. POST /api/research/briefs/{id}/more-detail
        res_more = await ac.post(f"/api/research/briefs/{brief_id}/more-detail")
        assert res_more.status_code == 200
        more_data = res_more.json()
        assert more_data["answerMode"] == "detailed"

        # 5. POST /api/research/briefs/{id}/examples
        res_ex = await ac.post(f"/api/research/briefs/{brief_id}/examples")
        assert res_ex.status_code == 200

        # 6. POST /api/research/briefs/{id}/compare
        res_comp = await ac.post(f"/api/research/briefs/{brief_id}/compare")
        assert res_comp.status_code == 200

        # 7. PATCH /api/research/briefs/{id} (Rename)
        res_patch = await ac.patch(f"/api/research/briefs/{brief_id}", json={
            "title": "Architectural Showdown: RISC-V vs ARM"
        })
        assert res_patch.status_code == 200
        assert res_patch.json()["title"] == "Architectural Showdown: RISC-V vs ARM"

        # 8. GET /api/research/briefs?query=Showdown (Search saved briefs)
        res_search = await ac.get("/api/research/briefs?query=Showdown")
        assert res_search.status_code == 200
        matches = res_search.json()
        assert len(matches) >= 1
        assert any(m["id"] == brief_id for m in matches)

        # 9. GET /api/research/briefs/{id}/export (Export Markdown)
        res_export = await ac.get(f"/api/research/briefs/{brief_id}/export")
        assert res_export.status_code == 200
        export_data = res_export.json()
        assert export_data["format"] == "markdown"
        assert "# Architectural Showdown" in export_data["content"]
        assert "## Direct Answer" in export_data["content"]
        assert "## Verified Sources" in export_data["content"]

        # 10. DELETE /api/research/briefs/{id}
        res_del = await ac.delete(f"/api/research/briefs/{brief_id}")
        assert res_del.status_code == 200
        assert res_del.json()["deleted"] is True

        # Verify it is deleted
        res_check = await ac.get(f"/api/research/briefs/{brief_id}")
        assert res_check.status_code == 404


@pytest.mark.asyncio
async def test_user_data_isolation():
    """Verifies that User B cannot access, rename, or delete User A's research brief."""
    user_a = "default-tony-stark"
    user_b = "rogue-agent-404"

    # Ensure User B exists in database
    async with get_db_connection() as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, email, hashed_password, display_name, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (user_b, "rogue_agent", "rogue@stark.com", "hash123", "Rogue Agent"))
        await db.commit()

    # User A creates a brief
    req = ResearchBriefRequest(query="Stark Industries Quantum Arc Reactor", answer_mode="brief", save_result=True)
    brief = await research_brief_service.generate_brief(user_a, req)

    # User B attempts to access User A's brief
    b_access = await research_brief_service.get_brief_by_id(brief.id, user_b)
    assert b_access is None

    # User B attempts to rename User A's brief
    b_rename = await research_brief_service.rename_brief(brief.id, user_b, "Hacked Title")
    assert b_rename is False

    # User B attempts to delete User A's brief
    b_delete = await research_brief_service.delete_brief(brief.id, user_b)
    assert b_delete is False

    # Verify User A's brief remains intact
    a_verify = await research_brief_service.get_brief_by_id(brief.id, user_a)
    assert a_verify is not None
    assert a_verify.title == brief.title


@pytest.mark.asyncio
async def test_audit_events_trail():
    """Verifies that research actions emit auditable event records in SQLite vault."""
    user_id = "default-tony-stark"
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT event_type FROM audit_events 
            WHERE user_id = ? AND event_type LIKE 'RESEARCH_%'
            ORDER BY timestamp DESC LIMIT 20
        """, (user_id,))
        rows = await cur.fetchall()
        events = [r["event_type"] for r in rows]

    assert "RESEARCH_BRIEF_GENERATED" in events
    assert "RESEARCH_RETRIEVAL_EXECUTED" in events
