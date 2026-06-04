# test_emissions_calculator.py
# Verification harness for the Emissions Calculator Module.

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.models import Vehicle, VehicleLog
import datetime

def test_emissions_endpoints():
    with TestClient(app) as client:
        # 1. Run emissions calculation on active database
        response = client.get("/api/v1/compliance/emissions/calculate?save_to_history=true")
        if response.status_code != 200:
            print(f"Error Response: Status={response.status_code}, Body={response.text}")
        assert response.status_code == 200
        data = response.json()

        # Assert basic metrics exist
        assert "total_vehicles" in data
        assert "total_transits" in data
        assert "corridor_distance_km" in data
        assert "total_co2_kg" in data
        assert "total_pm_g" in data
        assert "trees_offset_required" in data
        assert "offset_cost_inr" in data
        assert "idle_savings_kg" in data
        assert "segments" in data

        # Assert numeric bounds
        assert data["total_vehicles"] >= 0
        assert data["total_transits"] >= 0
        assert data["corridor_distance_km"] == 6.0
        assert data["total_co2_kg"] >= 0
        assert data["total_pm_g"] >= 0
        assert data["trees_offset_required"] >= 0
        assert data["offset_cost_inr"] >= 0.0
        assert data["idle_savings_kg"] >= 0.0

        # 2. Check history log endpoint
        history_res = client.get("/api/v1/compliance/emissions/history?limit=10")
        assert history_res.status_code == 200
        history_data = history_res.json()

    # Verify history array structure
    assert isinstance(history_data, list)
    if len(history_data) > 0:
        first_record = history_data[0]
        assert "id" in first_record
        assert "calculated_at" in first_record
        assert "total_vehicles" in first_record
        assert "total_transits" in first_record
        assert "total_co2_kg" in first_record
        assert "total_pm_g" in first_record
        assert "trees_offset" in first_record
        assert "offset_cost_inr" in first_record
        assert "idle_savings_kg" in first_record

    print("\n[Emissions Calculator Test Success] Output Summary:")
    print(f"  - Total Vehicles: {data['total_vehicles']}")
    print(f"  - Total Transits: {data['total_transits']}")
    print(f"  - Calculated CO2: {data['total_co2_kg']} kg")
    print(f"  - Calculated PM: {data['total_pm_g']} g")
    print(f"  - Offset Required: {data['trees_offset_required']} trees (Cost: INR {data['offset_cost_inr']})")
    print(f"  - Idle Savings: {data['idle_savings_kg']} kg CO2e")

if __name__ == "__main__":
    test_emissions_endpoints()
