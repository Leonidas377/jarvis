# ==========================================================================
# JARVIS Research Brief Automated Test Suite
# Tests 10-15 line briefs, modes (quick/brief/detailed), anti-hallucination
# citations, follow-up actions, context reuse, and failure states
# ==========================================================================

import pytest
import pytest_asyncio
import re
from httpx import AsyncClient, ASGITransport

from server.main import app
from server.database import init_db
from server.models.schemas import ResearchBriefRequest, ResearchBriefOut
from server.services.research.brief_service import research_brief_service, TopicClassifier
from server.services.extraction.extractor import ExtractionResult
from server.tools.registry import default_registry


@pytest_asyncio.fixture(autouse=True)
async def ensure_db():
    await init_db()


@pytest.fixture
def mock_extracted_sources():
    """Provides authentic, non-fabricated mock extraction results."""
    return [
        ExtractionResult(
            url="https://quantum.mit.edu/overview",
            title="Fundamentals of Superconducting Qubits",
            canonical_url="https://quantum.mit.edu/overview",
            publisher="MIT Quantum Engineering Center",
            author="Dr. W. Oliver",
            published_date="2025-01-15",
            extracted_text=(
                "Quantum computing utilizes quantum mechanical phenomena such as superposition and entanglement to solve computational problems beyond classical capability. "
                "Superconducting transmon circuits demonstrate coherence times exceeding hundreds of microseconds in controlled cryogenic environments. "
                "Current fault-tolerant roadmaps target physical-to-logical qubit ratios of approximately one thousand to one using surface codes. "
                "Key practical milestones focus on quantum error mitigation and algorithmic advantage in quantum chemistry simulations."
            ),
            headings=["Architectural Principles", "Error Mitigation"],
            status="EXTRACTED",
            content_hash="mit-quantum-001"
        ),
        ExtractionResult(
            url="https://nature.com/articles/s41586-quantum-advancement",
            title="Demonstration of Fault-Tolerant Logical Qubit Operations",
            canonical_url="https://nature.com/articles/s41586-quantum-advancement",
            publisher="Nature Publishing Group",
            author="Quantum Systems Consortium",
            published_date="2025-03-02",
            extracted_text=(
                "Empirical measurements verify two-qubit gate fidelities surpassing ninety-nine point nine percent across neutral atom arrays. "
                "Neutral atom platforms employ optical tweezers to dynamically reconfigure qubit interconnect topologies during active runtime. "
                "Commercial applicability remains constrained by laser phase stability and thermal dissipation limits inside dilution refrigeration units. "
                "Industry roadmaps project hybrid quantum-classical computing workflows entering pharmaceutical molecular modeling by late decade."
            ),
            headings=["Experimental Benchmark", "Physical Constraints"],
            status="EXTRACTED",
            content_hash="nature-quantum-002"
        ),
        ExtractionResult(
            url="https://nist.gov/programs/quantum-standards",
            title="NIST Post-Quantum Cryptography & Hardware Guidelines",
            canonical_url="https://nist.gov/programs/quantum-standards",
            publisher="National Institute of Standards and Technology",
            author="NIST Working Group",
            published_date="2024-11-20",
            extracted_text=(
                "Standardization protocols emphasize lattice-based cryptography transitions before cryptographically relevant quantum computers reach operational scale. "
                "Shor's algorithm requires millions of noisy physical qubits to factor standard RSA-2048 public keys, which is not feasible with current hardware. "
                "Government guidelines mandate dual-certificate authentication for federal critical infrastructure starting in fiscal year 2026."
            ),
            headings=["Cryptographic Security", "Timeline Expectations"],
            status="EXTRACTED",
            content_hash="nist-quantum-003"
        )
    ]


# --- 1. Topic Classifier Tests ---
def test_topic_classifier_heuristic():
    assert TopicClassifier.classify("What is quantum computing?") == "definition"
    assert TopicClassifier.classify("Tell me about Apple Inc revenue and leadership") == "company"
    assert TopicClassifier.classify("Compare NVIDIA Blackwell vs Hopper architecture") == "comparison"
    assert TopicClassifier.classify("How to deploy a FastAPI service with Docker") == "how_to"
    assert TopicClassifier.classify("Latest news about space exploration today") == "news"
    assert TopicClassifier.classify("Tesla stock price and market volatility") == "market"
    assert TopicClassifier.classify("General knowledge inquiry") == "general"


