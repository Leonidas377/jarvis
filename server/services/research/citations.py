# ==========================================================================
# JARVIS Structured Citation Engine
# Manages first-class citations, evidence excerpts, and anti-hallucination validation
# ==========================================================================

import re
from typing import List, Dict, Tuple, Optional
from server.models.schemas import CitationItem
from server.services.extraction.extractor import ExtractionResult

class CitationManager:
    @staticmethod
    def build_citations(sources: List[ExtractionResult]) -> List[CitationItem]:
        """Creates structured citation items from successfully retrieved source documents."""
        citations = []
        for i, src in enumerate(sources, 1):
            cit_id = f"CIT-{i:02d}"
            # Extract first substantive sentence as initial evidence excerpt
            paragraphs = src.extracted_text.split("\n\n")
            excerpt = paragraphs[0][:200] if paragraphs and paragraphs[0] else "Verified document retrieval."

            citations.append(CitationItem(
                id=cit_id,
                source_id=src.content_hash[:16],
                title=src.title,
                publisher=src.publisher,
                url=src.canonical_url or src.url,
                published_date=src.published_date,
                excerpt=excerpt,
                source_type="academic" if any(d in src.url for d in [".edu", "arxiv.org", "nature.com"]) else "web"
            ))
        return citations

    @staticmethod
    def validate_citations_in_report(
        key_facts: List[str],
        analysis: str,
        citations: List[CitationItem]
    ) -> Tuple[List[str], str, List[CitationItem]]:
        """
        Validates that every citation reference in facts/analysis exists in the citation list.
        Strips or marks orphaned references to ensure zero citation hallucination.
        """
        valid_ids = {c.id for c in citations}
        used_ids = set()

        def clean_text_citations(text: str) -> str:
            # Pattern matches [CIT-01], [CIT-02], etc.
            def replace_marker(match):
                cid = match.group(0)[1:-1]
                if cid in valid_ids:
                    used_ids.add(cid)
                    return match.group(0)
                # Remove hallucinated citation ID
                return ""

            return re.sub(r"\[CIT-\d{2}\]", replace_marker, text)

        cleaned_facts = [clean_text_citations(fact) for fact in key_facts]
        cleaned_analysis = clean_text_citations(analysis) if analysis else ""

        # Only retain citations that are verified and attached
        active_citations = [c for c in citations if c.id in used_ids or len(citations) <= 3]
        return cleaned_facts, cleaned_analysis, active_citations

citation_manager = CitationManager()
