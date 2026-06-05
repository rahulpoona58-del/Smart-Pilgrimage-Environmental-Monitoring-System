# backend/app/api/v1/endpoints/prediction.py
# API router endpoints for prediction modeling, forecasts, and model triggers.

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ....db.session import get_async_db
from ....core.prediction import PredictionEngine
from ....schemas.types import EnvironmentalRiskForecast, PredictionResult, ModelTrainingMetricsOut

router = APIRouter()

@router.post("/train", response_model=dict, status_code=status.HTTP_200_OK)
async def train_forecasting_models(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Triggers model training pipelines, calculating and saving R2, MAE, and RMSE metrics.
    """
    try:
        metrics = await PredictionEngine.train_prediction_models(db)
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training pipeline execution failed: {e}"
        )

@router.get("/risk-forecast/{location_id}", response_model=EnvironmentalRiskForecast)
async def get_environmental_risk_forecast(
    location_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves the 3-day consolidated environmental risk forecast across all four indicators.
    """
    try:
        forecast = await PredictionEngine.get_environmental_risk_forecast(db, location_id)
        return forecast
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate risk forecast: {e}"
        )

@router.get("/pollution/{location_id}", response_model=PredictionResult)
async def get_pollution_forecast(
    location_id: int,
    hours_ahead: int = Query(3, ge=1, le=72),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves a pollution spike prediction for a location.
    """
    try:
        result = await PredictionEngine.predict_pollution_spike(db, location_id, hours_ahead)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pollution forecasting failed: {e}"
        )

@router.get("/traffic/{location_id}", response_model=PredictionResult)
async def get_traffic_forecast(
    location_id: int,
    hours_ahead: int = Query(3, ge=1, le=72),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves a traffic congestion forecast for a location.
    """
    try:
        result = await PredictionEngine.predict_traffic_congestion(db, location_id, hours_ahead)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Traffic forecasting failed: {e}"
        )

@router.get("/crowd/{location_id}", response_model=PredictionResult)
async def get_crowd_forecast(
    location_id: int,
    hours_ahead: int = Query(3, ge=1, le=72),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves a crowd density forecast for a location.
    """
    try:
        result = await PredictionEngine.predict_crowd_density(db, location_id, hours_ahead)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crowd forecasting failed: {e}"
        )

@router.get("/litter/{location_id}", response_model=PredictionResult)
async def get_litter_forecast(
    location_id: int,
    hours_ahead: int = Query(3, ge=1, le=72),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves a littering hotspot frequency forecast for a location.
    """
    try:
        result = await PredictionEngine.predict_littering_hotspots(db, location_id, hours_ahead)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Litter hotspot forecasting failed: {e}"
        )
