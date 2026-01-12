"""Vertex AI Search client for document retrieval."""

from dataclasses import dataclass
from typing import Optional

from google.cloud import discoveryengine_v1 as discoveryengine

from src.config import get_settings


@dataclass
class SearchResult:
    """A single search result from Vertex AI Search."""

    content: str
    pdf_name: str
    pdf_url: str
    page: Optional[int] = None
    relevance_score: float = 0.0


class VertexSearchClient:
    """Client for querying Vertex AI Search."""

    def __init__(self):
        settings = get_settings()
        self.client = discoveryengine.SearchServiceClient()
        self.serving_config = (
            f"projects/{settings.gcp_project_id}/locations/global"
            f"/collections/default_collection"
            f"/engines/{settings.vertex_search_engine_id}"
            f"/servingConfigs/default_search"
        )
        self.pdf_base_url = settings.pdf_base_url

    def search(
        self,
        query: str,
        filter_expr: Optional[str] = None,
        page_size: int = 5,
    ) -> list[SearchResult]:
        """
        Search for documents matching the query.

        Args:
            query: The search query
            filter_expr: Optional filter expression (e.g., "category:tfsa")
            page_size: Number of results to return

        Returns:
            List of SearchResult objects
        """
        request = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=page_size,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                    max_extractive_answer_count=3,
                    max_extractive_segment_count=3,
                ),
            ),
        )

        if filter_expr:
            request.filter = filter_expr

        response = self.client.search(request)
        results = []

        for result in response.results:
            doc = result.document
            doc_data = dict(doc.derived_struct_data) if doc.derived_struct_data else {}

            # Extract metadata
            pdf_name = doc_data.get("title", doc_data.get("display_name", "Unknown"))
            source_url = doc_data.get("source_url", "")
            if not source_url and self.pdf_base_url:
                # Construct URL from base URL and filename
                filename = doc_data.get("filename", "")
                if filename:
                    source_url = f"{self.pdf_base_url}/{filename}"

            # Extract content from extractive answers/segments
            content_parts = []
            extractive_answers = doc_data.get("extractive_answers", [])
            for answer in extractive_answers:
                if isinstance(answer, dict) and "content" in answer:
                    content_parts.append(answer["content"])

            extractive_segments = doc_data.get("extractive_segments", [])
            for segment in extractive_segments:
                if isinstance(segment, dict) and "content" in segment:
                    content_parts.append(segment["content"])

            content = "\n".join(content_parts) if content_parts else ""

            # Extract page number if available
            page = None
            if extractive_answers and isinstance(extractive_answers[0], dict):
                page = extractive_answers[0].get("pageNumber")

            results.append(
                SearchResult(
                    content=content,
                    pdf_name=pdf_name,
                    pdf_url=source_url,
                    page=page,
                    relevance_score=getattr(result, "relevance_score", 0.0),
                )
            )

        return results

    def build_context(self, results: list[SearchResult]) -> str:
        """Build context string from search results for RAG."""
        if not results:
            return "No relevant documents found."

        context_parts = []
        for i, result in enumerate(results, 1):
            source_info = f"[Source {i}: {result.pdf_name}"
            if result.page:
                source_info += f", Page {result.page}"
            source_info += "]"

            context_parts.append(f"{source_info}\n{result.content}")

        return "\n\n".join(context_parts)
