"""Base tool class with Vertex AI Search RAG pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from src.tools.schemas import Source, ToolResponse
from src.tools.vertex_search import SearchResult, VertexSearchClient
from src.utils.gemini import generate_content


class BaseTool(ABC):
    """
    Base class for all RAG tools.
    Provides common Vertex AI Search + Gemini RAG functionality.
    """

    # Override in subclasses for topic-specific search
    search_filter: str = ""
    system_prompt: str = ""

    def __init__(self):
        self.search_client = VertexSearchClient()

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for identification."""
        pass

    def invoke(
        self,
        user_query: str,
        generate_chart: bool = False,
        chart_type: str = "bar",
    ) -> ToolResponse:
        """
        Execute the tool with RAG pattern.

        Args:
            user_query: The user's question
            generate_chart: Whether to generate a chart
            chart_type: Type of chart to generate

        Returns:
            ToolResponse with reply, optional chart, and sources
        """
        # 1. Query Vertex AI Search with topic filter
        search_results = self.search_client.search(
            query=user_query,
            filter_expr=self.search_filter if self.search_filter else None,
        )

        # 2. Build context from search results
        context = self.search_client.build_context(search_results)
        sources = self._extract_sources(search_results)

        # 3. Generate response with Gemini (RAG)
        reply = self._generate_response(user_query, context)

        # 4. Optionally generate chart
        image_base64 = None
        if generate_chart:
            from src.charts.data_extractor import extract_chart_data
            from src.charts.generator import generate_chart as create_chart

            chart_data = extract_chart_data(user_query, context, chart_type)
            if chart_data:
                image_base64 = create_chart(
                    data=chart_data["data"],
                    title=chart_data["title"],
                    chart_type=chart_type,
                )

        return ToolResponse(
            reply=reply,
            chart_type=chart_type if generate_chart and image_base64 else None,
            image_base64=image_base64,
            sources=sources,
        )

    def _generate_response(self, user_query: str, context: str) -> str:
        """Generate RAG response using Gemini."""
        prompt = f"""Based on the following context from official documents, answer the user's question.
If the context doesn't contain enough information to answer the question, say so clearly.
Always cite which document(s) your answer is based on.

Context:
{context}

User Question: {user_query}

Answer:"""

        return generate_content(prompt, system_instruction=self.system_prompt)

    def _extract_sources(self, results: list[SearchResult]) -> list[Source]:
        """Extract source information from search results."""
        sources = []
        seen_urls = set()

        for result in results:
            if result.pdf_url and result.pdf_url not in seen_urls:
                seen_urls.add(result.pdf_url)
                sources.append(
                    Source(
                        pdf_name=result.pdf_name,
                        pdf_url=result.pdf_url,
                        page=result.page,
                        snippet=result.content[:200] if result.content else None,
                    )
                )

        return sources
