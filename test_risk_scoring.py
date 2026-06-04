# test_risk_scoring.py
# Verification harness for Milestone: Environmental Risk Scoring.

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

def test_environmental_risk_summary_endpoint():
    client = TestClient(app)
    
    # Query the environmental risk summary endpoint
    response = client.get("/api/v1/compliance/environmental-risk-summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Assert existence of all five required environmental scores
    assert "vehicle_eco_score" in data
    assert "location_eco_score" in data
    assert "route_eco_score" in data
    assert "repeat_offender_score" in data
    assert "pollution_impact_score" in data
    
    # Verify score value ranges
    assert 0 <= data["vehicle_eco_score"] <= 100
    assert 0 <= data["location_eco_score"] <= 100
    assert 0 <= data["route_eco_score"] <= 100
    assert 0 <= data["repeat_offender_score"] <= 100
    assert 0 <= data["pollution_impact_score"] <= 100
    
    print("\n[Risk Scoring Test Success] Returned payload values:")
    for score_name, value in data.items():
        print(f"  - {score_name}: {value}%")

if __name__ == "__main__":
    test_environmental_risk_summary_endpoint()