# --- 2. Output Length & Mode Tests ---
@pytest.mark.asyncio
async def test_brief_mode_output_length_and_structure(mock_extracted_sources):
    """
    Default 'brief' mode must produce approximately 10-15 readable lines/sentences
    with a direct answer first, compact citations, and takeaway at the end.
    """
    raw = research_brief_service._synthesize_deterministic(
        query="What is quantum computing and why is it important?",
        sources=mock_extracted_sources,
        mode="brief",
        topic="definition"
    )
    citations, brief = research_brief_service._validate_and_anchor_citations(
        sources=mock_extracted_sources,
        raw_brief=raw
    )

    # 1. Direct answer must appear first in 1-2 sentences
    assert brief["direct_answer"]
    assert len(brief["direct_answer"]) > 40
    # Must not start with generic phrase
    assert not brief["direct_answer"].lower().startswith("here are the search results")
    assert not brief["direct_answer"].lower().startswith("based on the search")

    # 2. Brief body lines/sentences count should be approximately 10-15
    all_body_text = " ".join(brief["brief_paragraphs"])
    body_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', all_body_text) if len(s.strip()) > 15]
    total_lines = len(body_sentences)
    assert 8 <= total_lines <= 18, f"Expected 8-18 sentences (~10-15 lines), got {total_lines}"

    # 3. Concluding takeaway must be present
    assert brief["takeaway"]
    assert len(brief["takeaway"]) > 20

    # 4. Sources list must be compact (2 to 5 sources)
    assert 2 <= len(citations) <= 5


@pytest.mark.asyncio
async def test_quick_mode_output_length(mock_extracted_sources):
    """'quick' mode must produce a short summary of ~3-6 sentences."""
    raw = research_brief_service._synthesize_deterministic(
        query="Explain quantum computing briefly",
        sources=mock_extracted_sources,
        mode="quick",
        topic="definition"
    )
    citations, brief = research_brief_service._validate_and_anchor_citations(
        sources=mock_extracted_sources,
        raw_brief=raw
    )

    all_body_text = " ".join(brief["brief_paragraphs"])
    body_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', all_body_text) if len(s.strip()) > 15]
    assert len(body_sentences) <= 8, f"Expected short summary, got {len(body_sentences)} sentences"


@pytest.mark.asyncio
async def test_detailed_mode_output_length(mock_extracted_sources):
    """'detailed' mode must expand to ~20-35 sentences without generating an unbounded report."""
    raw = research_brief_service._synthesize_deterministic(
        query="Provide deep technical breakdown of quantum computing",
        sources=mock_extracted_sources,
        mode="detailed",
        topic="product_tech"
    )
    citations, brief = research_brief_service._validate_and_anchor_citations(
        sources=mock_extracted_sources,
        raw_brief=raw
    )

    all_body_text = " ".join(brief["brief_paragraphs"])
    body_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', all_body_text) if len(s.strip()) > 15]
    assert len(body_sentences) >= 10, f"Expected expanded brief, got {len(body_sentences)} sentences"


# --- 3. Citation Integrity & Anti-Hallucination Tests ---
@pytest.mark.asyncio
async def test_citation_integrity_and_anti_hallucination(mock_extracted_sources):
    """
    Every citation ID referenced in the text must exist in the validated citation list.
    No fabricated or out-of-bounds citation markers can survive validation.
    """
    raw_with_hallucinated = {
        "title": "Quantum Computing Test",
        "direct_answer": "Quantum computing harnesses superposition [1] and non-existent source [99].",
        "brief_paragraphs": [
            "MIT researchers demonstrated transmon coherence [1] while another group published findings [2].",
            "A fictional claim cited a fabricated marker [42] and a valid standard [3]."
        ],
        "takeaway": "Advancement requires physical scaling [2].",
        "limitations": ["Experimental data bounded by access timestamp."]
    }

    citations, cleaned_brief = research_brief_service._validate_and_anchor_citations(
        sources=mock_extracted_sources,
        raw_brief=raw_with_hallucinated
    )

    # Fabricated marker [99] and [42] must be stripped
    assert "[99]" not in cleaned_brief["direct_answer"]
    assert "[42]" not in cleaned_brief["brief_paragraphs"][1]

    # Valid markers [1], [2], [3] must be preserved
    assert "[1]" in cleaned_brief["direct_answer"]
    assert "[1]" in cleaned_brief["brief_paragraphs"][0]
    assert "[2]" in cleaned_brief["brief_paragraphs"][0]
    assert "[3]" in cleaned_brief["brief_paragraphs"][1]

    # Every citation item in output must match a retrieved URL
    valid_urls = {s.url for s in mock_extracted_sources}
    for c in citations:
        assert c.url in valid_urls
        assert c.id in ["1", "2", "3"]


