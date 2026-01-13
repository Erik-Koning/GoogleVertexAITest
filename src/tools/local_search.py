"""Local FAISS-based vector search client for document retrieval."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config import get_settings


@dataclass
class SearchResult:
    """A single search result from local vector search."""

    content: str
    pdf_name: str
    pdf_url: str
    page: Optional[int] = None
    relevance_score: float = 0.0


# Cache for loaded FAISS indexes by path
_vectorstore_cache: dict[str, FAISS] = {}


def get_embeddings():
    """Get embeddings model for FAISS."""
    settings = get_settings()
    if settings.is_dev():
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key,
        )
    else:
        from langchain_google_vertexai import VertexAIEmbeddings
        return VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )


class LocalSearchClient:
    """Client for querying local FAISS vector store."""

    def __init__(self, index_path: str):
        """
        Initialize search client for a specific FAISS index.

        Args:
            index_path: Path to the FAISS index directory
        """
        self.index_path = index_path
        self._load_index()

    def _load_index(self) -> None:
        """Load the FAISS index from disk (with caching)."""
        global _vectorstore_cache

        if self.index_path in _vectorstore_cache:
            self._vectorstore = _vectorstore_cache[self.index_path]
            return

        path = Path(self.index_path)

        if not path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at: {path}\n"
                "Please ensure the index exists at the configured path."
            )

        # Load FAISS index with embeddings for similarity search
        embeddings = get_embeddings()
        self._vectorstore = FAISS.load_local(
            str(path),
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
        _vectorstore_cache[self.index_path] = self._vectorstore
        print(f"Loaded FAISS index from: {path}")

    @property
    def vectorstore(self) -> FAISS:
        """Get the loaded vectorstore."""
        return self._vectorstore

    def search(
        self,
        query: str,
        page_size: int = 5,
    ) -> list[SearchResult]:
        """
        Search for documents matching the query.

        Args:
            query: The search query
            page_size: Number of results to return

        Returns:
            List of SearchResult objects
        """
        settings = get_settings()

        # Search with similarity scores
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query,
            k=page_size,
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
