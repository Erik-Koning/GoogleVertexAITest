"""Base tool class with local FAISS RAG pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from src.config import get_settings
from src.tools.schemas import ResponseMetadata, Source, ToolResponse
from src.tools.local_search import LocalSearchClient, SearchResult
from src.utils.gemini import generate_content


class BaseTool(ABC):
    """
    Base class for all RAG tools.
    Provides common local FAISS search + Gemini RAG functionality.
    Each tool has its own FAISS index for domain-specific search.
    """

    # Override in subclasses
    system_prompt: str = ""
    _search_client: Optional[LocalSearchClient] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for identification and index lookup."""
        pass

    @property
    def search_client(self) -> LocalSearchClient:
        """Lazy-load the search client for this tool's index."""
        if self._search_client is None:
            settings = get_settings()
            index_path = settings.get_faiss_index_path(self.name)
            self._search_client = LocalSearchClient(index_path)
        return self._search_client

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
        settings = get_settings()

        # Track metadata for response
        metadata = ResponseMetadata(
            filter_applied=f"index:{self.name}",
        )

        # 1. Query this tool's FAISS index
        try:
            search_results = self.search_client.search(query=user_query)
        except FileNotFoundError as e:
            # Index doesn't exist yet
            print(f"Warning: FAISS index not found for {self.name}: {e}")
            search_results = []
            metadata.warning = f"Index not found for {self.name}"
        except Exception as e:
            print(f"Warning: Search failed for {self.name}: {e}")
            search_results = []
            metadata.warning = f"Search failed: {str(e)[:100]}"

        # Update metadata with search results info
        metadata.search_results_count = len(search_results)
        metadata.data_store_empty = len(search_results) == 0

        # 2. Build context from search results
        context = self.search_client.build_context(search_results) if search_results else ""
        sources = self._extract_sources(search_results)

        # 3. Generate response with Gemini (RAG or fallback to internal knowledge)
        use_internal_knowledge = (
            metadata.data_store_empty and settings.allow_general_knowledge_fallback
        )
        metadata.used_internal_knowledge = use_internal_knowledge

        if metadata.data_store_empty and not settings.allow_general_knowledge_fallback:
            # No docs and fallback disabled - return message without calling Gemini
            reply = (
                "No relevant documents were found in the knowledge base to answer your question. "
                "Please ensure documents have been uploaded and indexed."
            )
        else:
            try:
                reply = self._generate_response(
                    user_query, context, use_internal_knowledge=use_internal_knowledge
                )
            except Exception as e:
                error_str = str(e).lower()
                if "overloaded" in error_str or "503" in error_str:
                    reply = "The AI model is currently overloaded. Please try again in a few moments."
                    metadata.warning = "Gemini model overloaded"
                elif "quota" in error_str or "429" in error_str:
                    reply = "API rate limit reached. Please try again later."
                    metadata.warning = "API rate limit reached"
                else:
                    raise

        # 4. Optionally generate chart
        image_base64 = None
        if generate_chart:
            try:
                from src.charts.data_extractor import extract_chart_data
                from src.charts.generator import generate_chart as create_chart

                chart_data = extract_chart_data(user_query, context, chart_type)
                if chart_data:
                    image_base64 = create_chart(
                        data=chart_data["data"],
                        title=chart_data["title"],
                        chart_type=chart_type,
                    )
            except Exception as e:
                print(f"Warning: Chart generation failed: {e}")
                metadata.warning = f"Chart generation failed: {str(e)[:50]}"

        return ToolResponse(
            reply=reply,
            chart_type=chart_type if generate_chart and image_base64 else None,
            image_base64=image_base64,
            sources=sources,
            metadata=metadata,
        )

    def _generate_response(
        self, user_query: str, context: str, use_internal_knowledge: bool = False
    ) -> str:
        """Generate response using Gemini.

        Args:
            user_query: The user's question
            context: Retrieved document context (may be empty)
            use_internal_knowledge: If True, answer from Gemini's internal knowledge
        """
        if use_internal_knowledge:
            prompt = f"""Answer the user's question using your internal knowledge.
Note: No documents were found in the knowledge base, so provide a general answer based on your training.
Start your response with a brief note that this answer is from general knowledge, not from specific documents.

User Question: {user_query}

Answer:"""
        else:
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
