from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.ai import (
    LocationAnalysisRequest,
    SafetyQuestionRequest,
    RouteContextAnalysisRequest,
    StructuredAIResponse
)
from app.services.safety_context_builder import SafetyContextBuilder
from app.services.llm_service import LLMService

router = APIRouter()


@router.post("/analyze-location", response_model=StructuredAIResponse, summary="Analyze Safety Context Around Location")
def analyze_location_safety(
    req: LocationAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Summarizes verified geographic, emergency facility, and crime information around user coordinates.
    """
    context = SafetyContextBuilder.build_location_context(
        db, latitude=req.latitude, longitude=req.longitude, radius_meters=req.radius_meters
    )
    ai_res = LLMService.analyze_safety_context(context, user_query="Analyze safety information around my current location.")
    ai_res["verified_context_summary"] = {
        "nearby_verified_incidents_count": context["nearby_verified_incidents_count"],
        "nearest_police_station_distance_meters": context["nearest_police_station_distance_meters"],
        "nearest_hospital_distance_meters": context["nearest_hospital_distance_meters"],
        "spatial_crime_density_per_sq_km": context["spatial_crime_density_per_sq_km"]
    }
    return ai_res


@router.post("/explain-crime-data", response_model=StructuredAIResponse, summary="Explain Verified Crime Data & Statistics")
def explain_crime_data(
    req: LocationAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Explains verified crime incidents and historical NCRB stats for target location.
    """
    context = SafetyContextBuilder.build_location_context(
        db, latitude=req.latitude, longitude=req.longitude, radius_meters=req.radius_meters
    )
    ai_res = LLMService.analyze_safety_context(context, user_query="Explain the verified crime incidents and statistics around this area.")
    ai_res["verified_context_summary"] = {
        "nearby_verified_incidents_count": context["nearby_verified_incidents_count"],
        "spatial_crime_density_per_sq_km": context["spatial_crime_density_per_sq_km"],
        "historical_ncrb_records": len(context.get("historical_ncrb_statistics", []))
    }
    return ai_res


@router.post("/safety-question", response_model=StructuredAIResponse, summary="Answer User Safety Questions Based on Verified Data")
def answer_safety_question(
    req: SafetyQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Answers questions like 'Where is the nearest police station?' or 'What emergency services exist?' using backend data only.
    """
    context = SafetyContextBuilder.build_location_context(
        db, latitude=req.latitude, longitude=req.longitude, radius_meters=req.radius_meters
    )
    ai_res = LLMService.analyze_safety_context(context, user_query=req.question)
    ai_res["verified_context_summary"] = {
        "user_question": req.question,
        "nearest_police_station_distance_meters": context["nearest_police_station_distance_meters"],
        "nearest_hospital_distance_meters": context["nearest_hospital_distance_meters"]
    }
    return ai_res


@router.post("/analyze-route-context", response_model=StructuredAIResponse, summary="Analyze Origin and Destination Route Context")
def analyze_route_context(
    req: RouteContextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyzes safety context for source and destination locations without predicting safest route (Phase 7 feature).
    """
    context = SafetyContextBuilder.build_location_context(
        db,
        latitude=req.origin_latitude,
        longitude=req.origin_longitude,
        radius_meters=req.radius_meters,
        destination_lat=req.destination_latitude,
        destination_lng=req.destination_longitude
    )
    ai_res = LLMService.analyze_safety_context(
        context, user_query="Analyze safety context for origin and destination coordinates."
    )
    ai_res["verified_context_summary"] = {
        "origin": {"latitude": req.origin_latitude, "longitude": req.origin_longitude},
        "destination": {"latitude": req.destination_latitude, "longitude": req.destination_longitude},
        "origin_incidents": context["nearby_verified_incidents_count"],
        "destination_incidents": context.get("destination_context", {}).get("destination_nearby_incidents_count", 0)
    }
    return ai_res
