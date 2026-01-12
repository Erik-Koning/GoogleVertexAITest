"""Pydantic schemas for tool inputs and outputs."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source document reference from Vertex AI Search."""

    pdf_name: str = Field(description="Display name of the source PDF")
    pdf_url: str = Field(description="URL to the source PDF")
    page: Optional[int] = Field(default=None, description="Page number in the PDF")
    snippet: Optional[str] = Field(default=None, description="Relevant text snippet")


class ToolInput(BaseModel):
    """Input schema for all tools."""

    user_query: str = Field(description="The user's question")
    generate_chart: bool = Field(default=False, description="Whether to generate a chart")
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram"] = Field(
        default="bar", description="Type of chart to generate"
    )


class ResponseMetadata(BaseModel):
    """Metadata about the response for debugging/transparency."""

    search_results_count: int = Field(default=0, description="Number of search results found")
    data_store_empty: bool = Field(default=False, description="Whether the data store returned no results")
    used_internal_knowledge: bool = Field(default=False, description="Whether Gemini used internal knowledge instead of documents")
    filter_applied: Optional[str] = Field(default=None, description="Search filter that was applied")
    filter_fallback: bool = Field(default=False, description="Whether filter failed and fell back to no filter")
    warning: Optional[str] = Field(default=None, description="Any warnings during processing")


class ToolResponse(BaseModel):
    """Unified response schema for all tools."""

    reply: str = Field(description="The text response to the user")
    chart_type: Optional[str] = Field(default=None, description="Chart type if generated")
    image_base64: Optional[str] = Field(
        default=None, description="Base64-encoded PNG image"
    )
    sources: list[Source] = Field(default_factory=list, description="Source documents")
    metadata: Optional[ResponseMetadata] = Field(default=None, description="Response metadata")


class ChatRequest(BaseModel):
    """Request schema for /chat endpoint."""

    message: str = Field(description="The user's message")


class ChatResponse(BaseModel):
    """Response schema for /chat endpoint."""

    reply: str
    chart_type: Optional[str] = None
    image_base64: Optional[str] = None
    sources: list[Source] = []
    metadata: Optional[ResponseMetadata] = None


class OrchestratorDecision(BaseModel):
    """Output schema for the orchestrator routing decision."""

    tool: Literal["tfsa", "rrsp", "fund_facts"] = Field(
        description="Which tool to route the query to"
    )
    user_query: str = Field(description="The user query to forward to the tool")
    generate_chart: bool = Field(
        default=False, description="Whether to generate a chart"
    )
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram"] = Field(
        default="bar", description="Type of chart to generate"
    )
    reasoning: str = Field(description="Explanation for the routing decision")
