"""Tests for the specialist tools."""

import pytest
from unittest.mock import MagicMock, patch

from src.tools.schemas import Source, ToolResponse, ResponseMetadata
from src.tools.local_search import SearchResult


class TestToolResponse:
    """Tests for ToolResponse schema."""

    def test_basic_response(self):
        response = ToolResponse(
            reply="Test response",
            sources=[],
        )
        assert response.reply == "Test response"
        assert response.chart_type is None
        assert response.image_base64 is None

    def test_response_with_chart(self):
        response = ToolResponse(
            reply="Here's the comparison",
            chart_type="bar",
            image_base64="data:image/png;base64,abc123",
            sources=[
                Source(pdf_name="Fund A Facts", pdf_url="https://example.com/fund-a.pdf")
            ],
        )
        assert response.chart_type == "bar"
        assert response.image_base64.startswith("data:image/png;base64,")
        assert len(response.sources) == 1

    def test_response_with_metadata(self):
        metadata = ResponseMetadata(
            search_results_count=5,
            data_store_empty=False,
            used_internal_knowledge=False,
            filter_applied="index:fund_facts",
        )
        response = ToolResponse(
            reply="Test",
            sources=[],
            metadata=metadata,
        )
        assert response.metadata.search_results_count == 5
        assert not response.metadata.data_store_empty


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        result = SearchResult(
            content="This is the content",
            pdf_name="Fund A Facts",
            pdf_url="https://example.com/fund-a.pdf",
            page=5,
            relevance_score=0.95,
        )
        assert result.content == "This is the content"
        assert result.page == 5
        assert result.relevance_score == 0.95

    def test_search_result_defaults(self):
        result = SearchResult(
            content="Content",
            pdf_name="Test",
            pdf_url="https://example.com/test.pdf",
        )
        assert result.page is None
        assert result.relevance_score == 0.0


class TestTFSATool:
    """Tests for TFSA tool."""

    def test_tfsa_tool_properties(self):
        from src.tools.tfsa_tool import TFSATool

        tool = TFSATool()
        assert tool.name == "tfsa"
        assert "TFSA" in tool.system_prompt

    def test_tfsa_tool_system_prompt_content(self):
        from src.tools.tfsa_tool import TFSATool

        tool = TFSATool()
        assert "contribution" in tool.system_prompt.lower()
        assert "withdrawal" in tool.system_prompt.lower()


class TestRRSPTool:
    """Tests for RRSP tool."""

    def test_rrsp_tool_properties(self):
        from src.tools.rrsp_tool import RRSPTool

        tool = RRSPTool()
        assert tool.name == "rrsp"
        assert "RRSP" in tool.system_prompt

    def test_rrsp_tool_system_prompt_content(self):
        from src.tools.rrsp_tool import RRSPTool

        tool = RRSPTool()
        assert "home buyers" in tool.system_prompt.lower()
        assert "rrif" in tool.system_prompt.lower()


class TestFundFactsTool:
    """Tests for Fund Facts tool."""

    def test_fund_facts_tool_properties(self):
        from src.tools.fund_facts_tool import FundFactsTool

        tool = FundFactsTool()
        assert tool.name == "fund_facts"
        assert "MER" in tool.system_prompt or "mutual fund" in tool.system_prompt.lower()

    def test_fund_facts_tool_system_prompt_content(self):
        from src.tools.fund_facts_tool import FundFactsTool

        tool = FundFactsTool()
        assert "performance" in tool.system_prompt.lower()
        assert "risk" in tool.system_prompt.lower()


class TestLocalSearchClient:
    """Tests for LocalSearchClient."""

    def test_build_context_empty(self):
        from src.tools.local_search import LocalSearchClient

        # We can test build_context without loading an index
        result = LocalSearchClient.build_context(None, [])
        assert result == "No relevant documents found."

    def test_build_context_with_results(self):
        from src.tools.local_search import LocalSearchClient

        results = [
            SearchResult(
                content="First document content",
                pdf_name="Doc 1",
                pdf_url="https://example.com/doc1.pdf",
                page=1,
            ),
            SearchResult(
                content="Second document content",
                pdf_name="Doc 2",
                pdf_url="https://example.com/doc2.pdf",
                page=5,
            ),
        ]

        # Call as instance method with None self (static-like behavior)
        context = LocalSearchClient.build_context(None, results)
        assert "[Source 1: Doc 1, Page 1]" in context
        assert "[Source 2: Doc 2, Page 5]" in context
        assert "First document content" in context
        assert "Second document content" in context
