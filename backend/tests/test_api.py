"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "service" in data


def test_summarize_extractive(client, sample_text):
    """Test summarization endpoint"""
    response = client.post(
        "/api/v1/summarize",
        json={
            "text": sample_text,
            "mode": "extractive",
            "top_k": 3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "sentences_extracted" in data
    assert data["mode"] == "extractive"


def test_summarize_invalid_input(client):
    """Test with invalid input"""
    response = client.post(
        "/api/v1/summarize",
        json={
            "text": "",  # Empty text
            "mode": "extractive"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_summarize_invalid_mode(client, sample_text):
    """Test with invalid mode"""
    response = client.post(
        "/api/v1/summarize",
        json={
            "text": sample_text,
            "mode": "invalid_mode"
        }
    )
    
    assert response.status_code == 422
