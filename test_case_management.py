# test_case_management.py
# Verification Test Harness for the Violation Case Management System (Approve/Reject, Review, Audit Logs, History, and PDF).

from fastapi.testclient import TestClient
from backend.app.main import app
import pytest
import io
import os
import hashlib
from datetime import datetime, timezone

client = TestClient(app)

def test_case_management_flow():
    # A. Setup: Create a unique dummy image crop to avoid duplicate hash validation errors
    dummy_file = io.BytesIO(b"dummy image data " + os.urandom(8))
    contents = dummy_file.read()
    dummy_file.seek(0)
    
    payload = {
        "location_id": "1",
        "camera_id": "CAM-GK-TEST-99",
        "plate_number": "UK07TA9999",
        "violation_type": "Littering",
        "severity_level": "Medium",
        "violation_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "latitude": "30.6504",
        "longitude": "79.0054"
    }
    
    files = {
        "evidence_image": ("test_case_management_evidence.jpg", dummy_file, "image/jpeg")
    }
    
    # 1. Test Case Creation (Create Violation)
    print("\n[Test Case] Submitting new violation case...")
    response = client.post("/api/v1/violations", data=payload, files=files)
    assert response.status_code == 201
    v_data = response.json()
    v_id = v_data["id"]
    assert v_id is not None
    assert v_data["status"] == "PENDING"
    assert float(v_data["fine_amount_inr"]) == 1000.00 # Base Littering fine is 1000.00
    
    # 2. Test Officer Review Queue (Fetch pending cases)
    print("[Test Case] Fetching pending review queue...")
    queue_response = client.get("/api/v1/violations?status=PENDING")
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue) > 0
    assert any(item["id"] == v_id for item in queue)
    
    # 3. Test Evidence Review (Fetch detailed case by ID)
    print(f"[Test Case] Retrieving detailed violation details for ID #{v_id}...")
    detail_response = client.get(f"/api/v1/violations/{v_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == v_id
    assert detail["plate_number"] == "UK07TA9999"
    assert detail["violation_type"] == "Littering"
    
    # 4. Test Evidence Integrity Verification
    print(f"[Test Case] Verifying SHA-256 evidence integrity for ID #{v_id}...")
    verify_response = client.get(f"/api/v1/violations/{v_id}/verify")
    assert verify_response.status_code == 200
    verification = verify_response.json()
    assert verification["status"] == "VALID"
    assert verification["stored_hash"] == v_data["evidence_hash"]
    
    # 5. Test Approve Workflow (Approve Case & generate challan)
    print(f"[Test Case] Approving violation ID #{v_id}...")
    approve_payload = {
        "action": "APPROVE",
        "officer_badge": "UK-POL-7718",
        "notes": "Verified license plate crop."
    }
    action_response = client.post(f"/api/v1/violations/{v_id}/action", json=approve_payload)
    assert action_response.status_code == 200
    approved_case = action_response.json()
    assert approved_case["status"] == "APPROVED"
    assert approved_case["challan_reference"] is not None
    assert approved_case["challan_reference"].startswith("CH-")
    
    # 6. Test Case History retrieval
    print(f"[Test Case] Querying historical records for ID #{v_id}...")
    history_response = client.get(f"/api/v1/violations/{v_id}/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) > 0
    assert any(h["action_type"] == "CASE_APPROVED" for h in history)
    
    # 7. Test Global System Audit Logs
    print("[Test Case] Verifying system-wide audit logs...")
    audit_response = client.get("/api/v1/violations/audit-logs")
    assert audit_response.status_code == 200
    audit_logs = audit_response.json()
    assert len(audit_logs) > 0
    assert any(log["action_type"] == "CASE_APPROVED" for log in audit_logs)
    
    # 8. Test PDF Export Integration
    print(f"[Test Case] Exporting legal e-challan PDF ASCII layout for ID #{v_id}...")
    pdf_response = client.get(f"/api/v1/violations/{v_id}/pdf")
    assert pdf_response.status_code == 200
    pdf_data = pdf_response.json()
    assert pdf_data["violation_id"] == v_id
    assert "pdf_ascii_layout" in pdf_data
    assert "CHALLAN REF NO:" in pdf_data["pdf_ascii_layout"]
    
    # 9. Test Reject/Dismiss Workflow (Dismiss Case & restore vehicle score)
    print(f"[Test Case] Rejecting/Dismissing violation ID #{v_id}...")
    dismiss_payload = {
        "action": "DISMISS",
        "officer_badge": "UK-POL-7718",
        "notes": "Littering action disputed, visual check passes."
    }
    dismiss_response = client.post(f"/api/v1/violations/{v_id}/action", json=dismiss_payload)
    assert dismiss_response.status_code == 200
    dismissed_case = dismiss_response.json()
    assert dismissed_case["status"] == "DISMISSED"
    
    # Verify that history logs the dismissal
    history_after_dismiss = client.get(f"/api/v1/violations/{v_id}/history").json()
    assert any(h["action_type"] == "CASE_DISMISSED" for h in history_after_dismiss)
