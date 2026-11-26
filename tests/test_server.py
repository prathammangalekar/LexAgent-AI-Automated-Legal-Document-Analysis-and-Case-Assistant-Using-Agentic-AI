"""Tests for the LexAgent AI Web API and frontend server."""

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_serve_frontend(client):
    """Verifies that the server delivers the index.html frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "LexAgent AI" in response.text
    assert "Document Analyzer" in response.text


def test_health_check(client):
    """Verifies that the API health check returns online status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["agents_active"] == 8


def test_api_legal_research(client):
    """Verifies that the /api/research endpoint invokes the research agent."""
    response = client.post("/api/research", json={"query": "non-compete clause under Indian Contract Act Section 27"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["precedents"]) > 0
    assert any("Percept" in p["title"] for p in data["precedents"])


def test_api_legal_draft(client):
    """Verifies that the /api/draft endpoint invokes the drafting agent."""
    response = client.post("/api/draft", json={"instructions": "Draft notice for refund of withheld liquidated damages."})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "FORMAL LEGAL NOTICE" in data["draft_title"]
    assert "WITHOUT PREJUDICE" in data["formal_body"]