# --- 4. Follow-Up Behavior & Context Reuse Tests ---
@pytest.mark.asyncio
async def test_follow_up_action_more_detail_and_context_reuse(mock_extracted_sources, monkeypatch):
    """
    Executing 'more_detail' on an existing brief reuses the parent brief context
    and expands the answer without making unrelated fresh searches.
    """
    user_id = "default-tony-stark"
    init_req = ResearchBriefRequest(
        query="Quantum Computing Architecture",
        answer_mode="brief",
        topic_type="product_tech"
    )

    from server.models.schemas import SearchResultItem
    class MockProvider:
        async def search(self, *args, **kwargs):
            return [
                SearchResultItem(
                    id=f"res-{i}",
                    title=s.title,
                    url=s.url,
                    snippet=s.extracted_text[:200],
                    domain="example.com",
                    provider="mock",
                    retrieval_timestamp="2026-09-10 10:00:00"
                ) for i, s in enumerate(mock_extracted_sources)
            ]

    monkeypatch.setattr("server.services.research.brief_service.get_search_provider", lambda: MockProvider())
    async def mock_fetch_html(url, *args, **kwargs):
        return ("<html>content</html>", url, 200)
    monkeypatch.setattr("server.services.research.brief_service.safe_fetch_html", mock_fetch_html)
    monkeypatch.setattr("server.services.research.brief_service.extractor.extract", lambda html, url: mock_extracted_sources[0])

    # 1. Generate initial brief
    initial_brief = await research_brief_service.generate_brief(user_id=user_id, request=init_req)
    assert initial_brief.id
    assert initial_brief.answer_mode == "brief"

    # 2. Execute follow-up 'more_detail'
    detailed_brief = await research_brief_service.execute_action(
        user_id=user_id,
        brief_id=initial_brief.id,
        action="more_detail"
    )
    assert detailed_brief.answer_mode == "detailed"
    assert len(" ".join(detailed_brief.brief_paragraphs)) > 100

    # 3. Execute follow-up 'simplify'
    simple_brief = await research_brief_service.execute_action(
        user_id=user_id,
        brief_id=initial_brief.id,
        action="simplify"
    )
    assert simple_brief.answer_mode == "quick"
    assert len(" ".join(simple_brief.brief_paragraphs)) < len(" ".join(detailed_brief.brief_paragraphs))



# --- 5. Tool Registry & API Endpoint Tests ---
@pytest.mark.asyncio
async def test_generate_research_brief_tool_execution():
    """Confirms the generate_research_brief tool is registered, safe (R0), and executes cleanly."""
    tool = default_registry.get("generate_research_brief")
    assert tool is not None
    assert tool.risk_level == "R0_SAFE"
    assert tool.requires_confirmation is False

    context = {"user": {"id": "default-tony-stark"}, "conversation_id": "test-conv-001"}
    params = {"query": "What is photonics in computing?", "answer_mode": "brief"}
    result = await tool.execute(tool.input_schema(**params), context)

    direct_ans = result.get("direct_answer") or result.get("directAnswer")
    brief_paras = result.get("brief_paragraphs") or result.get("briefParagraphs")
    assert direct_ans
    assert brief_paras
    assert len(brief_paras) >= 1


@pytest.mark.asyncio
async def test_research_brief_api_endpoints():
    """Tests POST /api/research/brief, GET /api/research/brief/{id}, and follow-up actions via HTTP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Research Brief
        create_res = await ac.post("/api/research/brief", json={
            "query": "EUV High-NA semiconductor lithography",
            "answer_mode": "brief"
        })
        assert create_res.status_code == 201
        data = create_res.json()
        brief_id = data["id"]
        direct_ans = data.get("directAnswer") or data.get("direct_answer")
        brief_paras = data.get("briefParagraphs") or data.get("brief_paragraphs")
        assert direct_ans
        assert len(brief_paras) >= 1
        assert "takeaway" in data

        # 2. Get Brief by ID
        get_res = await ac.get(f"/api/research/brief/{brief_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == brief_id

        # 3. Save Brief
        save_res = await ac.post(f"/api/research/brief/{brief_id}/save")
        assert save_res.status_code == 200
        assert save_res.json()["saved"] is True

        # 4. List Saved Briefs
        list_res = await ac.get("/api/research/briefs")
        assert list_res.status_code == 200
        saved_ids = [b["id"] for b in list_res.json()]
        assert brief_id in saved_ids

        # 5. Execute Action
        act_res = await ac.post(f"/api/research/brief/{brief_id}/action", json={
            "action": "simplify"
        })
        assert act_res.status_code == 200
        act_mode = act_res.json().get("answerMode") or act_res.json().get("answer_mode")
        assert act_mode == "quick"

