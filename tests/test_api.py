"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app
from src.tools.schemas import ChatResponse, Source


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_empty_message_rejected(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 400

    def test_whitespace_message_rejected(self, client):
        response = client.post("/chat", json={"message": "   "})
        assert response.status_code == 400

    def test_chat_with_mock_orchestrator(self, client):
        """Test chat endpoint with mocked orchestrator."""
        mock_response = ChatResponse(
            reply="The TFSA contribution limit for 2024 is $7,000.",
            sources=[
                Source(
                    pdf_name="TFSA Guide",
                    pdf_url="https://example.com/tfsa-guide.pdf",
                    page=5,
                )
            ],
        )

        with patch("src.main.get_orchestrator") as mock_get:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process.return_value = mock_response
            mock_get.return_value = mock_orchestrator

            response = client.post(
                "/chat",
                json={"message": "What is the TFSA contribution limit?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "sources" in data

    def test_chat_response_schema(self, client):
        """Test that chat response matches expected schema."""
        mock_response = ChatResponse(
            reply="Test response",
            chart_type="bar",
            image_base64="data:image/png;base64,abc123",
            sources=[
                Source(pdf_name="Test PDF", pdf_url="https://example.com/test.pdf")
            ],
        )

        with patch("src.main.get_orchestrator") as mock_get:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process.return_value = mock_response
            mock_get.return_value = mock_orchestrator

            response = client.post("/chat", json={"message": "Test"})

        data = response.json()
        assert "reply" in data
        assert "chart_type" in data
        assert "image_base64" in data
        assert "sources" in data
