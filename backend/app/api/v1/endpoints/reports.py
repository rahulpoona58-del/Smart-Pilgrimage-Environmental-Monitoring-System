# backend/app/api/v1/endpoints/reports.py
# Milestone 14: Alerting and Reporting Endpoints.

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from ....db.session import get_async_db
from ....db.models import Violation
from ....core.notification import AlertingSystem, ReportingEngine

router = APIRouter()

@router.post("/violations/{violation_id}/alert")
async def trigger_violation_alerts(
    violation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Triggers emergency real-time SMS (Twilio) and Email (AWS SES) alerts for a registered infraction."""
    query = select(Violation).where(Violation.id == violation_id)
    result = await db.execute(query)
    violation = result.scalars().first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation record not found."
        )

    # Compile details
    details = f"Surveillance Node flagged environmental violation: Category={violation.violation_type}, Severity={violation.severity_level}, Fine=INR {violation.fine_amount_inr:.2f}"
    
    alert_payload = AlertingSystem.trigger_alert(
        violation_id=violation.id,
        v_type=violation.violation_type,
        severity=violation.severity_level,
        details=details
    )
    return alert_payload

@router.post("/violations/{violation_id}/escalate")
async def trigger_violation_escalation(
    violation_id: int,
    duration_seconds: int = Query(6, description="Pending duration in seconds"),
    db: AsyncSession = Depends(get_async_db)
):
    """Triggers administrative escalation workflow for pending critical priority infractions."""
    query = select(Violation).where(Violation.id == violation_id)
    result = await db.execute(query)
    violation = result.scalars().first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation record not found."
        )

    escalation_payload = AlertingSystem.handle_escalation_workflow(
        violation_id=violation.id,
        severity=violation.severity_level,
        duration_seconds=duration_seconds
    )
    return escalation_payload

@router.get("/reports/daily/{location_id}")
async def get_daily_compliance_summary(
    location_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Generates rolling daily 24h compliance summary statistics and formatted summaries."""
    summary = await ReportingEngine.generate_daily_summary(db, location_id)
    return summary

@router.get("/violations/{violation_id}/pdf")
async def export_legal_evidence_pdf(
    violation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Exports an officially signed e-challan and legal evidence visual sheet (ASCII Layout)."""
    query = select(Violation).where(Violation.id == violation_id)
    result = await db.execute(query)
    violation = result.scalars().first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation record not found."
        )

    # Map spatial coordinate to approximate decimals
    # In SQLite, coordinates are mapped via standard string geometry representation
    coords_str = str(violation.violation_coordinates)
    lat = 30.6504
    lng = 79.0054
    if "POINT" in coords_str:
        try:
            # Parse from "POINT(79.0054 30.6504)"
            cleaned = coords_str.split("POINT")[1].strip("()").split()
            lng = float(cleaned[0])
            lat = float(cleaned[1])
        except Exception:
            pass

    violation_data = {
        "id": violation.id,
        "camera_id": violation.camera_id,
        "plate_number": violation.plate_number,
        "violation_type": violation.violation_type,
        "severity_level": violation.severity_level,
        "latitude": lat,
        "longitude": lng,
        "fine_amount_inr": float(violation.fine_amount_inr),
        "evidence_image_url": violation.evidence_image_url,
        "evidence_hash": violation.evidence_hash
    }

    pdf_text = ReportingEngine.generate_legal_pdf_report(violation_data)
    return {
        "violation_id": violation_id,
        "filename": f"challan_UK_SPEMS_{violation_id}.pdf",
        "pdf_ascii_layout": pdf_text
    }
