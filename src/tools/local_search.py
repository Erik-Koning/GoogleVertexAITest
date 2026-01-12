"""Local FAISS-based vector search client for document retrieval."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS

from src.config import get_settings


@dataclass
class SearchResult:
    """A single search result from local vector search."""

    content: str
    pdf_name: str
    pdf_url: str
    page: Optional[int] = None
    relevance_score: float = 0.0


class LocalSearchClient:
    """Client for querying local FAISS vector store."""

    _instance: Optional["LocalSearchClient"] = None
    _vectorstore: Optional[FAISS] = None

    def __new__(cls):
        """Singleton pattern to avoid reloading the index."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LocalSearchClient._vectorstore is None:
            self._load_index()

    def _load_index(self) -> None:
        """Load the FAISS index from disk."""
        settings = get_settings()
        index_path = Path(settings.faiss_index_path)

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at: {index_path}\n"
                "Please ensure the index exists at the configured FAISS_INDEX_PATH."
            )

        # Load FAISS index - embeddings are stored in the index
        # We use allow_dangerous_deserialization since we control the index creation
        LocalSearchClient._vectorstore = FAISS.load_local(
            str(index_path),
            embeddings=None,  # Not needed for search if stored in index
            allow_dangerous_deserialization=True,
        )
        print(f"Loaded FAISS index from: {index_path}")

    @property
    def vectorstore(self) -> FAISS:
        """Get the loaded vectorstore."""
        if LocalSearchClient._vectorstore is None:
            self._load_index()
        return LocalSearchClient._vectorstore

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
        settings = get_settings()

        # Build filter dict if filter_expr provided
        filter_dict = None
        if filter_expr:
            # Parse filter like "category:tfsa" into {"category": "tfsa"}
            if ":" in filter_expr:
                key, value = filter_expr.split(":", 1)
                filter_dict = {key.strip(): value.strip()}

        # Search with similarity scores
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query,
            k=page_size,
            filter=filter_dict,
        )

        results = []
        for doc, score in docs_with_scores:
            metadata = doc.metadata or {}

            # Extract metadata
            pdf_name = metadata.get("title", metadata.get("source", "Unknown"))
            source_url = metadata.get("source_url", "")

            # Construct URL from base URL if not present
            if not source_url and settings.pdf_base_url:
                filename = metadata.get("filename", "")
                if filename:
                    source_url = f"{settings.pdf_base_url}/{filename}"

            page = metadata.get("page")

            results.append(
                SearchResult(
                    content=doc.page_content,
                    pdf_name=pdf_name,
                    pdf_url=source_url,
                    page=page,
                    relevance_score=float(score),
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
