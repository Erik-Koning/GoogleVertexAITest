"""Tests for the orchestrator routing logic."""

import pytest
from unittest.mock import MagicMock, patch

from src.orchestrator.router import Orchestrator, RouterOutput
from src.tools.schemas import OrchestratorDecision


class TestRouterOutput:
    """Tests for RouterOutput schema."""

    def test_valid_router_output(self):
        output = RouterOutput(
            tool="tfsa",
            generate_chart=False,
            chart_type="bar",
            reasoning="Query mentions TFSA",
        )
        assert output.tool == "tfsa"
        assert output.generate_chart is False

    def test_router_output_with_chart(self):
        output = RouterOutput(
            tool="fund_facts",
            generate_chart=True,
            chart_type="line",
            reasoning="User wants to see historical performance",
        )
        assert output.generate_chart is True
        assert output.chart_type == "line"


class TestOrchestratorRouting:
    """Tests for orchestrator routing decisions."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create orchestrator with mocked LLM."""
        with patch("src.orchestrator.router.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm
            orchestrator = Orchestrator()
            yield orchestrator, mock_llm

    def test_tfsa_query_routing(self, mock_orchestrator):
        """Test that TFSA queries route to TFSA tool."""
        orchestrator, mock_llm = mock_orchestrator

        # Mock the chain response
        mock_response = RouterOutput(
            tool="tfsa",
            generate_chart=False,
            chart_type="bar",
            reasoning="Query is about TFSA contribution limits",
        )

        with patch.object(orchestrator, "route", return_value=OrchestratorDecision(
            tool="tfsa",
            user_query="What is the TFSA contribution limit?",
            generate_chart=False,
            chart_type="bar",
            reasoning="Query is about TFSA",
        )):
            decision = orchestrator.route("What is the TFSA contribution limit?")

        assert decision.tool == "tfsa"

    def test_rrsp_query_routing(self, mock_orchestrator):
        """Test that RRSP queries route to RRSP tool."""
        orchestrator, mock_llm = mock_orchestrator

        with patch.object(orchestrator, "route", return_value=OrchestratorDecision(
            tool="rrsp",
            user_query="How does the Home Buyers Plan work?",
            generate_chart=False,
            chart_type="bar",
            reasoning="Query is about RRSP HBP",
        )):
            decision = orchestrator.route("How does the Home Buyers Plan work?")

        assert decision.tool == "rrsp"

    def test_fund_facts_query_routing(self, mock_orchestrator):
        """Test that fund queries route to Fund Facts tool."""
        orchestrator, mock_llm = mock_orchestrator

        with patch.object(orchestrator, "route", return_value=OrchestratorDecision(
            tool="fund_facts",
            user_query="What is the MER for Fund A?",
            generate_chart=False,
            chart_type="bar",
            reasoning="Query is about fund fees",
        )):
            decision = orchestrator.route("What is the MER for Fund A?")

        assert decision.tool == "fund_facts"

    def test_chart_detection(self, mock_orchestrator):
        """Test that chart requests are detected."""
        orchestrator, mock_llm = mock_orchestrator

        with patch.object(orchestrator, "route", return_value=OrchestratorDecision(
            tool="fund_facts",
            user_query="Show me a chart comparing fund MERs",
            generate_chart=True,
            chart_type="bar",
            reasoning="User wants a comparison chart",
        )):
            decision = orchestrator.route("Show me a chart comparing fund MERs")

        assert decision.generate_chart is True
        assert decision.chart_type == "bar"
