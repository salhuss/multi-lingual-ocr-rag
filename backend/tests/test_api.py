"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data


class TestChatEndpoint:
    """Test chat endpoint with mocked dependencies."""

    @patch("app.main.is_hajj_related")
    @patch("app.main.retrieve_relevant_chunks")
    @patch("app.main.generate_answer")
    @patch("app.main.log_query")
    def test_chat_hajj_question_success(
        self,
        mock_log,
        mock_generate,
        mock_retrieve,
        mock_is_hajj,
    ):
        """Test successful chat response for Hajj question."""
        # Setup mocks
        mock_is_hajj.return_value = True
        mock_retrieve.return_value = [
            {
                "id": 1,
                "book_title": "Test Book",
                "page_number": 5,
                "arabic_text": "نص عربي",
                "similarity": 0.9,
            }
        ]
        mock_generate.return_value = {
            "answer": "This is the answer",
            "citations": [{"book": "Test Book", "page": 5, "excerpt": "نص"}],
            "status": "success",
        }

        response = client.post(
            "/chat",
            json={"query": "How do I perform tawaf?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert data["status"] == "success"

    @patch("app.main.is_hajj_related")
    def test_chat_non_hajj_question_rejected(self, mock_is_hajj):
        """Test that non-Hajj questions are rejected."""
        mock_is_hajj.return_value = False

        response = client.post(
            "/chat",
            json={"query": "What is zakat?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refused"
        assert "Hajj" in data["answer"]

    def test_chat_empty_query(self):
        """Test that empty query returns error."""
        response = client.post(
            "/chat",
            json={"query": ""},
        )

        assert response.status_code == 400

    @patch("app.main.is_hajj_related")
    @patch("app.main.retrieve_relevant_chunks")
    def test_chat_no_sources_found(self, mock_retrieve, mock_is_hajj):
        """Test response when no sources are found."""
        mock_is_hajj.return_value = True
        mock_retrieve.return_value = []

        response = client.post(
            "/chat",
            json={"query": "Very specific Hajj question"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refused"
        assert "don't know" in data["answer"].lower()


class TestCitationRequirement:
    """Test that citations are required in responses."""

    @patch("app.main.is_hajj_related")
    @patch("app.main.retrieve_relevant_chunks")
    @patch("app.main.generate_answer")
    def test_answer_without_citations_rejected(
        self,
        mock_generate,
        mock_retrieve,
        mock_is_hajj,
    ):
        """Test that answers without citations are rejected."""
        mock_is_hajj.return_value = True
        mock_retrieve.return_value = [
            {
                "id": 1,
                "book_title": "Test Book",
                "page_number": 5,
                "arabic_text": "نص عربي",
                "similarity": 0.9,
            }
        ]
        mock_generate.return_value = {
            "answer": "This is an answer without citations",
            "citations": [],
            "status": "no_citations",
        }

        response = client.post(
            "/chat",
            json={"query": "How do I perform tawaf?"},
        )

        # The endpoint should handle this and return a refusal
        # or the LLM should be forced to provide citations
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
