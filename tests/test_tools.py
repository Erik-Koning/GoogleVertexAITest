"""Tests for the specialist tools."""

import pytest
from unittest.mock import MagicMock, patch

from src.tools.schemas import Source, ToolResponse
from src.tools.vertex_search import SearchResult


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


class TestTFSATool:
    """Tests for TFSA tool."""

    def test_tfsa_tool_properties(self):
        from src.tools.tfsa_tool import TFSATool

        tool = TFSATool()
        assert tool.name == "tfsa"
        assert "tfsa" in tool.search_filter.lower()
        assert "TFSA" in tool.system_prompt


class TestRRSPTool:
    """Tests for RRSP tool."""

    def test_rrsp_tool_properties(self):
        from src.tools.rrsp_tool import RRSPTool

        tool = RRSPTool()
        assert tool.name == "rrsp"
        assert "rrsp" in tool.search_filter.lower()
        assert "RRSP" in tool.system_prompt


class TestFundFactsTool:
    """Tests for Fund Facts tool."""

    def test_fund_facts_tool_properties(self):
        from src.tools.fund_facts_tool import FundFactsTool

        tool = FundFactsTool()
        assert tool.name == "fund_facts"
        assert "fund_facts" in tool.search_filter.lower()
        assert "MER" in tool.system_prompt or "mutual fund" in tool.system_prompt.lower()
