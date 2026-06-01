import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ....db.session import get_async_db
from ....db.models import Violation, Vehicle
from ....schemas.types import ViolationOut

router = APIRouter()

# Local directory to store static evidence images
STATIC_UPLOAD_DIR = "static/evidence"
os.makedirs(STATIC_UPLOAD_DIR, exist_ok=True)

import hashlib
from typing import Optional

@router.post("", response_model=ViolationOut, status_code=status.HTTP_201_CREATED)
async def report_environmental_violation(
    location_id: int = Form(...),
    camera_id: str = Form(...),
    plate_number: str = Form(""),
    violation_type: str = Form(...),
    severity_level: str = Form("Medium"),
    violation_timestamp: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    evidence_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Receives multi-part environmental violations from Edge nodes, computes SHA-256 evidence seals,
    prevents duplicate evidence logs, saves files locally, and writes spatial SQL records.
    """
    # A. Generate cryptographic hash from raw image bytes
    contents = await evidence_image.read()
    evidence_hash = hashlib.sha256(contents).hexdigest()
    await evidence_image.seek(0) # Reset stream pointer for local save operations
    
    # B. Deduplication Check: Ensure this exact visual evidence hash does not already exist
    query_dup = select(Violation).where(Violation.evidence_hash == evidence_hash)
    res_dup = await db.execute(query_dup)
    exists = res_dup.scalars().first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate evidence detected. This environmental infraction has already been logged."
        )

    # 1. Save evidence image file locally
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{evidence_image.filename}"
    file_path = os.path.join(STATIC_UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(evidence_image.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write evidence keyframe storage: {e}"
        )

    # Convert timestamp string
    try:
        v_time = datetime.fromisoformat(violation_timestamp.replace("Z", "+00:00"))
    except ValueError:
        v_time = datetime.now(timezone.utc)

    # Define standard spatial insertion point (EPSG 4326)
    spatial_point = f"SRID=4326;POINT({longitude} {latitude})"

    # Calculate fine amount based on infraction severity
    fine_inr = 500.00
    if violation_type == "Restricted_Zone_Entry":
        fine_inr = 2000.00
    elif violation_type == "Littering":
        fine_inr = 1000.00
    elif violation_type == "River_Pollution":
        fine_inr = 5000.00

    if severity_level == "High":
        fine_inr *= 1.5

    # 2. Record infraction record in SQLAlchemy PostGIS model
    new_violation = Violation(
        location_id=location_id,
        camera_id=camera_id,
        plate_number=plate_number if plate_number != "" else None,
        violation_type=violation_type,
        severity_level=severity_level,
        evidence_image_url=f"/static/evidence/{filename}", # Relative path readable by web client
        violation_coordinates=spatial_point,
        violation_timestamp=v_time,
        status="PENDING",
        fine_amount_inr=fine_inr,
        evidence_hash=evidence_hash # Save cryptographic evidence hash
    )

    db.add(new_violation)

    # 3. Dynamic Score Penalty Engine
    # If violation is linked to a registered vehicle, deduct scores and recalculate risk
    if plate_number and plate_number != "":
        query = select(Vehicle).where(Vehicle.plate_number == plate_number)
        result = await db.execute(query)
        vehicle = result.scalars().first()

        if vehicle:
            # Deduct points based on severity
            deduction = 10
            if violation_type == "Littering":
                deduction = 15
            elif violation_type == "Restricted_Zone_Entry":
                deduction = 25
            elif violation_type == "River_Pollution":
                deduction = 35

            vehicle.compliance_score = max(0, vehicle.compliance_score - deduction)

            # Update Environmental Risk Categorization
            if vehicle.compliance_score > 75:
                vehicle.risk_rating = "Low"
            elif vehicle.compliance_score > 45:
                vehicle.risk_rating = "Medium"
            else:
                vehicle.risk_rating = "High"
            
            db.add(vehicle)

    await db.commit()
    await db.refresh(new_violation)

    # Return output mapping including the evidence hash
    return ViolationOut(
        id=new_violation.id,
        location_id=new_violation.location_id,
        camera_id=new_violation.camera_id,
        plate_number=new_violation.plate_number,
        violation_type=new_violation.violation_type,
        severity_level=new_violation.severity_level,
        evidence_image_url=new_violation.evidence_image_url,
        evidence_video_url=new_violation.evidence_video_url,
        evidence_hash=new_violation.evidence_hash,
        violation_timestamp=new_violation.violation_timestamp,
        status=new_violation.status,
        challan_reference=new_violation.challan_reference,
        fine_amount_inr=float(new_violation.fine_amount_inr),
        created_at=new_violation.created_at
    )

@router.get("", response_model=list[ViolationOut])
async def list_violations(
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Fetches violations list, sorted chronologically."""
    query = select(Violation)
    if status:
        query = query.where(Violation.status == status)
    if location_id:
        query = query.where(Violation.location_id == location_id)
        
    query = query.order_by(Violation.violation_timestamp.desc())
    result = await db.execute(query)
    violations = result.scalars().all()
    
    return [
        ViolationOut(
            id=v.id,
            location_id=v.location_id,
            camera_id=v.camera_id,
            plate_number=v.plate_number,
            violation_type=v.violation_type,
            severity_level=v.severity_level,
            evidence_image_url=v.evidence_image_url,
            evidence_video_url=v.evidence_video_url,
            evidence_hash=v.evidence_hash,
            violation_timestamp=v.violation_timestamp,
            status=v.status,
            challan_reference=v.challan_reference,
            fine_amount_inr=float(v.fine_amount_inr),
            created_at=v.created_at
        )
        for v in violations
    ]

@router.get("/{violation_id}/verify")
async def verify_evidence_integrity(violation_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Cryptographic verification endpoint.
    Recalculates the image hash of the file stored on local volumes, comparing it
    directly with the SHA-256 evidence seal written at ingestion, verifying admissibility.
    """
    query = select(Violation).where(Violation.id == violation_id)
    result = await db.execute(query)
    violation = result.scalars().first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation record not found."
        )

    # Convert relative web URL path back to local system filepath
    # e.g., '/static/evidence/filename.jpg' -> 'static/evidence/filename.jpg'
    relative_path = violation.evidence_image_url.lstrip('/')
    
    if not os.path.exists(relative_path):
        return {
            "violation_id": violation_id,
            "status": "FILE_NOT_FOUND",
            "message": f"Evidence file missing on local storage: {relative_path}",
            "stored_hash": violation.evidence_hash,
            "calculated_hash": None
        }

    try:
        # Calculate SHA-256 hash of the stored file
        with open(relative_path, "rb") as f:
            contents = f.read()
            calculated_hash = hashlib.sha256(contents).hexdigest()
            
        is_valid = calculated_hash == violation.evidence_hash
        
        return {
            "violation_id": violation_id,
            "status": "VALID" if is_valid else "TAMPERED",
            "message": "Evidence integrity successfully verified." if is_valid else "Warning: Cryptographic hash mismatch. Evidence has been modified.",
            "stored_hash": violation.evidence_hash,
            "calculated_hash": calculated_hash
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity check execution error: {e}"
        )
