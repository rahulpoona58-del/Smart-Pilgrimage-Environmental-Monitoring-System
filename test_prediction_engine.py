# test_prediction_engine.py
# Verification harness for SPEMS Prediction Engine.

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

def test_prediction_engine_integration():
    with TestClient(app) as client:
        # 1. Trigger Model Training Pipeline
        train_res = client.post("/api/v1/prediction/train")
        assert train_res.status_code == 200
        train_data = train_res.json()
        assert train_data["status"] == "success"
        assert "metrics" in train_data
        assert "pollution" in train_data["metrics"]
        assert "traffic" in train_data["metrics"]

        # 2. Query Unified Environmental Risk Forecast for Location 1
        forecast_res = client.get("/api/v1/prediction/risk-forecast/1")
        assert forecast_res.status_code == 200
        forecast_data = forecast_res.json()
        
        # Verify schema elements
        assert forecast_data["location_id"] == 1
        assert "overall_risk_rating" in forecast_data
        assert forecast_data["overall_risk_rating"] in ["LOW", "MEDIUM", "HIGH"]
        
        # Check individual indicator sub-keys
        for key in ["pollution_spike_prediction", "traffic_congestion_prediction", "crowd_density_prediction", "littering_hotspot_prediction"]:
            assert key in forecast_data
            pred = forecast_data[key]
            assert "target_type" in pred
            assert "predicted_value" in pred
            assert "confidence_score" in pred
            assert "target_time" in pred
            assert "alert_generated" in pred

        # 3. Query specific pollution forecast with lag hours
        pollution_res = client.get("/api/v1/prediction/pollution/1?hours_ahead=6")
        assert pollution_res.status_code == 200
        pollution_data = pollution_res.json()
        assert pollution_data["target_type"] == "pollution"
        assert "predicted_value" in pollution_data
        assert "confidence_score" in pollution_data

        print("\n[Prediction Engine Test Success] Validation details:")
        print(f"  - Overall Risk Rating: {forecast_data['overall_risk_rating']}")
        print(f"  - Forecasted AQI (24h): {forecast_data['pollution_spike_prediction']['predicted_value']}")
        print(f"  - Forecasted Traffic Transits (24h): {forecast_data['traffic_congestion_prediction']['predicted_value']} transits/hr")
        print(f"  - Forecasted Crowd Index (24h): {forecast_data['crowd_density_prediction']['predicted_value']}%")
        print(f"  - Forecasted Litter Incidents (24h): {forecast_data['littering_hotspot_prediction']['predicted_value']} incidents")

if __name__ == "__main__":
    test_prediction_engine_integration()
