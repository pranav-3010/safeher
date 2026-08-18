from typing import Optional, List
from pydantic import BaseModel, Field


class LocationAnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    radius_meters: float = Field(default=2000.0, gt=0.0, le=50000.0, description="Search radius in meters")


class SafetyQuestionRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    radius_meters: float = Field(default=2000.0, gt=0.0, le=50000.0, description="Search radius in meters")
    question: str = Field(..., min_length=3, max_length=500, description="Safety question from user")


class RouteContextAnalysisRequest(BaseModel):
    origin_latitude: float = Field(..., ge=-90.0, le=90.0)
    origin_longitude: float = Field(..., ge=-180.0, le=180.0)
    destination_latitude: float = Field(..., ge=-90.0, le=90.0)
    destination_longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_meters: float = Field(default=2000.0, gt=0.0, le=50000.0)


class SourceItem(BaseModel):
    claim: str
    source: str
    period: str


class StructuredAIResponse(BaseModel):
    summary: str
    key_factors: List[str]
    data_limitations: List[str]
    sources: List[SourceItem]
    verified_context_summary: Optional[dict] = None
