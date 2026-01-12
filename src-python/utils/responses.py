"""Response formatting utilities."""

from src.tools.schemas import ChatResponse, Source


def format_error_response(error_message: str) -> ChatResponse:
    """Create an error response."""
    return ChatResponse(
        reply=f"I apologize, but I encountered an error: {error_message}. Please try again.",
        sources=[],
    )


def format_no_results_response(query: str) -> ChatResponse:
    """Create a response when no relevant documents are found."""
    return ChatResponse(
        reply=(
            f"I couldn't find relevant information for your query: '{query}'. "
            "Please try rephrasing your question or ask about TFSA, RRSP, or Fund Facts topics."
        ),
        sources=[],
    )
