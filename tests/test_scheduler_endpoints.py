"""Integration tests for scheduler API endpoints."""

import pytest
from fastapi import status


@pytest.mark.integration
class TestSchedulerEndpoints:
    """Test scheduler API endpoints."""
    
    def test_start_scheduler(self, client, test_token):
        """Test starting the scheduler."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "location": "Minneapolis, MN",
                "queries": ["Python developer", "FastAPI developer"],
                "min_match_score": 0.7,
                "limit_per_query": 10
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "running"
        assert data["message"] == "Scheduler started"
        assert data["location"] == "Minneapolis, MN"
        assert data["min_match_score"] == 0.7
        assert "queries" in data
    
    def test_start_scheduler_minimal_request(self, client, test_token):
        """Test starting scheduler with minimal request body."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "running"
        assert data["message"] == "Scheduler started"
        assert data["location"] == "Minneapolis, MN"  # Default value
    
    def test_start_scheduler_idempotency(self, client, test_token):
        """Test that starting scheduler when already running is idempotent."""
        # Start scheduler first time
        response1 = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={"location": "Seattle, WA"}
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["status"] == "running"
        assert response1.json()["message"] == "Scheduler started"
        
        # Try to start again
        response2 = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={"location": "Seattle, WA"}
        )
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()
        assert data["status"] == "running"
        assert data["message"] == "Scheduler is already running"
    
    def test_stop_scheduler(self, client, test_token):
        """Test stopping the scheduler."""
        # Start scheduler first
        client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={"location": "Minneapolis, MN"}
        )
        
        # Stop scheduler
        response = client.post(
            "/api/v1/scheduler/stop",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "stopped"
        assert data["message"] == "Scheduler stopped"
    
    def test_stop_scheduler_idempotency(self, client, test_token):
        """Test that stopping scheduler when not running is idempotent."""
        # Stop scheduler without starting it
        response = client.post(
            "/api/v1/scheduler/stop",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "stopped"
        assert data["message"] == "Scheduler is not running"
    
    def test_stop_scheduler_when_running(self, client, test_token):
        """Test stopping scheduler when it's running."""
        # Start scheduler
        start_response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={"location": "Minneapolis, MN"}
        )
        assert start_response.status_code == status.HTTP_200_OK
        
        # Stop scheduler
        stop_response = client.post(
            "/api/v1/scheduler/stop",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert stop_response.status_code == status.HTTP_200_OK
        data = stop_response.json()
        assert data["status"] == "stopped"
        assert data["message"] == "Scheduler stopped"
        
        # Verify it's actually stopped by trying to stop again
        stop_again_response = client.post(
            "/api/v1/scheduler/stop",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert stop_again_response.status_code == status.HTTP_200_OK
        assert stop_again_response.json()["message"] == "Scheduler is not running"
    
    def test_start_scheduler_validation(self, client, test_token):
        """Test request validation for start endpoint."""
        # Invalid min_match_score (should be float)
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "min_match_score": "invalid"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_start_scheduler_validation_min_match_score_too_high(self, client, test_token):
        """Test validation rejects min_match_score > 1.0."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "min_match_score": 1.5
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "min_match_score must be between 0.0 and 1.0" in str(data)
    
    def test_start_scheduler_validation_min_match_score_too_low(self, client, test_token):
        """Test validation rejects min_match_score < 0.0."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "min_match_score": -0.1
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_start_scheduler_validation_limit_per_query_too_low(self, client, test_token):
        """Test validation rejects limit_per_query < 1."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "limit_per_query": 0
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "limit_per_query must be between 1 and 100" in str(data)
    
    def test_start_scheduler_validation_limit_per_query_too_high(self, client, test_token):
        """Test validation rejects limit_per_query > 100."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "limit_per_query": 101
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_start_scheduler_validation_empty_location(self, client, test_token):
        """Test validation rejects empty location."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "location": ""
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "location cannot be empty" in str(data)
    
    def test_start_scheduler_validation_whitespace_location(self, client, test_token):
        """Test validation rejects whitespace-only location."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "location": "   "
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_start_scheduler_validation_empty_queries_list(self, client, test_token):
        """Test validation rejects empty queries list."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "queries": []
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "queries list cannot be empty if provided" in str(data)
    
    def test_start_scheduler_validation_empty_sources_list(self, client, test_token):
        """Test validation rejects empty sources list."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "sources": []
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "sources list cannot be empty if provided" in str(data)
    
    def test_start_scheduler_with_all_fields(self, client, test_token):
        """Test starting scheduler with all optional fields."""
        response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "queries": ["Python", "FastAPI", "Docker"],
                "location": "San Francisco, CA",
                "sources": ["indeed", "linkedin"],
                "min_match_score": 0.8,
                "limit_per_query": 20
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "running"
        assert data["location"] == "San Francisco, CA"
        assert data["min_match_score"] == 0.8
        assert data["limit_per_query"] == 20
        assert data["queries"] == ["Python", "FastAPI", "Docker"]
        assert data["sources"] == ["indeed", "linkedin"]
    
    def test_scheduler_endpoints_no_auth(self, client):
        """Test that scheduler endpoints require authentication."""
        # Test start endpoint
        response = client.post(
            "/api/v1/scheduler/start",
            json={"location": "Minneapolis, MN"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test stop endpoint
        response = client.post("/api/v1/scheduler/stop")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test status endpoint
        response = client.get("/api/v1/scheduler/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_scheduler_status_stopped(self, client, test_token):
        """Test getting scheduler status when stopped."""
        response = client.get(
            "/api/v1/scheduler/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "stopped"
        assert data["message"] == "Scheduler is stopped"
        assert data["location"] is None
    
    def test_get_scheduler_status_running(self, client, test_token):
        """Test getting scheduler status when running."""
        # Start scheduler first
        start_response = client.post(
            "/api/v1/scheduler/start",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "location": "San Francisco, CA",
                "queries": ["Python", "FastAPI"],
                "min_match_score": 0.8,
                "limit_per_query": 15
            }
        )
        assert start_response.status_code == status.HTTP_200_OK
        
        # Get status
        status_response = client.get(
            "/api/v1/scheduler/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert status_response.status_code == status.HTTP_200_OK
        data = status_response.json()
        assert data["status"] == "running"
        assert data["message"] == "Scheduler is running"
        assert data["location"] == "San Francisco, CA"
        assert data["min_match_score"] == 0.8
        assert data["limit_per_query"] == 15
        assert data["queries"] == ["Python", "FastAPI"]
    
    def test_get_scheduler_status_no_auth(self, client):
        """Test that status endpoint requires authentication."""
        response = client.get("/api/v1/scheduler/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

